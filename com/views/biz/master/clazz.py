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
    pagination = BizAssetClass.query.filter(BizAssetClass.bg_id == current_user.company_id).filter(BizAssetClass.code.like('%' + code.upper() + '%'), BizAssetClass.name.like('%' + name + '%')).order_by(BizAssetClass.grade).order_by(BizAssetClass.code).paginate(page, per_page)
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
            code=gen_class_code(form),
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
    old_parent = clazz.get_parent_class
    old_grade = clazz.grade
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
            # 由2/3级调整为1级的情况下重新生成代码
            if old_grade != 1:
                clazz.code = gen_class_code(form)
        else:
            parent = BizAssetClass.query.get(form.parent.data)
            grade = parent.grade + 1
            # 父类别变更的情况下重新生成代码
            if old_parent:
                if old_parent.code != parent.code:
                    clazz.code = gen_class_code(form)
            else:
                clazz.code = gen_class_code(form)
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
            if parent_class:
                db.session.delete(parent_class)
                db.session.commit()
        else:
            clazz.set_parent_class(parent)
        flash('资产类别修改成功！')
        return redirect(url_for('.index'))
    return render_template('biz/master/clazz/edit.html', form=form)
def gen_class_code(form):
    '''
    生成资产类别代码
    :param form:
    :return:
    '''
    if form.has_parent.data and form.parent.data:
        # 子类别代码生成
        parent_class = BizAssetClass.query.get(form.parent.data)
        children = parent_class.get_child_class
        if children:
            codes = [child.child_class.code for child in children]
            new_code_num = int(max(codes)[-3:]) + 1
            if new_code_num < 10:
                return parent_class.code + '00' + str(new_code_num)
            elif new_code_num < 100:
                return parent_class.code + '0' + str(new_code_num)
            else:
                return parent_class.code + str(new_code_num)
        else:
            return parent_class.code + '001'
    else:
        # 一级分类代码生成
        class1_all = BizAssetClass.query.filter(BizAssetClass.grade == 1).all()
        if class1_all:
            return '0' + str(len(class1_all)+1) if len(class1_all)+1 < 10 else str(len(class1_all)+1)
        else:
            return '01'
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
@bp_clazz.route('/get_class2_options', methods=['GET', 'POST'])
@login_required
@log_record('获取二级分类下拉选项')
def get_class2_options():
    class2 = BizAssetClass.query.filter_by(grade=2).order_by(BizAssetClass.code).all()
    options = [(clazz.id, clazz.name) for clazz in class2]
    return jsonify(options=options)
@bp_clazz.route('/get_class3_options/<class2_id>', methods=['POST'])
@login_required
@log_record('获取三级分类下拉选项')
def get_class3_options(class2_id):
    class2 = BizAssetClass.query.get(class2_id)
    options = [(rel.child_class_id, rel.child_class.name) for rel in class2.get_child_class] if class2 else []
    return jsonify(options=options)
@bp_clazz.route('/get_class3_unit/<class3_id>', methods=['POST'])
@login_required
@log_record('获取三级分类单位')
def get_class3_unit(class3_id):
    class3 = BizAssetClass.query.get(class3_id)
    return jsonify(unit=class3.unit)