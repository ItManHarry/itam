from flask import Blueprint, render_template, flash, redirect, url_for, request, session, current_app, jsonify
from flask_login import login_required, current_user
from com.models import AuditRole
from com.plugins import db
from com.decorators import log_record
from com.forms.biz.audit.performer import PerformerSearchForm, PerformerForm
import uuid, time
from datetime import datetime
bp_performer = Blueprint('performer', __name__)
@bp_performer.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查看审批角色信息')
def index():    
    form = PerformerSearchForm()
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        try:
            code = session['performer_view_search_code'] if session['performer_view_search_code'] else ''  # 字典代码
            name = session['performer_view_search_name'] if session['performer_view_search_name'] else ''  # 字典名称
        except KeyError:
            code = ''
            name = ''
        form.code.data = code
        form.name.data = name
    if request.method == 'POST':
        page = 1
        code = form.code.data
        name = form.name.data
        session['performer_view_search_code'] = code
        session['performer_view_search_name'] = name
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']
    pagination = AuditRole.query.filter(AuditRole.bg_id == current_user.company_id).filter(AuditRole.code.like('%'+code+'%'), AuditRole.name.like('%'+name+'%')).order_by(AuditRole.code).paginate(page, per_page)
    performers = pagination.items
    return render_template('biz/audit/performer/index.html', pagination=pagination, performers=performers, form=form)
@bp_performer.route('/add', methods=['GET', 'POST'])
@login_required
@log_record('新增审批角色信息')
def add():
    form = PerformerForm()
    if form.validate_on_submit():
        performer = AuditRole(id=uuid.uuid4().hex, code=form.code.data.upper(), name=form.name.data, bg_id=current_user.company_id, create_id=current_user.id)
        db.session.add(performer)
        db.session.commit()
        flash('审批角色添加成功！')
        return redirect(url_for('.index'))
    return render_template('biz/audit/performer/add.html', form=form)
@bp_performer.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
@log_record('修改审批角色信息')
def edit(id):
    form = PerformerForm()
    performer = AuditRole.query.get_or_404(id)
    if request.method == 'GET':
        form.id.data = performer.id
        form.code.data = performer.code
        form.name.data = performer.name
    if form.validate_on_submit():
        performer.code = form.code.data
        performer.name = form.name.data
        performer.update_id = current_user.id
        performer.updatetime_utc = datetime.utcfromtimestamp(time.time())
        performer.updatetime_loc = datetime.fromtimestamp(time.time())
        db.session.commit()
        flash('审批角色更新成功！')
        return redirect(url_for('.index'))
    return render_template('biz/audit/performer/edit.html', form=form)

# @bp_performer.route('/models/<brand_id>', methods=['POST'])
# @login_required
# @log_record('获取品牌型号信息')
# def models(brand_id):
#     performer = AuditRole.query.get_or_404(brand_id)
#     models = [(model.id, model.name, model.code if model.code else '') for model in performer.models]
#     '''
#     for model in performer.models:
#         models.append((model.id, model.code, model.name if model.name else ''))
#     '''
#     return jsonify(models=sorted(models, key=lambda e: e[2]))
# @bp_performer.route('/model_add', methods=['POST'])
# @login_required
# @log_record('维护品牌型号信息')
# def model_add():
#     data = request.get_json()
#     brand_id = data['brand_id']
#     performer = AuditRole.query.get_or_404(brand_id)
#     # 先移除已关联的型号值
#     for model in performer.models:
#         performer.models.remove(model)
#     db.session.commit()
#     # 移除的型号信息执行删除
#     removed = data['removed']
#     print('Removed : ', removed)
#     for model_id in removed:
#         model = BizBrandModel.query.get(model_id)
#         if model:
#             db.session.delete(model)
#     db.session.commit()
#     # 关联型号信息
#     models = data['p_models']
#     for model in models:
#         print('Model id : ', model['id'], ', code : ', model['code'], ', display : ', model['name'])
#         model_entity = BizBrandModel.query.get(str(model['id']))
#         if model_entity:
#             model_entity.code = model['code']
#             model_entity.name = model['name']
#             model_entity.update_id = current_user.id
#             model_entity.updatetime_utc = datetime.utcfromtimestamp(time.time())
#             model_entity.updatetime_loc = datetime.fromtimestamp(time.time())
#             db.session.commit()
#         else:
#             model_entity = BizBrandModel(id=uuid.uuid4().hex, code=model['code'], name=model['name'], create_id=current_user.id)
#             db.session.add(model_entity)
#         performer.models.append(model_entity)
#     db.session.commit()
#     return jsonify(code=1, message='型号信息维护成功!')