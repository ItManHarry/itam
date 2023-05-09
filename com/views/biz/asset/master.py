from flask import Blueprint, render_template, flash, redirect, url_for, request, session, current_app, jsonify, send_from_directory
from flask_login import login_required, current_user
from com.models import BizAssetMaster, BizAssetClass, BizBrandMaster, BizVendorMaster, BizStoreMaster, BizCompany, \
    BizAssetBuy, BizEmployee, BizAssetMaint, BizAssetProperty, BizStockIn, BizStockHistory, BizStockAmount, AuditLine, \
    AuditItem, AuditInstance, RelAuditLineRole, AuditRole, BizAssetRepair, SysEnum, BizAssetScrap, BizAssetChange, \
    BizBrandModel, SysDict, BizDepartment
from com.plugins import db
from com.views.system.dicts import get_enum_value
from com.decorators import log_record
from com.forms.biz.asset.master import SearchForm, AssetForm, AssetSignForm
from com.email import send_mail
from datetime import datetime
from com.utils import gen_bill_no, gen_qrcode, gen_barcode, get_options
import uuid, time, os, xlrd2
from collections import namedtuple
bp_master = Blueprint('master', __name__)
@bp_master.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查看资产主数据信息')
def index():
    class1 = request.args.get('class1', type=int) if request.args.get('class1') else 1  # 1:资产 0:耗材  默认为1
    form = SearchForm()
    form.companies.choices = [('0', '资产法人-All')]+[(company.id, company.name) for company in BizCompany.query.order_by(BizCompany.code).all()]
    # 资产类别一级大类代码必须是'01':资产'02':耗材
    class_1 = BizAssetClass.query.filter(BizAssetClass.code == '01', BizAssetClass.bg_id == current_user.company_id).first() if class1 == 1 else BizAssetClass.query.filter(BizAssetClass.code == '02', BizAssetClass.bg_id == current_user.company_id).first()
    form.class2.choices = [('0', '资产分类-All')]
    if class_1:
        form.class2.choices += [(rel.child_class_id, rel.child_class.name) for rel in class_1.get_child_class]
    form.brands.choices = [('0', '品牌-All')]
    brands = BizBrandMaster.query.filter(BizBrandMaster.bg_id == current_user.company_id).order_by(BizBrandMaster.name).all()
    if brands:
        form.brands.choices += [(brand.id, brand.name) for brand in brands]
    if request.method == 'GET':
        page = request.args.get('page', type=int) if request.args.get('page') else 0
        # 如果是分页的话，就要取对应的搜索值，否则所有条件置空
        if page: # 分页查看
            searched = False
            try:
                session['asset_view_search_class2']
                searched = True
            except KeyError:
                print('NOT SEARCHED AT ALL!')
            form.class2.data = session['asset_view_search_class2'] if searched else '0'
            form.brands.data = session['asset_view_search_brands'] if searched else '0'
            form.code.data = session['asset_view_search_code'] if searched else ''
            if class1 == 1:
                form.sap_code.data = session['asset_view_search_sap_code'] if searched else ''
                form.used_by_id.data = session['asset_view_search_used_by'] if searched else ''
                form.companies.data = session['asset_view_search_company'] if searched else '0'
            if form.class2.data is None or form.class2.data == '0':
                form.class3.choices = [('0', '资产名称-All')]
            else:
                class_2 = BizAssetClass.query.get(form.class2.data)
                form.class3.choices = [('0', '资产名称-All')]+[(rel.child_class_id, rel.child_class.name) for rel in class_2.get_child_class]
                form.class3.data = session['asset_view_search_class3'] if searched else '0'
            if form.brands.data is None or form.brands.data == '0':
                form.models.choices = [('0', '型号-All')]
            else:
                brand = BizBrandMaster.query.get(form.brands.data)
                form.models.choices = [('0', '型号-All')]+[(model.id, model.name) for model in brand.models]
                form.models.data = session['asset_view_search_models'] if searched else '0'
        else: # 初始登录
            page = 1
            try:
                del session['asset_view_search_class2']
            except KeyError:
                print('NOT SET THIS KEY!!!')
            form.class3.choices = [('0', '资产名称-All')]
            form.models.choices = [('0', '型号-All')]
            form.code.data = ''
            if class1 == 1:
                form.sap_code.data = ''
                form.used_by.data = ''
                form.used_by_id.data = ''
    if request.method == 'POST':
        page = 1
        first_search = True
        try:
            session['asset_view_search_class2']
            first_search = False
        except KeyError:
            print('THIS IS FIRST TIME OF SEARCHING!')
        if form.class2.data == '0':
            form.class3.choices = [('0', '资产名称-All')]
            form.class3.data = '0'
        else:
            class_2 = BizAssetClass.query.get(form.class2.data)
            form.class3.choices = [('0', '资产名称-All')] + [(rel.child_class_id, rel.child_class.name) for rel in class_2.get_child_class]
            if not first_search:
                if session['asset_view_search_class2'] is not None and session['asset_view_search_class2'] != form.class2.data:
                    form.class3.data = '0'
        if form.brands.data == '0':
            form.models.choices = [('0', '型号-All')]
            form.models.data = '0'
        else:
            brand = BizBrandMaster.query.get(form.brands.data)
            form.models.choices = [('0', '型号-All')] + [(model.id, model.name) for model in brand.models]
            if not first_search:
                if session['asset_view_search_brands'] is not None and session['asset_view_search_brands'] != form.brands.data:
                    form.models.data = '0'
        session['asset_view_search_class2'] = form.class2.data
        session['asset_view_search_class3'] = form.class3.data
        session['asset_view_search_brands'] = form.brands.data
        session['asset_view_search_models'] = form.models.data
        session['asset_view_search_code'] = form.code.data
        if class1 == 1:
            session['asset_view_search_sap_code'] = form.sap_code.data
            session['asset_view_search_used_by'] = form.used_by_id.data
            session['asset_view_search_company'] = form.companies.data
    # 搜索条件
    conditions = set()
    if class_1:
        conditions.add(BizAssetMaster.class1_id == class_1.id)
    conditions.add(BizAssetMaster.bg_id == current_user.company_id)
    conditions.add(BizAssetMaster.code.like('%' + form.code.data + '%'))
    if form.buy_s.data:
        conditions.add(BizAssetMaster.buy_date >= datetime.strptime(form.buy_s.data, '%Y-%m-%d'))
    if form.buy_e.data:
        conditions.add(BizAssetMaster.buy_date <= datetime.strptime(form.buy_e.data, '%Y-%m-%d'))
    if class1 == 1:
        conditions.add(BizAssetMaster.sap_code.like('%' + form.sap_code.data + '%'))
    if form.class2.data is not None and form.class2.data != '0':
        conditions.add(BizAssetMaster.class2_id == form.class2.data)
    if form.class3.data is not None and form.class3.data != '0':
        conditions.add(BizAssetMaster.class3_id == form.class3.data)
    if form.brands.data is not None and form.brands.data != '0':
        conditions.add(BizAssetMaster.brand_id == form.brands.data)
    if form.models.data is not None and form.models.data != '0':
        conditions.add(BizAssetMaster.model_id == form.models.data)
    if form.companies.data is not None and form.companies.data != '0':
        conditions.add(BizAssetMaster.company_id == form.companies.data)
    if form.used_by_id.data:
        conditions.add(BizAssetMaster.user_id == form.used_by_id.data)
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']
    pagination = BizAssetMaster.query.filter(*conditions).order_by(BizAssetMaster.buy_date.desc()).paginate(page, per_page)
    assets = pagination.items
    if class1 == 1:
        repair_types = get_options('D006')      # 维修类型
        repair_states = get_options('D007')     # 维修状态
        repair_parts = get_options('D011')      # 故障部位
        scrap_reasons = get_options('D008')     # 报废原因
        scrap_states = get_options('D009')      # 报废状态
        companies = BizCompany.query.order_by(BizCompany.name).all()
        vendors = [(vendor.id, vendor.name) for vendor in BizVendorMaster.query.filter(BizVendorMaster.bg_id == current_user.company_id).order_by(BizVendorMaster.name).all()]
        return render_template('biz/asset/master/index1.html', form=form, pagination=pagination, assets=assets,
                           repair_types=repair_types, repair_states=repair_states, repair_parts=repair_parts, scrap_reasons=scrap_reasons,
                           scrap_states=scrap_states, vendors=vendors, companies=companies)
    else:
        return render_template('biz/asset/master/index0.html', form=form, pagination=pagination, assets=assets)
@bp_master.route('/add/<int:class1>', methods=['GET', 'POST'])
@login_required
@log_record('新增资产主信息')
def add(class1):
    form = AssetForm()
    form.class1.data = class1
    # 资产类别一级大类代码必须是'01':资产'02':耗材
    class_1 = BizAssetClass.query.filter(BizAssetClass.code == '01', BizAssetClass.bg_id == current_user.company_id).first() if class1 == 1 else BizAssetClass.query.filter(BizAssetClass.code == '02', BizAssetClass.bg_id == current_user.company_id).first()
    companies = BizCompany.query.order_by(BizCompany.name).all()
    form.class2.choices = [('0', '资产分类-All')]
    if class_1:
        form.class2.choices += [(rel.child_class_id, rel.child_class.name) for rel in class_1.get_child_class]
    form.brands.choices = [('0', '品牌-All')]
    brands = BizBrandMaster.query.filter(BizBrandMaster.bg_id == current_user.company_id).order_by(BizBrandMaster.name).all()
    if brands:
        form.brands.choices += [(brand.id, brand.name) for brand in brands]
    form.vendors.choices = [('0', '供应商-All')]
    vendors = BizVendorMaster.query.filter(BizVendorMaster.bg_id == current_user.company_id).order_by(BizVendorMaster.name).all()
    if vendors:
        form.vendors.choices += [(vendor.id, vendor.name) for vendor in vendors]
    form.store.choices = [(store.id, store.name) for store in BizStoreMaster.query.filter(BizStoreMaster.bg_id == current_user.company_id).order_by().all()]
    if form.validate_on_submit():
        # 保存主数据
        buy_bill = BizAssetBuy.query.filter_by(buy_no=form.buy_no.data.upper()).first()
        code = gen_bill_no('AS')
        name = BizAssetClass.query.get(form.class3_id.data).name
        manager = BizEmployee.query.filter_by(code=current_user.user_id).first()
        e = get_enum_value('D003', '1')
        master = BizAssetMaster(
            id=uuid.uuid4().hex,
            bg_id=current_user.company_id,
            create_id=current_user.id,
            is_asset=class1,
            buy_bill_id=buy_bill.id,
            buy_date=datetime.strptime(form.buy_date.data, '%Y-%m-%d'),
            buy_fee=form.buy_fee.data,
            code=code,
            reg_date=datetime.today(),
            status_id=e.id if e else '',
            class1_id=class_1.id,
            class2_id=form.class2.data,
            class3_id=form.class3_id.data,
            brand_id=form.brands.data,
            model_id=form.model_id.data,
            manager_id=manager.id if manager else '',
            vendor_id=form.vendors.data,
            store_id=form.store.data
        )
        # 设置使用人
        if form.used_by_id.data:
            master.user_id = form.used_by_id.data
            used_by = BizEmployee.query.get(form.used_by_id.data)
            master.department_id = used_by.department_id
            master.company_id = used_by.company_id
        reg_amount = 1
        '''
        资产需要生成二维码和条形码，耗材只更新登记数量即可
        '''
        if class1 == 1:
            master.sap_code = form.sap_code.data
            data = "{'code'='" + code + "', 'name'='" + name + "'}"
            gen_barcode(current_app.config['BAR_CODE_PATH'], code)
            qr_path = current_app.config['QR_CODE_PATH'] + '\\' + code + '.png'
            gen_qrcode(qr_path, data)
            master.bar_path = code + '.png'
            master.qr_path = code + '.png'
        else:
            reg_amount = form.reg_amount.data
        master.reg_amount = reg_amount
        db.session.add(master)
        db.session.commit()
        print('Master save successfully, and the master id is : ', master.id)
        # 设置使用人
        if form.used_by_id.data:
            change = BizAssetChange(
                id=uuid.uuid4().hex,
                change_date=datetime.today(),
                asset_id=master.id,
                new_holder_id=form.used_by_id.data
            )
            db.session.add(change)
            db.session.commit()
        # 设置主资产
        if form.parent_asset.data:
            print('设置主资产, 主资产ID : ', form.parent_asset_id.data)
            parent = BizAssetMaster.query.get(form.parent_asset_id.data)
            master.set_parent_asset(parent)
        # 保存维保信息
        maintain = BizAssetMaint(
            id=uuid.uuid4().hex,
            start_date=datetime.strptime(form.start_date.data, '%Y-%m-%d'),
            expire_date=datetime.strptime(form.expire_date.data, '%Y-%m-%d'),
            free=True,
            vendor_id=form.vendors.data,
            master_id=master.id
        )
        db.session.add(maintain)
        db.session.commit()
        # 保存属性信息
        if class1 == 1:
            asset_property = BizAssetProperty(
                id=uuid.uuid4().hex,
                cpu=form.cpu.data,
                memory=form.memory.data,
                disk=form.disk.data,
                screen_ratio=form.screen_ratio.data,
                screen_size=form.screen_size.data,
                inf=form.inf.data,
                system_os=form.system_os.data,
                serial_no=form.serial_no.data,
                mac=form.mac.data,
                battery=form.battery.data,
                power=form.power.data,
                remark=form.remark.data,
                asset_master_id=master.id
            )
            db.session.add(asset_property)
            db.session.commit()
        # 生成入库审批单
        audit_line = AuditLine.query.filter_by(code='T001').first()
        e = get_enum_value('D004', '1')
        bill_in_no = gen_bill_no('IN')
        bill_in = BizStockIn(
            id=uuid.uuid4().hex,
            bg_id=current_user.company_id,
            in_no=bill_in_no,
            in_date=datetime.today(),
            audit_line_id=audit_line.id,
            charger_id=current_user.id,
            state_id=e.id if e else ''
        )
        db.session.add(bill_in)
        db.session.commit()
        # 更新资产主数据对应的入库单
        master.in_bill_id = bill_in.id
        db.session.commit()
        # 记录出入库履历
        io_history = BizStockHistory(
            id=uuid.uuid4().hex,
            bg_id=current_user.company_id,
            bill_no=bill_in_no,
            asset_id=master.id,
            class1_id=class_1.id,
            class2_id=form.class2.data,
            class3_id=form.class3_id.data,
            brand_id=form.brands.data,
            model_id=form.model_id.data,
            io_type=1,
            amount=reg_amount,
            code=master.code,
            sap_code=master.code
        )
        # 出入库类型 - 登记入库
        e = get_enum_value('D010', '1')
        if e:
            io_history.io_class_id = e.id
        db.session.add(io_history)
        db.session.commit()
        # 更新库存余额表
        conditions = set()
        conditions.add(BizStockAmount.class1_id == class_1.id)
        conditions.add(BizStockAmount.class2_id == form.class2.data)
        conditions.add(BizStockAmount.class3_id == form.class3_id.data)
        conditions.add(BizStockAmount.brand_id == form.brands.data)
        conditions.add(BizStockAmount.model_id == form.model_id.data)
        conditions.add(BizStockAmount.bg_id == current_user.company_id)
        stock_amount = BizStockAmount.query.filter(*conditions).first()
        # 找到则更新，否则新增
        if stock_amount:
            stock_amount.amount += reg_amount
            stock_amount.update_id = current_user.id
            stock_amount.updatetime_utc = datetime.utcfromtimestamp(time.time())
            stock_amount.updatetime_loc = datetime.fromtimestamp(time.time())
        else:
            stock_amount = BizStockAmount(
                id=uuid.uuid4().hex,
                bg_id=current_user.company_id,
                class1_id=class_1.id,
                class2_id=form.class2.data,
                class3_id=form.class3_id.data,
                brand_id=form.brands.data,
                model_id=form.model_id.data,
                amount=reg_amount
            )
            db.session.add(stock_amount)
        db.session.commit()
        # 写入待审批
        audit_item = AuditItem(
            id=uuid.uuid4().hex,
            bg_id=current_user.company_id,
            audit_line_id=audit_line.id,
            bill_no=bill_in_no,
            bill_type='SI',
            audit_level=1
        )
        db.session.add(audit_item)
        db.session.commit()
        # 发送邮件提醒
        rel = RelAuditLineRole.query.filter(RelAuditLineRole.audit_line_id == audit_line.id, RelAuditLineRole.audit_grade == 1).first()
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
                send_mail(subject='资产登记审批提醒', to=to, cc=[], template='emails/asset_approve_remind', asset=master)
        flash('资产信息新增成功！')
        return redirect(url_for('.index', class1=class1))
    return render_template('biz/asset/master/add.html', form=form, companies=companies)
@bp_master.route('/generate_bar/<id>', methods=['POST'])
@login_required
@log_record('重新生成条码')
def generate_bar(id):
    asset = BizAssetMaster.query.get(id)
    code = asset.code
    name = BizAssetClass.query.get(asset.class3_id).name
    data = "{'code'='" + code + "', 'name'='" + name + "'}"
    gen_barcode(current_app.config['BAR_CODE_PATH'], code)
    qr_path = current_app.config['QR_CODE_PATH'] + '\\' + code + '.png'
    gen_qrcode(qr_path, data)
    asset.bar_path = code + '.png'
    asset.qr_path = code + '.png'
    asset.update_id = current_user.id
    asset.updatetime_utc = datetime.utcfromtimestamp(time.time())
    asset.updatetime_loc = datetime.fromtimestamp(time.time())
    db.session.commit()
    return jsonify(code=asset.code, message='重新生成条码成功！')
@bp_master.route('/edit/<id>/<int:class1>', methods=['GET', 'POST'])
@login_required
@log_record('修改资产主数据信息')
def edit(id, class1):
    asset = BizAssetMaster.query.get(id)
    maintain = BizAssetMaint.query.with_parent(asset).order_by(BizAssetMaint.createtime_loc.desc()).first()
    form = AssetForm()
    form.id.data = id
    form.class1.data = class1
    # 资产类别一级大类代码必须是'01':资产'02':耗材
    class_1 = BizAssetClass.query.filter(BizAssetClass.code == '01', BizAssetClass.bg_id == current_user.company_id).first() if class1 == 1 else BizAssetClass.query.filter(BizAssetClass.code == '02', BizAssetClass.bg_id == current_user.company_id).first()
    companies = BizCompany.query.order_by(BizCompany.name).all()
    form.class2.choices = [('0', '资产分类-All')] + [(rel.child_class_id, rel.child_class.name) for rel in class_1.get_child_class]
    form.brands.choices = [('0', '品牌-All')] + [(brand.id, brand.name) for brand in BizBrandMaster.query.filter(BizBrandMaster.bg_id == current_user.company_id).order_by(BizBrandMaster.name).all()]
    form.vendors.choices = [('0', '供应商-All')] + [(vendor.id, vendor.name) for vendor in BizVendorMaster.query.filter(BizVendorMaster.bg_id == current_user.company_id).order_by(BizVendorMaster.name).all()]
    form.store.choices = [(store.id, store.name) for store in BizStoreMaster.query.filter(BizStoreMaster.bg_id == current_user.company_id).order_by().all()]
    if request.method == 'GET':
        form.class2.data = asset.class2_id
        form.class3_id.data = asset.class3_id
        form.brands.data = asset.brand_id
        form.model_id.data = asset.model_id
        form.vendors.data = asset.vendor_id
        form.start_date.data = maintain.start_date.strftime('%Y-%m-%d')
        form.expire_date.data = maintain.expire_date.strftime('%Y-%m-%d')
        form.store.data = asset.store_id
        form.buy_no.data = asset.buy_bill.buy_no
        form.buy_date.data = asset.buy_date.strftime('%Y-%m-%d')
        form.buy_fee.data = asset.buy_fee
        form.code.data = asset.code
        form.sap_code.data = asset.sap_code
        form.reg_amount.data = asset.reg_amount
        if asset.user:
            form.used_by.data = asset.user.name+'('+asset.user.code+')'
            form.used_by_id.data = asset.user.id
        parent = asset.get_parent_asset
        if parent:
            form.parent_asset.data = parent.class3.name+'('+parent.code+')'
            form.parent_asset_id.data = parent.id
        form.contact_person.data = asset.vendor.contact_person
        form.contact_phone.data = asset.vendor.contact_phone
        asset_property = asset.properties
        if asset_property:
            form.cpu.data = asset_property.cpu
            form.memory.data = asset_property.memory
            form.disk.data = asset_property.disk
            form.screen_ratio.data = asset_property.screen_ratio
            form.screen_size.data = asset_property.screen_size
            form.inf.data = asset_property.inf
            form.system_os.data = asset_property.system_os
            form.serial_no.data = asset_property.serial_no
            form.mac.data = asset_property.mac
            form.battery.data = asset_property.battery
            form.power.data = asset_property.power
            form.remark.data = asset_property.remark
    if form.validate_on_submit():
        '''
        先更新出入库履历&库存余额再保存主数据
        '''
        reg_amount = 1  # 登记数量：资产默认为1，耗材以表单为准
        if class1 == 0:
            reg_amount = form.reg_amount.data
        '''           
            查询条件：
                资产ID&入库单号找到对应的唯一出入库记录
            更新出入库履历逻辑：
                只更新耗材入库履历即可，资产数量固定为1，无需修改，耗材数量有可能调整，以调整后的为准
                满足出入库履历存在/类型是耗材/修改的登记数量和老的登记数量不相等的情况下执行更新    
        '''
        stock_history = BizStockHistory.query.filter(BizStockHistory.bill_no == asset.in_bill.in_no, BizStockHistory.asset_id == id).first()
        if stock_history and class1 == 0 and asset.reg_amount != form.reg_amount.data:
            stock_history.amount = reg_amount
            stock_history.update_id = current_user.id
            stock_history.updatetime_utc = datetime.utcfromtimestamp(time.time())
            stock_history.updatetime_loc = datetime.fromtimestamp(time.time())
            db.session.commit()
        '''        
        更新条件：资产类别/名称/品牌/型号/登记数量 任一项目发生变化均更新数量
        更新逻辑：旧的库存余额减少，新的库存余额增加
        '''
        # 更新库存余额
        if asset.class2_id != form.class2.data or asset.class3_id != form.class3_id or asset.brand_id != form.brands.data or asset.model_id != form.model_id.data or asset.reg_amount != form.reg_amount.data:
            # 旧的库存余额先减掉
            conditions = set()
            conditions.add(BizStockAmount.class1_id == asset.class1_id)
            conditions.add(BizStockAmount.class2_id == asset.class2_id)
            conditions.add(BizStockAmount.class3_id == asset.class3_id)
            conditions.add(BizStockAmount.brand_id == asset.brand_id)
            conditions.add(BizStockAmount.model_id == asset.model_id)
            conditions.add(BizStockAmount.bg_id == current_user.company_id)
            old_stock_amount = BizStockAmount.query.filter(*conditions).first()
            if old_stock_amount:
                old_stock_amount.amount -= asset.reg_amount
                old_stock_amount.update_id = current_user.id
                old_stock_amount.updatetime_utc = datetime.utcfromtimestamp(time.time())
                old_stock_amount.updatetime_loc = datetime.fromtimestamp(time.time())
                db.session.commit()
            conditions.clear()
            # 新的库存余额
            conditions.add(BizStockAmount.class1_id == class_1.id)
            conditions.add(BizStockAmount.class2_id == form.class2.data)
            conditions.add(BizStockAmount.class3_id == form.class3_id.data)
            conditions.add(BizStockAmount.brand_id == form.brands.data)
            conditions.add(BizStockAmount.model_id == form.model_id.data)
            conditions.add(BizStockAmount.bg_id == current_user.company_id)
            new_stock_amount = BizStockAmount.query.filter(*conditions).first()
            # 找到则更新，否则新增
            if new_stock_amount:
                new_stock_amount.amount += reg_amount
                new_stock_amount.update_id = current_user.id
                new_stock_amount.updatetime_utc = datetime.utcfromtimestamp(time.time())
                new_stock_amount.updatetime_loc = datetime.fromtimestamp(time.time())
            else:
                new_stock_amount = BizStockAmount(
                    id=uuid.uuid4().hex,
                    bg_id=current_user.company_id,
                    class1_id=class_1.id,
                    class2_id=form.class2.data,
                    class3_id=form.class3_id.data,
                    brand_id=form.brands.data,
                    model_id=form.model_id.data,
                    amount=reg_amount
                )
                db.session.add(new_stock_amount)
            db.session.commit()
        # 保存主数据
        buy_bill = BizAssetBuy.query.filter_by(buy_no=form.buy_no.data.upper()).first()
        manager = BizEmployee.query.filter_by(code=current_user.user_id).first()
        asset.update_id = current_user.id
        asset.updatetime_utc = datetime.utcfromtimestamp(time.time())
        asset.updatetime_loc = datetime.fromtimestamp(time.time())
        asset.buy_bill_id = buy_bill.id
        asset.buy_date = datetime.strptime(form.buy_date.data, '%Y-%m-%d')
        asset.buy_fee = form.buy_fee.data
        asset.class1_id = class_1.id
        asset.class2_id = form.class2.data
        asset.class3_id = form.class3_id.data
        asset.brand_id = form.brands.data
        asset.model_id = form.model_id.data
        asset.manager_id = manager.id if manager else ''
        asset.vendor_id = form.vendors.data
        asset.store_id = form.store.data
        # 设置使用人
        old_user_id = asset.user_id if asset.user_id else ''
        if form.used_by_id.data:
            asset.user_id = form.used_by_id.data
            used_by = BizEmployee.query.get(form.used_by_id.data)
            asset.department_id = used_by.department_id
            asset.company_id = used_by.company_id
        db.session.commit()
        # 如果使用人改变了，新增资产变更履历
        if form.used_by_id.data != old_user_id and old_user_id:
            change = BizAssetChange(
                id=uuid.uuid4().hex,
                change_date=datetime.today(),
                asset_id=id,
                old_holder_id=old_user_id,
                new_holder_id=form.used_by_id.data
            )
            db.session.add(change)
            db.session.commit()
        # 保存维保信息
        maintain.start_date = datetime.strptime(form.start_date.data, '%Y-%m-%d')
        maintain.expire_date = datetime.strptime(form.expire_date.data, '%Y-%m-%d')
        maintain.update_id = current_user.id
        maintain.updatetime_utc = datetime.utcfromtimestamp(time.time())
        maintain.updatetime_loc = datetime.fromtimestamp(time.time())
        db.session.commit()
        # 保存属性信息
        if class1 == 1:
            asset_property = asset.properties
            asset_property.cpu = form.cpu.data
            asset_property.memory = form.memory.data
            asset_property.disk = form.disk.data
            asset_property.screen_ratio = form.screen_ratio.data
            asset_property.screen_size = form.screen_size.data
            asset_property.inf = form.inf.data
            asset_property.system_os = form.system_os.data
            asset_property.serial_no = form.serial_no.data
            asset_property.mac = form.mac.data
            asset_property.battery = form.battery.data
            asset_property.power = form.power.data
            asset_property.remark = form.remark.data
        db.session.commit()
        flash('资产信息修改成功！')
        # return redirect(url_for('.index', class1=class1))
        return redirect(url_for('.edit', id=id, class1=class1))
    return render_template('biz/asset/master/edit.html', form=form, companies=companies)
@bp_master.route('/repair', methods=['POST'])
@login_required
@log_record('资产维修申请')
def repair():
    data = request.get_json()
    asset_id = data['asset_id']
    repair_id = data['repair_id']
    repair_type_id = data['repair_type_id']
    repair_state_id = data['repair_state_id']
    pre_finish_date = data['pre_finish_date']
    rel_finish_date = data['rel_finish_date']
    out_date = data['out_date']
    pre_in_date = data['pre_in_date']
    real_in_date = data['real_in_date']
    fee = data['fee']
    request_draft = data['request_draft']
    request_accept_dt = data['request_accept_dt']
    requested_by_id = data['requested_by_id']
    repair_draft = data['repair_draft']
    repair_handler_id = data['repair_handler_id']
    repair_part_id = data['repair_part_id']
    repair_content = data['repair_content']
    action = data['action']
    if action == 'A':
        repair_no = gen_bill_no('AR')
        asset_repair = BizAssetRepair(
            id=uuid.uuid4().hex,
            bg_id=current_user.company_id,
            asset_id=asset_id,
            repair_no=repair_no,
            repair_type_id=repair_type_id,
            repair_state_id=repair_state_id,
            request_draft=request_draft,
            request_accept_dt=datetime.strptime(request_accept_dt, '%Y-%m-%d'),
            requested_by_id=requested_by_id,
            repair_draft=repair_draft,
            repair_handler_id=repair_handler_id,
            repair_part_id=repair_part_id,
            repair_content=repair_content,
            fee=fee
        )
        if pre_finish_date:
            asset_repair.pre_finish_date = datetime.strptime(pre_finish_date, '%Y-%m-%d')
        if out_date:
            asset_repair.out_date = datetime.strptime(out_date, '%Y-%m-%d')
        if pre_in_date:
            asset_repair.pre_in_date = datetime.strptime(pre_in_date, '%Y-%m-%d')
        if rel_finish_date:
            asset_repair.rel_finish_date = datetime.strptime(rel_finish_date, '%Y-%m-%d')
        if real_in_date:
            asset_repair.real_in_date = datetime.strptime(real_in_date, '%Y-%m-%d')
        db.session.add(asset_repair)
        message = '资产维修申请成功(维修单号:{})!'.format(repair_no)
    else:
        asset_repair = BizAssetRepair.query.get(repair_id)
        asset_repair.repair_type_id = repair_type_id
        asset_repair.repair_state_id = repair_state_id
        asset_repair.request_draft = request_draft
        asset_repair.request_accept_dt = datetime.strptime(request_accept_dt, '%Y-%m-%d')
        asset_repair.requested_by_id = requested_by_id
        asset_repair.repair_draft = repair_draft
        asset_repair.repair_handler_id = repair_handler_id
        asset_repair.fee = fee
        asset_repair.repair_part_id = repair_part_id
        asset_repair.repair_content = repair_content
        if pre_finish_date:
            asset_repair.pre_finish_date = datetime.strptime(pre_finish_date, '%Y-%m-%d')
        if out_date:
            asset_repair.out_date = datetime.strptime(out_date, '%Y-%m-%d')
        if pre_in_date:
            asset_repair.pre_in_date = datetime.strptime(pre_in_date, '%Y-%m-%d')
        if rel_finish_date:
            asset_repair.rel_finish_date = datetime.strptime(rel_finish_date, '%Y-%m-%d')
        if real_in_date:
            asset_repair.real_in_date = datetime.strptime(real_in_date, '%Y-%m-%d')
        asset_repair.update_id = current_user.id
        asset_repair.updatetime_utc = datetime.utcfromtimestamp(time.time())
        asset_repair.updatetime_loc = datetime.fromtimestamp(time.time())
        message = '资产维修修改成功!'
    db.session.commit()
    # 更新资产状态
    asset = BizAssetMaster.query.get(asset_id)
    repair_state = SysEnum.query.get(repair_state_id)
    if repair_state.item == '1':
        code = '5'
    if repair_state.item == '2':
        code = '6'
    if repair_state.item == '3':
        code = '7'
    e = get_enum_value('D003', code)
    if e:
        asset.status_id = e.id
    db.session.commit()
    return jsonify(code=1, message=message)
@bp_master.route('/scrap', methods=['POST'])
@login_required
@log_record('资产报废')
def scrap():
    data = request.get_json()
    asset_id = data['asset_id']
    scrap_id = data['scrap_id']
    scrap_reason_id = data['scrap_reason_id']
    scrap_state_id = data['scrap_state_id']
    scrap_date = data['scrap_date']
    finish_date = data['finish_date']
    scrap_draft = data['scrap_draft']
    sap_scrap = data['sap_scrap']
    action = data['action']
    if action == 'A':
        scrap_no = gen_bill_no('AS')
        asset_scrap = BizAssetScrap(
            id=uuid.uuid4().hex,
            bg_id=current_user.company_id,
            asset_id=asset_id,
            scrap_no=scrap_no,
            scrap_reason_id=scrap_reason_id,
            scrap_state_id=scrap_state_id,
            scrap_date=datetime.strptime(scrap_date, '%Y-%m-%d'),
            scrap_draft=scrap_draft,
            sap_scrap=True if sap_scrap else False
        )
        if finish_date:
            asset_scrap.finish_date = datetime.strptime(finish_date, '%Y-%m-%d')
            asset_scrap.scraper_id = current_user.id
        db.session.add(asset_scrap)
        message = '资产报废操作成功完成(报废单号:{})!'.format(scrap_no)
    else:
        asset_scrap = BizAssetScrap.query.get(scrap_id)
        asset_scrap.scrap_reason_id = scrap_reason_id
        asset_scrap.scrap_state_id = scrap_state_id
        asset_scrap.scrap_date = datetime.strptime(scrap_date, '%Y-%m-%d')
        asset_scrap.scrap_draft = scrap_draft
        asset_scrap.sap_scrap = True if sap_scrap else False
        if finish_date:
            asset_scrap.finish_date = datetime.strptime(finish_date, '%Y-%m-%d')
            asset_scrap.scraper_id = current_user.id
        asset_scrap.update_id = current_user.id
        asset_scrap.updatetime_utc = datetime.utcfromtimestamp(time.time())
        asset_scrap.updatetime_loc = datetime.fromtimestamp(time.time())
        message = '资产报废信息修改成功!'
    db.session.commit()
    # 更新资产状态
    asset = BizAssetMaster.query.get(asset_id)
    scrap_state = SysEnum.query.get(scrap_state_id)
    if scrap_state.item == '1':
        code = '8'
    if scrap_state.item == '2':
        code = '9'
        # 如果是报废完成，资产库存状态变更为"已出库"
        asset.is_out = True
    e = get_enum_value('D003', code)
    if e:
        asset.status_id = e.id
    db.session.commit()
    # 如果报废状态为报废完成，则更新库存余额：库存减一
    scrap_state = SysEnum.query.get(scrap_state_id)
    if scrap_state.item == '2':
        asset = BizAssetMaster.query.get(asset_id)
        conditions = set()
        conditions.add(BizStockAmount.class1_id == asset.class1_id)
        conditions.add(BizStockAmount.class2_id == asset.class2_id)
        conditions.add(BizStockAmount.class3_id == asset.class3_id)
        conditions.add(BizStockAmount.brand_id == asset.brand_id)
        conditions.add(BizStockAmount.model_id == asset.model_id)
        conditions.add(BizStockAmount.bg_id == current_user.company_id)
        stock_amount = BizStockAmount.query.filter(*conditions).first()
        if stock_amount:
            stock_amount.amount -= 1
            stock_amount.update_id = current_user.id
            stock_amount.updatetime_utc = datetime.utcfromtimestamp(time.time())
            stock_amount.updatetime_loc = datetime.fromtimestamp(time.time())
    db.session.commit()
    return jsonify(code=1, message=message)
@bp_master.route('/reinsurance', methods=['POST'])
@login_required
@log_record('资产续保')
def reinsurance():
    data = request.get_json()
    asset_id = data['asset_id']
    vendor_id = data['vendor_id']
    start_date = data['start_date']
    expire_date = data['expire_date']
    content = data['content']
    draft_no = data['draft_no']
    price = data['price']
    # 更新以往维保信息check为False
    asset = BizAssetMaster.query.get(asset_id)
    for maintain in asset.maintains:
        maintain.check = False
        db.session.commit()
    maintain = BizAssetMaint(
        id=uuid.uuid4().hex,
        start_date=datetime.strptime(start_date, '%Y-%m-%d'),
        expire_date=datetime.strptime(expire_date, '%Y-%m-%d'),
        content=content,
        draft_no=draft_no,
        price=price,
        vendor_id=vendor_id,
        master_id=asset_id
    )
    db.session.add(maintain)
    db.session.commit()
    # 更新资产维保供应商信息
    asset.vendor_id = vendor_id
    db.session.commit()
    return jsonify(code=1, message='资产续保操作成功完成!')
@bp_master.route('/check_user/<asset_id>', methods=['POST'])
@login_required
@log_record('检索资产使用者信息')
def check_user(asset_id):
    master = BizAssetMaster.query.get(asset_id)
    used_by = master.user
    return jsonify(code=1, employee=dict(id=used_by.id if used_by else '0', code=used_by.code if used_by else '0', name=used_by.name if used_by else '0'))
    # if used_by:
    #     return jsonify(code=1, employee=dict(id=used_by.id, code=used_by.code, name=used_by.name))
    # return jsonify(code=0, message='当前资产无使用者,无法进行资产变更!')
@bp_master.route('/change_user', methods=['POST'])
@login_required
@log_record('资产变更')
def change_user():
    data = request.get_json()
    asset_id = data['asset_id']
    pre_user = data['pre_user']
    new_user = data['new_user']
    change = BizAssetChange(
        id=uuid.uuid4().hex,
        change_date=datetime.today(),
        asset_id=asset_id,
        new_holder_id=new_user
    )
    if pre_user != '0':
        change.old_holder_id = pre_user
    db.session.add(change)
    db.session.commit()
    # 更改资产使用者信息
    asset = BizAssetMaster.query.get(asset_id)
    asset.is_new = False
    asset.user_id = new_user
    used_by = BizEmployee.query.get(new_user)
    asset.department_id = used_by.department_id
    asset.company_id = used_by.company_id
    db.session.commit()
    return jsonify(code=1, message='资产变更操作成功完成!')
@bp_master.route('/change_list/<asset_id>', methods=['POST'])
@login_required
@log_record('资产变更履历')
def change_list(asset_id):
    asset = BizAssetMaster.query.get(asset_id)
    change_list = BizAssetChange.query.with_parent(asset).order_by(BizAssetChange.createtime_loc.desc()).all()
    return jsonify(list=[(i+1, change.new_holder.name if change.new_holder else '-', change.old_holder.name if change.old_holder else '-', change.change_date.strftime('%Y-%m-%d') if  change.change_date else '-') for i, change in enumerate(change_list)])
@bp_master.route('/get_stores/<asset_id>', methods=['POST'])
@login_required
@log_record('获取资产返回仓库信息')
def get_stores(asset_id):
    asset = BizAssetMaster.query.get(asset_id)
    stores = BizStoreMaster.query.filter_by(bg_id = current_user.company_id).order_by(BizStoreMaster.name).all()
    return jsonify(stores=[(store.id, store.name) for store in stores], store_id=asset.store_id)
@bp_master.route('/restore/<asset_id>', methods=['POST'])
@login_required
@log_record('资产返回操作')
def restore(asset_id):
    data = request.get_json()
    amount = data['amount']
    store = data['store']
    try:
        amount = int(amount)
    except:
        return jsonify(code=0, message='返还数量不是整数!')
    asset = BizAssetMaster.query.get(asset_id)
    # 更改资产状态&库存状态栏位信息
    asset.is_new = False                # 设置为二手
    asset.is_out = False                # 库存状态设置为在库
    e = get_enum_value('D003', '1')
    asset.status_id = e.id              # 资产状态设置为在库
    asset.store_id = store              # 设置仓库
    # 清空使用人信息
    if asset.is_asset:
        company = BizCompany.query.get(asset.company_id)
        department = BizDepartment.query.get(asset.department_id)
        user = BizEmployee.query.get(asset.user_id)
        company.biz_assets.remove(asset)
        department.assets.remove(asset)
        user.used_assets.remove(asset)
    db.session.commit()
    # 新增入库履历
    io_history = BizStockHistory(
        id=uuid.uuid4().hex,
        bg_id=current_user.company_id,
        asset_id=asset.id,
        class1_id=asset.class1_id,
        class2_id=asset.class2_id,
        class3_id=asset.class3_id,
        brand_id=asset.brand_id,
        model_id=asset.model_id,
        io_type=1,
        amount=amount,
        code=asset.code,
        sap_code=asset.sap_code
    )
    if data['reason']:
        io_history.remark = data['reason']
    # 出入库类型 - 返还入库
    e = get_enum_value('D010', '2')
    if e:
        io_history.io_class_id = e.id
    db.session.add(io_history)
    db.session.commit()
    # 更新库存余额
    conditions = set()
    conditions.add(BizStockAmount.class1_id == asset.class1_id)
    conditions.add(BizStockAmount.class2_id == asset.class2_id)
    conditions.add(BizStockAmount.class3_id == asset.class3_id)
    conditions.add(BizStockAmount.brand_id == asset.brand_id)
    conditions.add(BizStockAmount.model_id == asset.model_id)
    conditions.add(BizStockAmount.bg_id == current_user.company_id)
    stock_amount = BizStockAmount.query.filter(*conditions).first()
    if stock_amount:
        stock_amount.amount += amount
        stock_amount.update_id = current_user.id
        stock_amount.updatetime_utc = datetime.utcfromtimestamp(time.time())
        stock_amount.updatetime_loc = datetime.fromtimestamp(time.time())
    db.session.commit()
    return jsonify(code=1, message='资产返还操作成功完成!')
@bp_master.route('/get_bar_image/<int:bar_type>/<path:filename>')
def get_bar_image(bar_type, filename):
    directory = current_app.config['BAR_CODE_PATH'] if bar_type == 1 else current_app.config['QR_CODE_PATH']
    return send_from_directory(directory, filename)
def get_stock_amount(asset):
    conditions = set()
    conditions.add(BizStockAmount.class1_id == asset.class1_id)
    conditions.add(BizStockAmount.class2_id == asset.class2_id)
    conditions.add(BizStockAmount.class3_id == asset.class3_id)
    conditions.add(BizStockAmount.brand_id == asset.brand_id)
    conditions.add(BizStockAmount.model_id == asset.model_id)
    conditions.add(BizStockAmount.bg_id == current_user.company_id)
    stock_amount = BizStockAmount.query.filter(*conditions).first()
    return stock_amount
@bp_master.route('/sign/<asset_id>', methods=['GET', 'POST'])
def sign(asset_id):
    form = AssetSignForm()
    form.id.data = asset_id
    asset = BizAssetMaster.query.get(asset_id)
    if form.validate_on_submit():
        e = get_enum_value('D003', '3')
        if e:
            asset.status_id = e.id
            db.session.commit()
        flash('接收确认成功，您可以关闭此画面了！')
    return render_template('biz/asset/master/_sign.html', form=form, asset=asset)
@bp_master.route('/template')
@log_record('下载资产信息导入模板')
def template():
    directory = current_app.config['FILE_UPLOAD_PATH']
    template_path = os.path.join(directory, 'excel_templates')
    print('Template path is : ', template_path)
    return send_from_directory(template_path, 'assetstemplate.xlsx')
@bp_master.route('/transport', methods=['GET', 'POST'])
@login_required
@log_record('导入资产信息')
def transport():
    if 'file' not in request.files:
        return jsonify(code=0, message='导入失败,文件未读取！')
    else:
        file = request.files.get('file')
        file_name = file.filename
        file_path = os.path.join(current_app.config['FILE_UPLOAD_PATH'], file_name)
        # 执行上传
        file.save(file_path)
        # 执行解析
        ex_file = xlrd2.open_workbook(file_path)
        sheet = ex_file.sheet_by_index(0)
        rows = sheet.nrows
        items = []
        AssetMaster = namedtuple('AssetMaster', ['class1_cd',
                                                 'class2_cd',
                                                 'class3_cd',
                                                 'asset_cd',
                                                 'asset_sap_cd',
                                                 'status',
                                                 'brand_cd',
                                                 'model_cd',
                                                 'user_cd',
                                                 'amount',
                                                 'buy_no',
                                                 'buy_dt',
                                                 'store_cd',
                                                 'vendor_cd',
                                                 'insurance_start_dt',
                                                 'insurance_expire_dt',
                                                 'pro_os',
                                                 'pro_cpu',
                                                 'pro_mem',
                                                 'pro_disk',
                                                 'pro_screen_ratio',
                                                 'pro_screen_size',
                                                 'pro_serial_no',
                                                 'pro_inf',
                                                 'pro_mac',
                                                 'pro_battery',
                                                 'pro_power',
                                                 'pro_remark'
                                                 ])
        for i in range(1, rows):
            values = sheet.row_values(i)
            items.append(AssetMaster(*values))
        # 执行校验
        errors = []
        class1 = {clazz.code: clazz.id for clazz in BizAssetClass.query.all() if clazz.grade == 1}
        class2 = {clazz.code: clazz.id for clazz in BizAssetClass.query.all() if clazz.grade == 2}
        class3 = {clazz.code: clazz.id for clazz in BizAssetClass.query.all() if clazz.grade == 3}
        brands = {}
        models = {}
        for brand in BizBrandMaster.query.all():
            brands[brand.code] = brand.id
            for model in BizBrandModel.query.with_parent(brand).all():
                models[brand.code+'-'+model.code] = model.id
        employees = {employee.code: employee.id for employee in BizEmployee.query.all()}
        stores = {store.code: store.id for store in BizStoreMaster.query.all()}
        vendors = {vendor.code: vendor.id for vendor in BizVendorMaster.query.all()}
        buy_bills = {buy.buy_no: buy.id for buy in BizAssetBuy.query.all()}
        s_dict = SysDict.query.filter_by(code='D003').first()
        s_status = [e.item for e in SysEnum.query.with_parent(s_dict).all()]
        print('==============================', s_status)
        for index, item in enumerate(items):
            # print('Index is : ', index, ', Item is : ', item)
            print('Status is : ', str(int(item.status)))
            check_result = []
            if item.class1_cd.strip() not in class1:
                check_result.append('一级分类代码不存在')
            if item.class2_cd.strip() not in class2:
                check_result.append('二级分类代码不存在')
            if item.class3_cd.strip() not in class3:
                check_result.append('三级分类代码不存在')
            if str(int(item.status)) not in s_status:
                check_result.append('资产状态代码不存在')
            if item.brand_cd.strip() not in brands:
                check_result.append('品牌代码不存在')
            if item.brand_cd.strip()+'-'+(str(int(item.model_cd)).strip() if isinstance(item.model_cd, float) else item.model_cd) not in models:
                check_result.append('型号代码不存在')
            if item.user_cd and item.user_cd.strip().lower() not in employees:
                check_result.append('使用者职号不存在')
            if item.store_cd.strip() not in stores:
                check_result.append('仓库代码不存在')
            if item.vendor_cd.strip() not in vendors:
                check_result.append('供应商代码不存在')
            if item.buy_no.strip() not in buy_bills:
                check_result.append('购买单号不存在')
            if check_result:
                errors.append('<h6>第{}行:{}</h6>'.format(index+2, ';'.join(check_result)))
        if errors:
            return jsonify(code=0, result='<hr>'.join(errors))
        # 执行导入
        # 生成入库单
        audit_line = AuditLine.query.filter_by(code='T001').first()
        e = get_enum_value('D004', '1')
        bill_in_no = gen_bill_no('IN')
        bill_in = BizStockIn(
            id=uuid.uuid4().hex,
            bg_id=current_user.company_id,
            in_no=bill_in_no,
            in_date=datetime.today(),
            audit_line_id=audit_line.id,
            charger_id=current_user.id,
            state_id=e.id if e else ''
        )
        db.session.add(bill_in)
        db.session.commit()
        for item in items:
            print('Class1 code is : ', item.class1_cd.strip())
            class_1 = 1 if item.class1_cd.strip() == '01' else 0
            reg_amount = int(item.amount)
            class1_id = class1[item.class1_cd.strip()]
            class2_id = class2[item.class2_cd.strip()]
            class3_id = class3[item.class3_cd.strip()]
            brand_id = brands[item.brand_cd.strip()]
            model_id = models[item.brand_cd.strip()+'-'+(str(int(item.model_cd)).strip() if isinstance(item.model_cd, float) else item.model_cd)]
            buy_bill_id = buy_bills[item.buy_no.upper()]
            code = (str(int(item.asset_cd)) if isinstance(item.asset_cd, float) else item.asset_cd.strip()) if item.asset_cd else gen_bill_no('AS')
            name = BizAssetClass.query.get(class3[item.class3_cd]).name
            manager = BizEmployee.query.filter_by(code=current_user.user_id).first()
            e = get_enum_value('D003', str(int(item.status)))
            master = BizAssetMaster(
                id=uuid.uuid4().hex,
                bg_id=current_user.company_id,
                create_id=current_user.id,
                is_asset=class_1,
                buy_bill_id=buy_bill_id,
                buy_date=datetime.strptime(item.buy_dt.strip(), '%Y-%m-%d'),
                code=code,
                reg_date=datetime.today(),
                status_id=e.id if e else '',
                class1_id=class1_id,
                class2_id=class2_id,
                class3_id=class3_id,
                brand_id=brand_id,
                model_id=model_id,
                manager_id=manager.id if manager else '',
                vendor_id=vendors[item.vendor_cd.strip()],
                store_id=stores[item.store_cd.strip()],
                in_bill_id=bill_in.id,
                reg_amount=reg_amount
            )
            # 设置在库状态
            if str(int(item.status)) != '1':
                master.is_out = True
            # 设置使用人
            if item.user_cd:
                master.user_id = employees[item.user_cd.strip().lower()]
                used_by = BizEmployee.query.get(employees[item.user_cd.strip().lower()])
                master.department_id = used_by.department_id
                master.company_id = used_by.company_id
            '''
            资产需要生成二维码和条形码，耗材只更新登记数量即可
            '''
            if class_1 == 1:
                master.sap_code = item.asset_sap_cd if item.asset_sap_cd else ''
                data = "{'code'='" + code + "', 'name'='" + name + "'}"
                gen_barcode(current_app.config['BAR_CODE_PATH'], code)
                qr_path = current_app.config['QR_CODE_PATH'] + '\\' + code + '.png'
                gen_qrcode(qr_path, data)
                master.bar_path = code + '.png'
                master.qr_path = code + '.png'
            db.session.add(master)
            db.session.commit()
            print('Master save successfully, and the master id is : ', master.id)
            # 设置使用人
            if item.user_cd:
                change = BizAssetChange(
                    id=uuid.uuid4().hex,
                    change_date=datetime.today(),
                    asset_id=master.id,
                    new_holder_id=used_by.id
                )
                db.session.add(change)
                db.session.commit()
            # 保存维保信息
            maintain = BizAssetMaint(
                id=uuid.uuid4().hex,
                start_date=datetime.strptime(item.insurance_start_dt.strip(), '%Y-%m-%d'),
                expire_date=datetime.strptime(item.insurance_expire_dt.strip(), '%Y-%m-%d'),
                free=True,
                vendor_id=vendors[item.vendor_cd.strip()],
                master_id=master.id
            )
            db.session.add(maintain)
            db.session.commit()
            # 保存属性信息
            if class_1 == 1:
                asset_property = BizAssetProperty(
                    id=uuid.uuid4().hex,
                    cpu=(str(int(item.pro_cpu)).strip() if isinstance(item.pro_cpu, float) else item.pro_cpu.strip()) if item.pro_cpu else '',
                    memory=(str(int(item.pro_mem)).strip() if isinstance(item.pro_mem, float) else item.pro_mem.strip()) if item.pro_mem else '',
                    disk=(str(int(item.pro_disk)).strip() if isinstance(item.pro_disk, float) else item.pro_disk.strip()) if item.pro_disk else '',
                    screen_ratio=(str(int(item.pro_screen_ratio)).strip() if isinstance(item.pro_screen_ratio, float) else item.pro_screen_ratio.strip()) if item.pro_screen_ratio else '',
                    screen_size=(str(int(item.pro_screen_size)).strip() if isinstance(item.pro_screen_size, float) else item.pro_screen_size.strip()) if item.pro_screen_size else '',
                    inf=(str(int(item.pro_inf)).strip() if isinstance(item.pro_inf, float) else item.pro_inf.strip()) if item.pro_inf else '',
                    system_os=(str(int(item.pro_os)).strip() if isinstance(item.pro_os, float) else item.pro_os.strip()) if item.pro_os else '',
                    serial_no=(str(int(item.pro_serial_no)).strip() if isinstance(item.pro_serial_no, float) else item.pro_serial_no.strip()) if item.pro_serial_no else '',
                    mac=(str(int(item.pro_mac)).strip() if isinstance(item.pro_mac, float) else item.pro_mac.strip()) if item.pro_mac else '',
                    battery=(str(int(item.pro_battery)).strip() if isinstance(item.pro_battery, float) else item.pro_battery.strip()) if item.pro_battery else '',
                    power=(str(int(item.pro_power)).strip() if isinstance(item.pro_power, float) else item.pro_power.strip()) if item.pro_power else '',
                    remark=(str(int(item.pro_remark)).strip() if isinstance(item.pro_remark, float) else item.pro_remark.strip()) if item.pro_remark else '',
                    asset_master_id=master.id
                )
                db.session.add(asset_property)
                db.session.commit()
            # 记录出入库履历
            io_history = BizStockHistory(
                id=uuid.uuid4().hex,
                bg_id=current_user.company_id,
                bill_no=bill_in_no,
                asset_id=master.id,
                class1_id=class1_id,
                class2_id=class2_id,
                class3_id=class3_id,
                brand_id=brand_id,
                model_id=model_id,
                io_type=1,
                amount=reg_amount,
                code=master.code,
                sap_code=master.sap_code
            )
            # 出入库类型 - 登记入库
            e = get_enum_value('D010', '1')
            if e:
                io_history.io_class_id = e.id
            db.session.add(io_history)
            db.session.commit()
            # 更新库存余额表 - 状态为在库的才执行库存余额更新
            if str(int(item.status)) == '1':
                conditions = set()
                conditions.add(BizStockAmount.class1_id == class1_id)
                conditions.add(BizStockAmount.class2_id == class2_id)
                conditions.add(BizStockAmount.class3_id == class3_id)
                conditions.add(BizStockAmount.brand_id == brand_id)
                conditions.add(BizStockAmount.model_id == model_id)
                conditions.add(BizStockAmount.bg_id == current_user.company_id)
                stock_amount = BizStockAmount.query.filter(*conditions).first()
                # 找到则更新，否则新增
                if stock_amount:
                    stock_amount.amount += reg_amount
                    stock_amount.update_id = current_user.id
                    stock_amount.updatetime_utc = datetime.utcfromtimestamp(time.time())
                    stock_amount.updatetime_loc = datetime.fromtimestamp(time.time())
                else:
                    stock_amount = BizStockAmount(
                        id=uuid.uuid4().hex,
                        bg_id=current_user.company_id,
                        class1_id=class1_id,
                        class2_id=class2_id,
                        class3_id=class3_id,
                        brand_id=brand_id,
                        model_id=model_id,
                        amount=reg_amount
                    )
                    db.session.add(stock_amount)
                db.session.commit()
        return jsonify(code=1, result='资产信息导入成功！')
@bp_master.route('/card_show/<asset_id>', methods=['GET', 'POST'])
@login_required
@log_record('显示资产信息卡')
def card_show(asset_id):
    asset = BizAssetMaster.query.get(asset_id)
    return jsonify(asset_sap_code=asset.sap_code,
                   asset_buy_date=asset.buy_date.strftime('%Y-%m-%d'),
                   asset_name=asset.class3.name,
                   asset_code=asset.code,
                   asset_model='{} - {}'.format(asset.brand.name, asset.model.name),
                   asset_bar=asset.bar_path)
@bp_master.route('/card_print/<asset_id>', methods=['GET', 'POST'])
@login_required
@log_record('打印资产信息卡')
def card_print(asset_id):
    asset = BizAssetMaster.query.get(asset_id)
    # 生成PDF文档后打印 - 此方法废弃(PDF无法使用条码打印机打印)
    # from com.printer import gen_pdf, print_asset_card
    # file_name = gen_pdf(asset)
    # print_asset_card(file_name)
    # 使用Excel模板进行打印，每次拷贝模板写入数据打印即可
    import shutil
    from com.printer import print_asset_card, insert_print_data
    # 拷贝模板生成打印文件
    template = current_app.config['PRINTER_TEMPLATE']
    file_path, file_name = os.path.split(template)
    file_ext = file_name.split('.')[1]
    print_bar = os.path.join(file_path, asset.code+'.'+file_ext)
    shutil.copy(template, print_bar)
    insert_print_data(asset, print_bar)
    print_asset_card(print_bar)
    return jsonify(code=1, message='打印成功！')
