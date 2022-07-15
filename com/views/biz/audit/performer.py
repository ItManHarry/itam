from flask import Blueprint, render_template, flash, redirect, url_for, request, session, current_app, jsonify
from flask_login import login_required, current_user
from com.models import AuditRole, SysUser
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
            code = session['performer_view_search_code'] if session['performer_view_search_code'] else ''  # 角色代码
            name = session['performer_view_search_name'] if session['performer_view_search_name'] else ''  # 角色名称
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
@bp_performer.route('/people/<performer_id>', methods=['POST'])
@login_required
@log_record('获取角色人员信息')
def people(performer_id):
    performer = AuditRole.query.get_or_404(performer_id)
    selected = [(user.id, user.user_name) for user in performer.auditors]
    selected_ids = [user.id for user in performer.auditors]
    for_select = [(user.id, user.user_name) for user in SysUser.query.filter(~SysUser.id.in_(selected_ids)).filter(SysUser.user_id != 'admin').all()]
    return jsonify(for_select=sorted(for_select, key=lambda e: e[1]), selected=sorted(selected, key=lambda e: e[1]))
@bp_performer.route('/people_add', methods=['POST'])
@login_required
@log_record('保存审批人员信息')
def people_add():
    data = request.get_json()
    performer_id, people = data['performer_id'], data['people']
    # print('Performer ID : ', performer_id)
    # print('People : ', people)
    performer = AuditRole.query.get_or_404(performer_id)
    # 先移除已添加的人员再追加新指定的人员
    for auditor in performer.auditors:
        performer.auditors.remove(auditor)
        db.session.commit()
    # 保存最新的审批人
    for auditor_id in people:
        auditor = SysUser.query.get(auditor_id)
        # print('User name : ', auditor.user_name)
        performer.auditors.append(auditor)
        db.session.commit()
    return jsonify(code=1, message='审批人员维护成功!')