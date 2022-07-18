from flask import Blueprint, render_template, flash, redirect, url_for, request, session, current_app, jsonify
from flask_login import login_required, current_user
from com.models import AuditLine, AuditBizCode, RelAuditLineRole, AuditRole
from com.plugins import db
from com.decorators import log_record
from com.forms.biz.audit.line import LineSearchForm, LineForm
import uuid, time
from datetime import datetime
bp_line = Blueprint('line', __name__)
@bp_line.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查看审批模板信息')
def index():    
    form = LineSearchForm()
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        try:
            code = session['line_view_search_code'] if session['line_view_search_code'] else ''  # 模板代码
            name = session['line_view_search_name'] if session['line_view_search_name'] else ''  # 模板名称
        except KeyError:
            code = ''
            name = ''
        form.code.data = code
        form.name.data = name
    if request.method == 'POST':
        page = 1
        code = form.code.data
        name = form.name.data
        session['line_view_search_code'] = code
        session['line_view_search_name'] = name
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']
    pagination = AuditLine.query.filter(AuditLine.bg_id == current_user.company_id).filter(AuditLine.code.like('%'+code+'%'), AuditLine.name.like('%'+name+'%')).order_by(AuditLine.code).paginate(page, per_page)
    lines = pagination.items
    roles = AuditRole.query.order_by(AuditRole.name).all()
    return render_template('biz/audit/line/index.html', pagination=pagination, lines=lines, form=form, roles=roles)
@bp_line.route('/add', methods=['GET', 'POST'])
@login_required
@log_record('新增审批模板信息')
def add():
    form = LineForm()
    form.biz_code.choices = [(code.id, code.name) for code in AuditBizCode.query.order_by(AuditBizCode.name).all()]
    if form.validate_on_submit():
        line = AuditLine(id=uuid.uuid4().hex,
                         code=form.code.data.upper(),
                         name=form.name.data,
                         biz_code_id=form.biz_code.data,
                         remark=form.remark.data,
                         bg_id=current_user.company_id,
                         create_id=current_user.id)
        db.session.add(line)
        db.session.commit()
        flash('审批模板添加成功！')
        return redirect(url_for('.index'))
    return render_template('biz/audit/line/add.html', form=form)
@bp_line.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
@log_record('修改审批模板信息')
def edit(id):
    form = LineForm()
    form.biz_code.choices = [(code.id, code.name) for code in AuditBizCode.query.order_by(AuditBizCode.name).all()]
    line = AuditLine.query.get_or_404(id)
    if request.method == 'GET':
        form.id.data = line.id
        form.code.data = line.code
        form.name.data = line.name
        form.biz_code.data = line.biz_code_id
        form.remark.data = line.remark
    if form.validate_on_submit():
        line.code = form.code.data
        line.name = form.name.data
        line.biz_code_id = form.biz_code.data
        line.remark = form.remark.data
        line.update_id = current_user.id
        line.updatetime_utc = datetime.utcfromtimestamp(time.time())
        line.updatetime_loc = datetime.fromtimestamp(time.time())
        db.session.commit()
        flash('审批模板更新成功！')
        return redirect(url_for('.index'))
    return render_template('biz/audit/line/edit.html', form=form)
@bp_line.route('/audit_nodes/<line_id>', methods=['POST'])
@login_required
@log_record('获取模板审批线信息')
def audit_nodes(line_id):
    rels = RelAuditLineRole.query.filter_by(audit_line_id=line_id).order_by(RelAuditLineRole.audit_grade).all()
    nodes = []
    for rel in rels:
        role = AuditRole.query.get(rel.audit_role_id)
        nodes.append(dict(role=role.name, grade=rel.audit_grade, people=','.join([user.user_name for user in role.auditors]), rel_id=rel.id))
    return jsonify(nodes=nodes)
@bp_line.route('/node_add', methods=['POST'])
@login_required
@log_record('保存模板审批线信息')
def node_add():
    data = request.get_json()
    line_id, role_id = data['line_id'], data['role_id']
    print('Line id is {}, role id is {}'.format(line_id, role_id))
    grade = RelAuditLineRole.query.filter_by(audit_line_id=line_id).count() + 1
    rel = RelAuditLineRole(id=uuid.uuid4().hex, audit_line_id=line_id, audit_role_id=role_id, audit_grade=grade, create_id=current_user.id)
    db.session.add(rel)
    db.session.commit()
    return jsonify(code=1, message='审批角色添加成功!')
@bp_line.route('/node_remove', methods=['POST'])
@login_required
@log_record('移除审批角色')
def node_remove():
    data = request.get_json()
    rel_id = data['rel_id']
    print('Rel id is {}.'.format(rel_id))
    rel = RelAuditLineRole.query.get(rel_id)
    db.session.delete(rel)
    db.session.commit()
    return jsonify(code=1, message='审批角色移除成功!')