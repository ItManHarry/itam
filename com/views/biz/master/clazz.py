from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app, session
from flask_login import login_required, current_user
from com.models import BizAssetClass
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
    form.parent.choices = [(clazz.id, clazz.name) for clazz in BizAssetClass.query.filter(BizAssetClass.grade.in_([1, 2])).all()]
    if request.method == 'GET':
        form.has_parent.data = True
    if form.validate_on_submit():
        clazz = BizAssetClass(
            id=uuid.uuid4().hex,
            code=form.code.data.upper(),
            name=form.name.data,
            unit=form.unit.data,
            bg_id=current_user.company_id,
            create_id=current_user.id
        )
        db.session.add(clazz)
        db.session.commit()
        flash('资产类别添加成功！')
        return redirect(url_for('.index'))
    return render_template('biz/master/clazz/add.html', form=form)
@bp_clazz.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
@log_record('修改资产类别信息')
def edit(id):
    form = ClazzForm()
    clazz = BizAssetClass.query.get_or_404(id)
    if request.method == 'GET':
        form.id.data = id
        form.code.data = clazz.code
        form.name.data = clazz.name
        form.unit.data = clazz.unit
    if form.validate_on_submit():
        clazz.code = form.code.data.upper()
        clazz.name = form.name.data
        clazz.unit = form.unit.data
        clazz.update_id = current_user.id
        clazz.updatetime_utc = datetime.utcfromtimestamp(time.time())
        clazz.updatetime_loc = datetime.fromtimestamp(time.time())
        db.session.commit()
        flash('资产类别修改成功！')
        return redirect(url_for('.index'))
    return render_template('biz/master/clazz/edit.html', form=form)