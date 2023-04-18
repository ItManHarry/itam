from flask import Blueprint, render_template, current_app, jsonify, session, request
from flask_login import login_required, current_user
from com.models import BizAssetMaster, BizCompany, BizDepartment
from com.decorators import log_record
from com.forms.biz.report.asset_sap_rpt import SearchForm
import flask_excel as excel
bp_asset_sap_rpt = Blueprint('asset_sap_rpt', __name__)
@bp_asset_sap_rpt.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查看资产报表-SAP别')
def index():
    form = SearchForm()
    companies = [('0', '法人所属-All')] + [(company.id, company.name) for company in BizCompany.query.order_by(BizCompany.code.desc()).all()]
    form.companies.choices = companies
    if request.method == 'GET':
        page = request.args.get('page', type=int) if request.args.get('page') else 0
        # 如果是分页的话，就要取对应的搜索值，否则所有条件置空
        if page: # 分页查看
            searched = False
            try:
                session['asset_sap_report_search_company']
                searched = True
            except KeyError:
                print('NOT SEARCHED AT ALL!')
            form.companies.data = session['asset_sap_report_search_company'] if searched else '0'
            form.sap_code.data = session['asset_report_search_sap_code'] if searched else ''
            if form.companies.data is None or form.companies.data == '0':
                form.departments.choices = [('0', '所属部门-All')]
            else:
                company = BizCompany.query.get(form.companies.data)
                form.departments.choices = [('0', '所属部门-All')] + [(department.id, department.name) for department in company.departments]
                form.departments.data = session['asset_sap_report_search_department'] if searched else '0'
            if form.departments.data is None or form.departments.data == '0':
                form.employees.choices = [('0', '使用者-All')]
            else:
                department = BizDepartment.query.get(form.departments.data)
                form.employees.choices = [('0', '使用者-All')] + [(employee.id, employee.name) for employee in department.employees]
                form.employees.data = session['asset_sap_report_search_employee'] if searched else '0'
        else:
            page = 1
            try:
                del session['asset_sap_report_search_company']
            except KeyError:
                print('NOT SET THIS KEY!!!')
            form.departments.choices = [('0', '所属部门-All')]
            form.employees.choices = [('0', '使用者-All')]
            form.sap_code.data = ''
    if request.method == 'POST':
        page = 1
        first_search = True
        try:
            session['asset_sap_report_search_company']
            first_search = False
        except KeyError:
            print('THIS IS FIRST TIME OF SEARCHING!')
        if form.companies.data == '0':
            form.departments.choices = [('0', '所属部门-All')]
            form.departments.data = '0'
        else:
            company = BizCompany.query.get(form.companies.data)
            form.departments.choices = [('0', '所属部门-All')] + [(department.id, department.name) for department in company.departments]
            if not first_search:
                if session['asset_sap_report_search_company'] is not None and session['asset_sap_report_search_company'] != form.companies.data:
                    form.departments.data = '0'
        if form.departments.data == '0':
            form.employees.choices = [('0', '使用者-All')]
            form.employees.data = '0'
        else:
            department = BizDepartment.query.get(form.departments.data)
            form.employees.choices = [('0', '使用者-All')] + [(employee.id, employee.name) for employee in department.employees]
            if not first_search:
                if session['asset_sap_report_search_department'] is not None and session['asset_sap_report_search_department'] != form.departments.data:
                    form.employees.data = '0'
        session['asset_sap_report_search_company'] = form.companies.data
        session['asset_sap_report_search_department'] = form.departments.data
        session['asset_sap_report_search_employee'] = form.employees.data
        session['asset_report_search_sap_code'] = form.sap_code.data
    # 搜索条件
    search_all = {}
    search_all['sap_code'] = form.sap_code.data
    search_all['company_id'] = '0'
    search_all['department_id'] = '0'
    search_all['user_id'] = '0'
    if form.companies.data is not None and form.companies.data != '0':
        search_all['company_id'] = form.companies.data
    if form.departments.data is not None and form.departments.data != '0':
        search_all['department_id'] = form.departments.data
    if form.employees.data is not None and form.employees.data != '0':
        search_all['user_id'] = form.employees.data
    conditions = get_condition_set(search_all)
    session['asset_sap_report_current_page'] = page
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']
    pagination = BizAssetMaster.query.filter(*conditions).order_by(BizAssetMaster.code).paginate(page, per_page)
    assets = pagination.items    
    session['asset_sap_export_all'] = search_all  # 导出全部
    session['asset_sap_export_per'] = [[asset.company.name, asset.department.name, asset.class3.name, asset.code, asset.get_parent_asset.code if asset.get_parent_asset else '', asset.sap_code, asset.brand.name, asset.model.name, asset.vendor.name, asset.user.name if asset.user else '', asset.reg_date.strftime('%Y-%m-%d'), asset.status.display, '已出库' if asset.is_out else '在库'] for asset in assets]     # 导出当前
    return render_template('biz/report/asset_sap_rpt/index.html', form=form, assets=assets, pagination=pagination)
@bp_asset_sap_rpt.route('/export/<int:sign>')
@login_required
@log_record('导出SAP别资产信息')
def export(sign):
    '''
    导出SAP别资产信息
    :param sign: 0:全部导出 1:导出当前页
    :return:
    '''
    excel.init_excel(current_app)
    page = session['asset_sap_report_current_page']
    data_header = [['所属法人', '所属部门', '资产名称', '资产编号', '主资产编号', 'SAP资产编号', '品牌', '型号', '供应商', '使用者', '登记日期', '资产状态', '库存状态']]
    if sign == 0:
        search_all = session['asset_sap_export_all']
        conditions = get_condition_set(search_all)
        asset_all = BizAssetMaster.query.filter(*conditions).order_by(BizAssetMaster.code).all()
        data_body = [[asset.company.name, asset.department.name, asset.class3.name, asset.code, asset.get_parent_asset.code if asset.get_parent_asset else '', asset.sap_code, asset.brand.name, asset.model.name, asset.vendor.name, asset.user.name if asset.user else '', asset.reg_date.strftime('%Y-%m-%d'), asset.status.display, '已出库' if asset.is_out else '在库'] for asset in asset_all]     # 导出全部
    else:
        data_body = session['asset_sap_export_per']
    data = data_header + data_body
    file_name = u'资产信息SAP-all' if sign == 0 else u'资产信息SAP-' + str(page)
    print('Excel file name is : ', file_name)
    return excel.make_response_from_array(data, file_name=file_name, file_type='xlsx')
def get_condition_set(cm):
    '''
    获取查询条件
    :param cm:
    :return:
    '''
    conditions = set()
    conditions.add(BizAssetMaster.bg_id == current_user.company_id)
    conditions.add(BizAssetMaster.user_id != '')
    conditions.add(BizAssetMaster.sap_code != '')
    conditions.add(BizAssetMaster.sap_code.like('%' + cm['sap_code'] + '%'))
    if cm['company_id'] != '0':
        conditions.add(BizAssetMaster.company_id == cm['company_id'])
    if cm['department_id'] != '0':
        conditions.add(BizAssetMaster.department_id == cm['department_id'])
    if cm['user_id'] != '0':
        conditions.add(BizAssetMaster.user_id == cm['user_id'])
    return conditions