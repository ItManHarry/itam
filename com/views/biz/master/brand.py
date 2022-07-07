from flask import Blueprint, render_template, flash, redirect, url_for, request, session, current_app
from flask_login import login_required, current_user
from com.models import BizBrandMaster
from com.plugins import db
from com.decorators import log_record
from com.forms.biz.master.brand import BrandSearchForm, BrandForm
import uuid, time
from datetime import datetime
bp_brand = Blueprint('brand', __name__)
@bp_brand.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查看品牌分类信息')
def index():
    form = BrandSearchForm()
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        try:
            code = session['brand_view_search_code'] if session['brand_view_search_code'] else ''  # 字典代码
            name = session['brand_view_search_name'] if session['brand_view_search_name'] else ''  # 字典名称
        except KeyError:
            code = ''
            name = ''
        form.code.data = code
        form.name.data = name
    if request.method == 'POST':
        page = 1
        code = form.code.data
        name = form.name.data
        session['brand_view_search_code'] = code
        session['brand_view_search_name'] = name
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']
    pagination = BizBrandMaster.query.filter(BizBrandMaster.bg_id == current_user.company_id).filter(BizBrandMaster.code.like('%'+code+'%'), BizBrandMaster.name.like('%'+name+'%')).order_by(BizBrandMaster.code).paginate(page, per_page)
    brands = pagination.items
    return render_template('biz/master/brand/index.html', pagination=pagination, brands=brands, form=form)
@bp_brand.route('/add', methods=['GET', 'POST'])
@login_required
@log_record('新增品牌信息')
def add():
    form = BrandForm()
    if form.validate_on_submit():
        brand = BizBrandMaster(id=uuid.uuid4().hex, code=form.code.data.upper(), name=form.name.data, bg_id=current_user.company_id, create_id=current_user.id)
        db.session.add(brand)
        db.session.commit()
        flash('品牌信息添加成功！')
        return redirect(url_for('.index'))
    return render_template('biz/master/brand/add.html', form=form)
@bp_brand.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
@log_record('修改品牌信息')
def edit(id):
    form = BrandForm()
    brand = BizBrandMaster.query.get_or_404(id)
    if request.method == 'GET':
        form.id.data = brand.id
        form.code.data = brand.code
        form.name.data = brand.name
    if form.validate_on_submit():
        brand.code = form.code.data
        brand.name = form.name.data
        brand.update_id = current_user.id
        brand.updatetime_utc = datetime.utcfromtimestamp(time.time())
        brand.updatetime_loc = datetime.fromtimestamp(time.time())
        db.session.commit()
        flash('品牌信息更新成功！')
        return redirect(url_for('.index'))
    return render_template('biz/master/brand/edit.html', form=form)