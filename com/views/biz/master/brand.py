from flask import Blueprint, render_template, flash, redirect, url_for, request, session, current_app, jsonify
from flask_login import login_required, current_user
from com.models import BizBrandMaster, BizBrandModel
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
            code = session['brand_view_search_code'] if session['brand_view_search_code'] else ''  # 品牌代码
            name = session['brand_view_search_name'] if session['brand_view_search_name'] else ''  # 品牌名称
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
@bp_brand.route('/models/<brand_id>', methods=['POST'])
@login_required
@log_record('获取品牌型号信息')
def models(brand_id):
    brand = BizBrandMaster.query.get_or_404(brand_id)
    models = [(model.id, model.name, model.code if model.code else '') for model in brand.models]
    '''
    for model in brand.models:
        models.append((model.id, model.code, model.name if model.name else ''))
    '''
    return jsonify(models=sorted(models, key=lambda e: e[2]))
@bp_brand.route('/model_add', methods=['POST'])
@login_required
@log_record('维护品牌型号信息')
def model_add():
    data = request.get_json()
    brand_id = data['brand_id']
    brand = BizBrandMaster.query.get_or_404(brand_id)
    # # 先移除已关联的型号值 - 此逻辑剔除,系统只做新增/修改操作
    # for model in brand.models:
    #     brand.models.remove(model)
    #     db.session.commit()
    # 移除的型号信息执行删除
    # removed = data['removed']
    # print('Removed : ', removed)
    # for model_id in removed:
    #     model = BizBrandModel.query.get(model_id)
    #     if model:
    #         db.session.delete(model)
    #         db.session.commit()
    # 新增/修改型号信息
    models = data['p_models']
    for model in models:
        print('Model id : ', model['id'], ', code : ', model['code'], ', display : ', model['name'])
        model_entity = BizBrandModel.query.get(str(model['id']))
        if model_entity:
            model_entity.code = model['code']
            model_entity.name = model['name']
            model_entity.update_id = current_user.id
            model_entity.updatetime_utc = datetime.utcfromtimestamp(time.time())
            model_entity.updatetime_loc = datetime.fromtimestamp(time.time())
        else:
            model_entity = BizBrandModel(id=uuid.uuid4().hex, code=model['code'], name=model['name'], create_id=current_user.id)
            brand.models.append(model_entity)
    db.session.commit()
    return jsonify(code=1, message='型号信息维护成功!')
@bp_brand.route('/get_brands', methods=['GET', 'POST'])
@login_required
@log_record('获取所有品牌信息')
def get_brands():
    brands = BizBrandMaster.query.order_by(BizBrandMaster.name).all()
    options = [(brand.id, brand.name) for brand in brands]
    return jsonify(options=options)
@bp_brand.route('/get_model_options/<brand_id>', methods=['POST'])
@login_required
@log_record('获取型号下拉选项')
def get_model_options(brand_id):
    brand = BizBrandMaster.query.get(brand_id)
    options = [(model.id, model.name) for model in brand.models] if brand else []
    return jsonify(options=options)