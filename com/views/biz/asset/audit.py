from flask import Blueprint, render_template, flash, redirect, url_for, request,current_app,session, jsonify
from flask_login import login_required, current_user
from com.models import BizStockIn, SysUser, SysEnum, AuditItem, AuditInstance, SysDict
from flask_wtf import form
from wtforms import SelectField
from wtforms.validators import DataRequired
from com.views.system.dicts import get_enum_value
from com.forms.biz.asset.audit import  AuditSearchForm,AuditForm
from com.forms.biz.asset.master import AssetForm
from com.models import BizAssetApply, BizCompany, BizDepartment, BizEmployee
from com.plugins import db
from com.decorators import log_record
import uuid, time
from datetime import datetime
from com.utils import gen_bill_no #引用生成单号函数
bp_audit = Blueprint('audit', __name__)
@bp_audit.route('/index', methods=['GET', 'POST'])
@login_required ###必须登录画面
@log_record('查看资产审批清单')###记录操作日志
def index():
    form = AuditSearchForm()
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        try:
            in_no = session['audit_view_search_in_no'] if session['audit_view_search_in_no'] else ''  # 字典代码
        except KeyError:
            in_no = ''
        form.in_no.data = in_no
    if request.method == 'POST':
        page = 1
        in_no = form.in_no.data
        session['audit_view_search_in_no'] = in_no
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']
    pagination = BizStockIn.query.filter(BizStockIn.bg_id==current_user.company_id).filter(BizStockIn.in_no.like('%'+in_no+'%')).order_by(BizStockIn.in_no).paginate(page, per_page)
    audits = pagination.items

    return render_template('biz/asset/audit/index.html',pagination=pagination,form=form,audits=audits)
@bp_audit.route('/edit/<id>', methods=['GET', 'POST'])
@login_required ###必须登录画面
@log_record('资产信息明细编辑')###记录操作日志
def edit(id):
    form = AuditForm()
    audit = BizStockIn.query.get_or_404(id)

    if request.method == 'GET':
        form.id.data = id
        form.in_no.data = audit.in_no
        form.in_date.data = audit.in_date
        # form.charger_id.data = audit.charger_id
        # form.state_id.data = audit.state_id
        form.charger_id.data = audit.charger.user_name
        form.state_id.data = audit.state.display
    if form.validate_on_submit():
        audit.in_no = form.in_no.data
        audit.in_date = form.in_date.data
        audit.charger_id = form.charger_id.data
        audit.state_id = form.state_id.data
        audit.update_id = current_user.id
        audit.updatetime_utc = datetime.utcfromtimestamp(time.time())
        audit.updatetime_loc = datetime.fromtimestamp(time.time())
        db.session.commit()
        flash('资产明细修改成功！')
        return redirect(url_for('.index'))
        ###开始保存
    return render_template('biz/asset/audit/edit.html', form=form, assets=audit.assets)
@bp_audit.route('/resubmit/<id>', methods=['POST'])
@log_record('重新提交审批')
def resubmit(id):
    print('ID is : ', id)
    audit = BizStockIn.query.get_or_404(id)
    e = get_enum_value('D004', '1')#用于获取字典信息的字典明细方法是code加value
    audit.state_id = e.id if e else ''
    audit.update_id = current_user.id
    audit.updatetime_utc = datetime.utcfromtimestamp(time.time())
    audit.updatetime_loc = datetime.fromtimestamp(time.time())



    audit_item = AuditItem.query.filter(AuditItem.bill_no == audit.in_no).first()
    audit_item.resubmit = False  ######0表示false，1表示true
    audit_item.update_id = current_user.id
    audit_item.updatetime_utc = datetime.utcfromtimestamp(time.time())
    audit_item.updatetime_loc = datetime.fromtimestamp(time.time())
    # db.session.commit()
    audit_instance = AuditInstance(
        id=uuid.uuid4().hex,
        audit_item_id=audit_item.id,
        user_id=current_user.id
    )
    db.session.add(audit_instance)
    db.session.commit()

    return jsonify(code=1, message='重新提交审批完成！')