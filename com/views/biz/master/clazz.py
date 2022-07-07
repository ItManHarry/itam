from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app, session, jsonify
from flask_login import login_required, current_user
from com.models import BizAssetClass, RelAssetClass
from com.plugins import db
from com.decorators import log_record
from com.forms.biz.master.clazz import ClazzSearchForm, ClazzForm
import uuid, time
from datetime import datetime
bp_clazz = Blueprint('clazz', __name__)
@bp_clazz.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查看资产分类信息')
def index():
    form = ClazzSearchForm()
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        try:
            code = session['clazz_view_search_code'] if session['clazz_view_search_code'] else ''  # 字典代码
            name = session['clazz_view_search_name'] if session['clazz_view_search_name'] else ''  # 字典名称
        except KeyError:
            code = ''
            name = ''
        form.code.data = code
        form.name.data = name
    if request.method == 'POST':
        page = 1
        code = form.code.data
        name = form.name.data
        session['clazz_view_search_code'] = code
        session['clazz_view_search_name'] = name
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']
    pagination = BizAssetClass.query.filter(BizAssetClass.code.like('%' + code.upper() + '%'), BizAssetClass.name.like('%' + name + '%')).order_by(BizAssetClass.code).paginate(page, per_page)
    clazzes = pagination.items
    return render_template('biz/master/clazz/index.html', form=form, clazzes=clazzes, pagination=pagination)
@bp_clazz.route('/add', methods=['GET', 'POST'])
@login_required
@log_record('新增资产分类信息')
def add():
    form = ClazzForm()
    form.parent.choices = get_parents()
    if request.method == 'GET':
        form.has_parent.data = True
    if form.validate_on_submit():
        if not form.has_parent.data or not form.parent.data:
            grade = 1
        else:
            parent = BizAssetClass.query.get(form.parent.data)
            grade = parent.grade + 1
        clazz = BizAssetClass(
            id=uuid.uuid4().hex,
            code=form.code.data.upper(),
            name=form.name.data,
            unit=form.unit.data,
            grade=grade,
            bg_id=current_user.company_id,
            create_id=current_user.id
        )
        db.session.add(clazz)
        db.session.commit()
        # 设置上级大类
        if grade != 1:
            clazz.set_parent_class(parent)
        flash('资产类别添加成功！')
        return redirect(url_for('.index'))
    return render_template('biz/master/clazz/add.html', form=form)
@bp_clazz.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
@log_record('修改资产类别信息')
def edit(id):
    form = ClazzForm()
    clazz = BizAssetClass.query.get_or_404(id)
    form.parent.choices = get_parents(clazz)
    if request.method == 'GET':
        form.id.data = id
        form.code.data = clazz.code
        form.name.data = clazz.name
        form.has_parent.data = True if clazz.get_parent_class else False
        form.parent.data = clazz.get_parent_class.id if clazz.get_parent_class else ''
        form.unit.data = clazz.unit
    if form.validate_on_submit():
        if not form.has_parent.data or not form.parent.data:
            grade = 1
        else:
            parent = BizAssetClass.query.get(form.parent.data)
            grade = parent.grade + 1
        clazz.code = form.code.data.upper()
        clazz.name = form.name.data
        clazz.grade = grade
        clazz.unit = form.unit.data
        clazz.update_id = current_user.id
        clazz.updatetime_utc = datetime.utcfromtimestamp(time.time())
        clazz.updatetime_loc = datetime.fromtimestamp(time.time())
        db.session.commit()
        # 如果是1等级即根类别，则删除关联关系，否则重新设定新上级类别
        if grade == 1:
            parent_class = RelAssetClass.query.filter_by(child_class_id=id).first()
            db.session.delete(parent_class)
            db.session.commit()
        else:
            clazz.set_parent_class(parent)
        flash('资产类别修改成功！')
        return redirect(url_for('.index'))
    return render_template('biz/master/clazz/edit.html', form=form)
@bp_clazz.route('/grade/<id>', methods=['POST'])
@login_required
@log_record('获取类别等级信息')
def grade(id):
    clazz = BizAssetClass.query.get_or_404(id)
    return jsonify(grade=clazz.grade)
def get_parents(clazz=None):
    '''
    获取1/2级类别供选择
    :param clazz_id: 为空表示新增，否则表示编辑
    :return:
    '''
    if clazz:
        # 获取本类别ID及子类别ID
        self_and_child_ids = [clazz.id]
        get_self_and_child_ids(clazz, self_and_child_ids)
        # 剔除掉自身及子类别ID
        return [(clazz.id, (clazz.get_parent_class.name+' / ' if clazz.get_parent_class else '')+clazz.name) for clazz in BizAssetClass.query.filter(BizAssetClass.grade.in_([1, 2])).filter(~BizAssetClass.id.in_(self_and_child_ids)).order_by(BizAssetClass.grade, BizAssetClass.createtime_loc).all()]
    else:
        return [(clazz.id, (clazz.get_parent_class.name + ' / ' if clazz.get_parent_class else '') + clazz.name) for clazz in BizAssetClass.query.filter(BizAssetClass.grade.in_([1, 2])).order_by(BizAssetClass.grade, BizAssetClass.createtime_loc).all()]
def get_self_and_child_ids(parent, children):
    '''
    递归获取类别及子类别ID
    :param clazz:
    :param self_and_children_ids:
    :return:
    '''
    children_clazz = parent.get_child_class
    if children_clazz:
        for child_clazz in children_clazz:
            children.append(child_clazz.child_class_id)
            get_self_and_child_ids(BizAssetClass.query.get(child_clazz.child_class_id), children)
    else:
        return children