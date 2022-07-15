from flask import Blueprint, render_template, flash, redirect, url_for, request, session, current_app, jsonify
from flask_login import login_required, current_user
from com.models import AuditLine, AuditBizCode
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
    roles = AuditBizCode.query.order_by(AuditBizCode.name).all()
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
    pass
    # line = AuditLine.query.get_or_404(line_id)
    # selected = [(user.id, user.user_name) for user in line.auditors]
    # selected_ids = [user.id for user in line.auditors]
    # for_select = [(user.id, user.user_name) for user in SysUser.query.filter(~SysUser.id.in_(selected_ids)).filter(SysUser.user_id != 'admin').all()]
    # return jsonify(for_select=sorted(for_select, key=lambda e: e[1]), selected=sorted(selected, key=lambda e: e[1]))
@bp_line.route('/node_add', methods=['POST'])
@login_required
@log_record('保存模板审批线信息')
def node_add():
    data = request.get_json()
    # line_id, audit_nodes = data['line_id'], data['audit_nodes']
    # # print('Performer ID : ', line_id)
    # # print('People : ', audit_nodes)
    # line = AuditLine.query.get_or_404(line_id)
    # # 先移除已添加的人员再追加新指定的人员
    # for auditor in line.auditors:
    #     line.auditors.remove(auditor)
    #     db.session.commit()
    # # 保存最新的审批人
    # for auditor_id in audit_nodes:
    #     auditor = SysUser.query.get(auditor_id)
    #     # print('User name : ', auditor.user_name)
    #     line.auditors.append(auditor)
    #     db.session.commit()
    return jsonify(code=1, message='审批线维护成功!')