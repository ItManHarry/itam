import xlrd2, os
from flask import Blueprint, render_template, flash, redirect, url_for, request, session, current_app, jsonify
from flask_login import login_required, current_user
import flask_excel as excel
from com.models import BizAssetMaster, BizAssetCheck, BizCompany, RelAssetCheckItem, BizEmployee
from com.plugins import db
from com.decorators import log_record
from com.forms.biz.daily.inventory import CheckForm, CheckSearchForm, SelfCheckForm
import uuid, time
from datetime import datetime
from com.utils import gen_bill_no
from collections import defaultdict, namedtuple
from com.email import send_mail
from com.views.system.dicts import get_enum_value
bp_inventory = Blueprint('inventory', __name__)
@bp_inventory.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查看资产盘点单信息')
def index():
    form = CheckSearchForm()
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        try:
            check_no = session['check_view_search_no'] if session['check_view_search_no'] else ''     # 出库类型
            check_year = session['check_view_search_year'] if session['check_view_search_year'] else ''           # 出库单号
        except KeyError:
            check_no = ''
            check_year = ''
        form.check_no.data = check_no
        form.check_year.data = check_year
    if request.method == 'POST':
        page = 1
        check_no = form.check_no.data
        check_year = form.check_year.data
        session['check_view_search_no'] = check_no
        session['check_view_search_year'] = check_year
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']
    conditions = set()
    conditions.add(BizAssetCheck.bg_id == current_user.company_id)
    conditions.add(BizAssetCheck.check_no.like('%'+check_no+'%'))
    if form.check_year.data:
        conditions.add(BizAssetCheck.check_year == check_year)
    pagination = BizAssetCheck.query.filter(*conditions).order_by(BizAssetCheck.check_year).paginate(page, per_page)
    inventories = pagination.items
    return render_template('biz/daily/inventory/index.html', pagination=pagination, inventories=inventories, form=form)
@bp_inventory.route('/add', methods=['GET', 'POST'])
@login_required
@log_record('新增资产盘点单')
def add():
    form = CheckForm()
    # 只盘点资产
    assets = BizAssetMaster.query.filter_by(is_asset=1).order_by(BizAssetMaster.code).all()
    companies = BizCompany.query.order_by(BizCompany.name).all()
    selected_assets = []
    if form.check_asset_ids.data:
        selected_assets = BizAssetMaster.query.filter(BizAssetMaster.id.in_(form.check_asset_ids.data.split(','))).order_by(BizAssetMaster.code).all()
    if form.validate_on_submit():
        form.check_no.data = gen_bill_no('CK')
        check = BizAssetCheck(
            id=uuid.uuid4().hex,
            bg_id=current_user.company_id,
            create_id=current_user.id,
            check_no=form.check_no.data,
            check_year=form.check_year.data,
            check_batch=form.check_batch.data,
            plan_start_date=datetime.strptime(form.plan_start_date.data, '%Y-%m-%d'),
            plan_finish_date=datetime.strptime(form.plan_finish_date.data, '%Y-%m-%d'),
            checker_id=form.checker_id.data
        )
        db.session.add(check)
        db.session.commit()
        form.id.data = check.id
        # 保存关联的盘点资产清单
        save_rels(form)
        flash('资产盘点单保存成功！')
        return redirect(url_for('.index'))
    return render_template('biz/daily/inventory/add.html', form=form, selected_assets=selected_assets, assets=[asset for asset in assets if asset.status.item not in ['8', '9']], companies=companies)
@bp_inventory.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
@log_record('修改盘点单信息')
def edit(id):
    check = BizAssetCheck.query.get(id)
    form = CheckForm()
    form.id.data = id
    form.check_no.data = check.check_no
    assets = BizAssetMaster.query.filter_by(is_asset=1).order_by(BizAssetMaster.code).all()
    companies = BizCompany.query.order_by(BizCompany.name).all()
    items = RelAssetCheckItem.query.filter_by(check_id=id).all()
    asset_ids = [item.asset_id for item in items]
    if request.method == 'GET':
        form.check_year.data = check.check_year
        form.check_batch.data = check.check_batch
        form.check_asset_ids.data = ','.join(asset_ids)
        form.plan_start_date.data = check.plan_start_date.strftime('%Y-%m-%d')
        form.plan_finish_date.data = check.plan_finish_date.strftime('%Y-%m-%d')
        form.checker_id.data = check.checker_id
        form.checker.data = check.checker.name+'('+check.checker.code+')'
    if form.validate_on_submit():
        # 删除之前关联的盘点资产清单
        for item in items:
            db.session.delete(item)
            db.session.commit()
        # 执行数据保存
        check.check_year = form.check_year.data
        check.check_batch = form.check_batch.data
        check.plan_start_date = datetime.strptime(form.plan_start_date.data, '%Y-%m-%d')
        check.plan_finish_date = datetime.strptime(form.plan_finish_date.data, '%Y-%m-%d')
        check.checker_id = form.checker_id.data
        check.update_id = current_user.id
        check.updatetime_utc = datetime.utcfromtimestamp(time.time())
        check.updatetime_loc = datetime.fromtimestamp(time.time())
        db.session.commit()
        # 保存关联的盘点资产清单
        save_rels(form)
        flash('资产盘点修改成功！')
        return redirect(url_for('.index'))
    return render_template('biz/daily/inventory/edit.html', form=form, selected_assets=check.assets, assets=[asset for asset in assets if asset.status.item not in ['8', '9']], companies=companies)
@bp_inventory.route('/my_check/<check_id>/<employee_id>', methods=['GET', 'POST'])
def my_check(check_id, employee_id):
    check = BizAssetCheck.query.get(check_id)
    form = SelfCheckForm()
    form.id.data = check_id
    assets = [asset for asset in check.assets if asset.user]
    to_employees = defaultdict(list)
    for asset in assets:
        to_employees[asset.user.id].append(asset)
    if form.validate_on_submit():
        ids = form.check_asset_ids.data.split(',')
        rls = form.check_asset_rls.data.split(',')
        results = dict(zip(ids, rls))
        for asset_id, result in results.items():
            print('Asset id is : ', asset_id, ', check result is : ', result)
            rel = RelAssetCheckItem.query.filter(RelAssetCheckItem.check_id == check_id, RelAssetCheckItem.asset_id == asset_id).first()
            if rel:
                rel.passed_biz = True if int(result) else False
        db.session.commit()
        flash('资产自盘点成功,感谢配合(本页面可以多次从邮件点开进行确认)！')
    rels = RelAssetCheckItem.query.filter(RelAssetCheckItem.check_id == check_id).all()
    # 自盘点结果字典
    result_dict = {rel.asset_id: rel.passed_biz for rel in rels}
    for asset_id, checked in result_dict.items():
        print('Asset Id : ', asset_id, ', checked : ', checked)
    return render_template('biz/daily/inventory/self_check.html', form=form, assets=to_employees[employee_id], check=check, result_dict=result_dict)
@bp_inventory.route('/export/<inventory_id>')
@login_required
@log_record('导出盘点清单信息')
def export(inventory_id):
    excel.init_excel(current_app)
    check = BizAssetCheck.query.get(inventory_id)
    rels = RelAssetCheckItem.query.filter(RelAssetCheckItem.check_id == inventory_id).all()
    biz_result_dict = {rel.asset_id: rel.passed_biz for rel in rels}
    it_result_dict = {rel.asset_id: rel.passed_it for rel in rels}
    ml_result_dict = {rel.asset_id: rel.more_or_less for rel in rels}
    remark_dict = {rel.asset_id: rel.remark for rel in rels}
    assets = check.assets
    data_header = [['盘点ID', '盘点单号', '资产ID', '资产编号', 'SAP资产编号', '资产名称', '品牌', '型号', '使用者', '使用者盘点(Y/N)', 'IT盘点通过(Y/N)', '盈/亏', '盘点结果备注']]
    data_body = [[check.id, check.check_no, asset.id, asset.code, asset.sap_code, asset.class3.name, asset.brand.name, asset.model.name, asset.user.name if asset.user else '', 'Y' if biz_result_dict[asset.id] else 'N', 'Y' if it_result_dict[asset.id] else 'N', ml_result_dict[asset.id], remark_dict[asset.id]] for asset in assets]
    data = data_header + data_body
    file_name = '({})盘点清单'.format(check.check_no)
    return excel.make_response_from_array(data, file_name=file_name, file_type='xlsx')
@bp_inventory.route('/import_back', methods=['GET', 'POST'])
@login_required
@log_record('导入盘点结果')
def import_back():
    if 'file' not in request.files:
        return jsonify(code=0, message='盘点结果导入失败,文件未读取！')
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
        results = []
        InventoryResult = namedtuple('InventoryResult', ['check_id', 'check_no', 'asset_id', 'asset_cd', 'asset_sap_cd', 'asset_nm', 'brand', 'model', 'used_by', 'user_check', 'it_check', 'more_or_less', 'remark'])
        for i in range(1, rows):
            values = sheet.row_values(i)
            results.append(InventoryResult(*values))
        # 执行保存
        for result in results:
            print(result.check_id, result.check_no, result.asset_id, result.asset_cd, result.asset_nm)
            rel = RelAssetCheckItem.query.filter(RelAssetCheckItem.check_id == result.check_id, RelAssetCheckItem.asset_id == result.asset_id).first()
            if rel:
                rel.passed_biz = True if result.user_check.strip() == 'Y' else False
                rel.passed_it = True if result.it_check.strip() == 'Y' else False
                rel.more_or_less = result.more_or_less if result.more_or_less else ''
                rel.remark = result.remark
                if result.more_or_less.strip() == '亏':
                    asset = BizAssetMaster.query.get(result.asset_id)
                    e = get_enum_value('D003', '10')
                    if e:
                        asset.status_id = e.id
            db.session.commit()
        return jsonify(code=1, message='盘点结果导入成功！')
@bp_inventory.route('/self_check/<inventory_id>', methods=['GET', 'POST'])
@login_required
@log_record('提醒使用者进行资产自盘点')
def self_check(inventory_id):
    check = BizAssetCheck.query.get(inventory_id)
    assets = [asset for asset in check.assets if asset.user]
    print('Assets length is : ', len(assets))
    to_employees = defaultdict(list)
    for asset in assets:
        to_employees[asset.user.id].append(asset)
    # 发送邮件提醒
    for employee_id, employee_assets in to_employees.items():
        print('Employee id  is : ', employee_id, ', asset are : ', employee_assets)
        employee = BizEmployee.query.get(employee_id)
        if employee.email:
            send_mail(subject='资产自盘点邀请', to=[employee.email], cc=[], template='emails/self_check_remind', assets=employee_assets, check=check, employee=employee)
    return jsonify(code=0, message='自盘点提醒邮件发送成功!')
def save_rels(form):
    selected_assets = BizAssetMaster.query.filter(BizAssetMaster.id.in_(form.check_asset_ids.data.split(','))).order_by(BizAssetMaster.code).all()
    for asset in selected_assets:
        rel = RelAssetCheckItem(
            id=uuid.uuid4().hex,
            check_id=form.id.data,
            asset_id=asset.id,
            create_id=current_user.id
        )
        db.session.add(rel)
    db.session.commit()