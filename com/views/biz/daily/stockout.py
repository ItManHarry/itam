from flask import Blueprint, render_template, flash, redirect, url_for, request, session, current_app, jsonify
from flask_login import login_required, current_user
from com.email import send_mail
from com.models import BizAssetMaster, BizStockOut, AuditBizCode, BizCompany, RelAssetOutItem, BizStockHistory, \
    BizEmployee, AuditItem, RelAuditLineRole, AuditRole, AuditInstance, SysEnum, AuditLine, BizAssetChange
from com.plugins import db
from com.decorators import log_record
from com.forms.biz.daily.stockout import StockoutForm, StockoutSearchForm
import uuid, time
from datetime import datetime, date
from com.views.system.dicts import get_enum_value
from com.utils import get_options, gen_bill_no
from com.views.biz.asset.master import get_stock_amount
bp_stockout = Blueprint('stockout', __name__)
@bp_stockout.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查看出库单信息')
def index():
    form = StockoutSearchForm()
    form.out_type.choices = [('0', '---出库类型(ALL)---')]+get_options('D005')
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        try:
            out_type = session['stockout_view_search_type'] if session['stockout_view_search_type'] else ''     # 出库类型
            out_no = session['stockout_view_search_no'] if session['stockout_view_search_no'] else ''           # 出库单号
        except KeyError:
            out_type = ''
            out_no = ''
        form.out_type.data = out_type
        form.out_no.data = out_no
    if request.method == 'POST':
        page = 1
        out_type = form.out_type.data
        out_no = form.out_no.data
        session['stockout_view_search_type'] = out_type
        session['stockout_view_search_no'] = out_no
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']
    conditions = set()
    conditions.add(BizStockOut.bg_id == current_user.company_id)
    conditions.add(BizStockOut.out_no.like('%'+out_no+'%'))
    print('Out type id is : ', out_type)
    if out_type and out_type != '0':
        conditions.add(BizStockOut.out_type_id == out_type)
    else:
        print('Select all...')
    pagination = BizStockOut.query.filter(*conditions).order_by(BizStockOut.out_no.desc()).paginate(page, per_page)
    stockouts = pagination.items
    return render_template('biz/daily/stockout/index.html', pagination=pagination, stockouts=stockouts, form=form)
@bp_stockout.route('/add', methods=['GET', 'POST'])
@login_required
@log_record('新增资产出库申请单')
def add():
    form = StockoutForm()
    assets = BizAssetMaster.query.filter(BizAssetMaster.is_out == False).order_by(BizAssetMaster.code).all()
    companies = BizCompany.query.order_by(BizCompany.name).all()
    form.out_type_id.choices = get_options('D005')
    biz = AuditBizCode.query.filter(AuditBizCode.code == 'BZ002').first()
    form.audit_line_id.choices = [(line.id, line.name) for line in biz.audit_lines]
    if request.method == 'GET':
        enum = SysEnum.query.get(form.out_type_id.choices[0][0])
        line = AuditLine.query.filter(AuditLine.code == enum.item).first()
        form.audit_line_id.data = line.id
        form.audit_line.data = line.id
        form.out_date.data = date.today().strftime('%Y-%m-%d')
    selected_assets = []
    amount_dict = {}
    if form.out_assets_ids.data:
        selected_assets = BizAssetMaster.query.filter(BizAssetMaster.id.in_(form.out_assets_ids.data.split(','))).order_by(BizAssetMaster.code).all()
        ids = form.out_assets_ids.data.split(',')
        amounts = form.out_assets_amount.data.split(',')
        amount_dict = dict(zip(ids, amounts))
    if form.validate_on_submit():
        form.out_no.data = gen_bill_no('OUT')
        sign = form.sign.data
        if sign == '0':         # 仅保存
            e = get_enum_value('D004', '0')
        else:                   # 保存并提交
            e = get_enum_value('D004', '1')
        stock_out = BizStockOut(
            id=uuid.uuid4().hex,
            bg_id=current_user.company_id,
            create_id=current_user.id,
            out_no=form.out_no.data,
            out_date=datetime.strptime(form.out_date.data, '%Y-%m-%d'),
            out_type_id=form.out_type_id.data,
            audit_line_id=form.audit_line.data,
            charger_id=current_user.id,
            state_id=e.id if e else '',
            summary=form.summary.data
        )
        if form.back_date.data:
            stock_out.back_date = datetime.strptime(form.back_date.data, '%Y-%m-%d')
        db.session.add(stock_out)
        db.session.commit()
        form.id.data = stock_out.id
        save_rels(form)
        flash('资产出库申请成功！')
        return redirect(url_for('.index'))
    return render_template('biz/daily/stockout/add.html', form=form, selected_assets=selected_assets, amount_dict=amount_dict, assets=assets, companies=companies)
@bp_stockout.route('/edit/<action>/<id>', methods=['GET', 'POST'])
@login_required
@log_record('修改出库单信息')
def edit(action, id):
    print('Action is : ', action)
    stock_out = BizStockOut.query.get(id)
    form = StockoutForm()
    form.id.data = id
    form.out_no.data = stock_out.out_no
    rel = RelAssetOutItem.query.filter_by(out_bill_id=id).first()
    assets = BizAssetMaster.query.filter(BizAssetMaster.is_out == False).order_by(BizAssetMaster.code).all()
    companies = BizCompany.query.order_by(BizCompany.name).all()
    form.out_type_id.choices = get_options('D005')
    biz = AuditBizCode.query.filter(AuditBizCode.code == 'BZ002').first()
    form.audit_line_id.choices = [(line.id, line.name) for line in biz.audit_lines]
    asset_ids = []
    asset_ams = []
    items = BizStockHistory.query.filter_by(bill_no=stock_out.out_no).all()
    if items:
        for item in items:
            asset_ids.append(item.asset_id)
            asset_ams.append(str(item.amount))
        amount_dict = dict(zip(asset_ids, asset_ams))
    else:
        amount_dict = {}
    if request.method == 'GET':
        form.take_by_id.data = rel.take_by_id if rel else ''
        form.take_by.data = rel.take_by.name+'('+rel.take_by.code+')' if rel else ''
        form.out_assets_ids.data = ','.join(asset_ids)
        form.out_assets_amount.data = ','.join(asset_ams)
        form.audit_line_id.data = stock_out.audit_line_id
        form.audit_line.data = stock_out.audit_line_id
        form.out_date.data = stock_out.out_date.strftime('%Y-%m-%d')
        form.back_date.data = stock_out.back_date.strftime('%Y-%m-%d') if stock_out.back_date else ''
        form.out_type_id.data = stock_out.out_type_id
        form.summary.data = stock_out.summary
    if form.validate_on_submit():
        '''逻辑：
                先将之前出库的数据还原后再执行保存
                1. 还原库存余额
                2. 删除出库履历记录
        '''
        # 还原资产状态及库存余额
        items = BizStockHistory.query.filter_by(bill_no=stock_out.out_no).all()
        for item in items:
            asset = BizAssetMaster.query.get(item.asset_id)
            # 库存状态为已出库
            asset.is_out = False
            # 资产状态-在库
            e = get_enum_value('D003', '1')
            if e:
                asset.status_id = e.id
            stock_amount = get_stock_amount(asset)
            if stock_amount and stock_amount.amount:
                stock_amount.amount += item.amount
        db.session.commit()
        # 删除库存履历
        for item in items:
            db.session.delete(item)
            db.session.commit()
        # 执行数据保存
        sign = form.sign.data
        if sign == '0':     # 仅保存
            e = get_enum_value('D004', '0')
        else:               # 保存并提交
            e = get_enum_value('D004', '1')
        stock_out.out_date = datetime.strptime(form.out_date.data, '%Y-%m-%d')
        stock_out.out_type_id = form.out_type_id.data
        stock_out.audit_line_id = form.audit_line.data
        stock_out.charger_id = current_user.id
        stock_out.state_id = e.id if e else ''
        stock_out.summary = form.summary.data
        if form.back_date.data:
            stock_out.back_date = datetime.strptime(form.back_date.data, '%Y-%m-%d')
        stock_out.update_id = current_user.id
        stock_out.updatetime_utc = datetime.utcfromtimestamp(time.time())
        stock_out.updatetime_loc = datetime.fromtimestamp(time.time())
        db.session.commit()
        save_rels(form)
        flash('资产出库修改成功！')
        return redirect(url_for('.index'))
    return render_template('biz/daily/stockout/edit.html', form=form, selected_assets=stock_out.assets, amount_dict=amount_dict, assets=assets, companies=companies, action=action)
@bp_stockout.route('/audit/<type_id>', methods=['GET', 'POST'])
def set_audit(type_id):
    '''
    根据出库类型设定审批模板
    :param type_id:
    :return:
    '''
    enum = SysEnum.query.get(type_id)
    print('Stock out type code is : ', enum.item)
    line = AuditLine.query.filter(AuditLine.code == enum.item).first()
    return jsonify(line_id=line.id)
def save_rels(form):
    sign = form.sign.data
    give_by = BizEmployee.query.filter_by(code=current_user.user_id).first()
    selected_assets = BizAssetMaster.query.filter(BizAssetMaster.id.in_(form.out_assets_ids.data.split(','))).order_by(BizAssetMaster.code).all()
    ids = form.out_assets_ids.data.split(',')
    amounts = form.out_assets_amount.data.split(',')
    amount_dict = dict(zip(ids, amounts))
    for asset in selected_assets:
        # 库存状态为已出库
        asset.is_out = True
        # 资产状态
        stock_type = SysEnum.query.get(form.out_type_id.data)
        code = '3'
        if stock_type.item == 'T003':
            code = '2'
        if stock_type.item == 'T004':
            code = '4'
        e = get_enum_value('D003', code)
        if e:
            asset.status_id = e.id
        # 领用发放->更新资产使用者没有使用者时新增变更履历
        '''
        此逻辑与实际业务逻辑不符 -> 领用人不等同于使用人，故屏蔽
        if stock_type.item == 'T003':
            if not asset.user:
                change = BizAssetChange(
                    id=uuid.uuid4().hex,
                    change_date=datetime.today(),
                    asset_id=asset.id,
                    new_holder_id=form.take_by_id.data
                )
                db.session.add(change)
            # 更改资产使用者信息
            asset.user_id = form.take_by_id.data
            used_by = BizEmployee.query.get(form.take_by_id.data)
            asset.department_id = used_by.department_id
            asset.company_id = used_by.company_id
            db.session.commit()
        '''
        amount = int(amount_dict[asset.id])
        rel = RelAssetOutItem(
            id=uuid.uuid4().hex,
            out_bill_id=form.id.data,
            asset_id=asset.id,
            amount=amount,
            give_by_id=give_by.id,
            take_by_id=form.take_by_id.data
        )
        db.session.add(rel)
        # 写入出入库履历
        io_history = BizStockHistory(
            id=uuid.uuid4().hex,
            bg_id=current_user.company_id,
            bill_no=form.out_no.data,
            asset_id=asset.id,
            class1_id=asset.class1_id,
            class2_id=asset.class2_id,
            class3_id=asset.class3_id,
            brand_id=asset.brand_id,
            model_id=asset.model_id,
            io_type=0,
            amount=amount,
            code=asset.code,
            sap_code=asset.sap_code
        )
        io_type = SysEnum.query.get(form.out_type_id.data)
        if io_type.item == '1':
            code = '3'
        elif io_type.item == '2':
            code = '4'
        else:
            code = '5'
        # 出入库类型
        e = get_enum_value('D010', code)
        if e:
            io_history.io_class_id = e.id
        db.session.add(io_history)
        # 更新库存余额
        stock_amount = get_stock_amount(asset)
        if stock_amount and stock_amount.amount:
            stock_amount.amount -= amount
    db.session.commit()
    # 保存并提交时执行
    if sign == '1':
        # 如果是"发放申请"，则发邮件给资产使用者
        for asset in selected_assets:
            if asset.is_asset and asset.user and asset.user.email:
                send_mail(subject='资产接收确认', to=[asset.user.email], cc=[], template='emails/asset_sign_remind', asset=asset)
        # 写入待审批
        audit_item = AuditItem(
            id=uuid.uuid4().hex,
            bg_id=current_user.company_id,
            audit_line_id=form.audit_line.data,
            bill_no=form.out_no.data,
            bill_type='SO',
            audit_level=1
        )
        db.session.add(audit_item)
        db.session.commit()
        # 发送邮件提醒
        rel = RelAuditLineRole.query.filter(RelAuditLineRole.audit_line_id == form.audit_line.data, RelAuditLineRole.audit_grade == 1).first()
        if rel:
            audit_role = AuditRole.query.get(rel.audit_role_id)
            auditors = audit_role.auditors
            if auditors:
                # 生成Work To Do
                for user in auditors:
                    audit_instance = AuditInstance(
                        id=uuid.uuid4().hex,
                        audit_item_id=audit_item.id,
                        user_id=user.id
                    )
                    db.session.add(audit_instance)
                db.session.commit()
                to = [user.email for user in auditors]
            else:
                to = []
            if to:
                print('Send mail to : ', to)
                send_mail(subject='资产出库审批提醒', to=to, cc=[], template='emails/stockout_approve_remind', assets=selected_assets, amount_dict=amount_dict)