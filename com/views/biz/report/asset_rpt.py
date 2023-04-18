from flask import Blueprint, render_template, current_app, jsonify, session, request
from flask_login import login_required, current_user
from com.models import BizAssetMaster, BizAssetClass, BizBrandMaster
from com.decorators import log_record
from com.forms.biz.report.asset_rpt import SearchForm
import flask_excel as excel
from operator import itemgetter
from itertools import groupby
from datetime import datetime
import json
bp_asset_rpt = Blueprint('asset_rpt', __name__)
@bp_asset_rpt.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查看资产报表')
def index():
    form = SearchForm()
    # classes_1 = BizAssetClass.query.filter(BizAssetClass.code._in('01', '02'), BizAssetClass.bg_id == current_user.company_id).order_by(BizAssetMaster.code).all()
    # form.class1.choices = [('0', '资产大类-All')]
    # if classes_1:
    #     form.class1.choices += [(clazz.id, clazz.name) for clazz in classes_1]
    form.class2.choices = [('0', '资产分类-All')]
    classes_2 = BizAssetClass.query.filter_by(grade=2).order_by(BizAssetClass.name).all()
    if classes_2:
        form.class2.choices += [(clazz.id, clazz.name) for clazz in classes_2]
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
                session['asset_report_search_class2']
                searched = True
            except KeyError:
                print('NOT SEARCHED AT ALL!')
            form.class2.data = session['asset_report_search_class2'] if searched else '0'
            form.brands.data = session['asset_report_search_brand'] if searched else '0'
            form.code.data = session['asset_report_search_code'] if searched else ''
            form.sap_code.data = session['asset_report_search_sap_code'] if searched else ''
            if form.class2.data is None or form.class2.data == '0':
                form.class3.choices = [('0', '资产名称-All')]
            else:
                class_2 = BizAssetClass.query.get(form.class2.data)
                form.class3.choices = [('0', '资产名称-All')]+[(rel.child_class_id, rel.child_class.name) for rel in class_2.get_child_class]
                form.class3.data = session['asset_report_search_class3'] if searched else '0'
            if form.brands.data is None or form.brands.data == '0':
                form.models.choices = [('0', '型号-All')]
            else:
                brand = BizBrandMaster.query.get(form.brands.data)
                form.models.choices = [('0', '型号-All')]+[(model.id, model.name) for model in brand.models]
                form.models.data = session['asset_report_search_model'] if searched else '0'
        else: # 初始登录
            page = 1
            try:
                del session['asset_report_search_class2']
            except KeyError:
                print('NOT SET THIS KEY!!!')
            form.class3.choices = [('0', '资产名称-All')]
            form.models.choices = [('0', '型号-All')]
            form.code.data = ''
            form.sap_code.data = ''
    if request.method == 'POST':
        page = 1
        first_search = True
        try:
            session['asset_report_search_class2']
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
                if session['asset_report_search_class2'] is not None and session['asset_report_search_class2'] != form.class2.data:
                    form.class3.data = '0'
        if form.brands.data == '0':
            form.models.choices = [('0', '型号-All')]
            form.models.data = '0'
        else:
            brand = BizBrandMaster.query.get(form.brands.data)
            form.models.choices = [('0', '型号-All')] + [(model.id, model.name) for model in brand.models]
            if not first_search:
                if session['asset_report_search_brand'] is not None and session['asset_report_search_brand'] != form.brands.data:
                    form.models.data = '0'
        session['asset_report_search_class2'] = form.class2.data
        session['asset_report_search_class3'] = form.class3.data
        session['asset_report_search_brand'] = form.brands.data
        session['asset_report_search_model'] = form.models.data
        session['asset_report_search_code'] = form.code.data
        session['asset_report_search_sap_code'] = form.sap_code.data
    # 搜索条件
    search_all = {}
    search_all['class2'] = '0'
    search_all['class3'] = '0'
    search_all['brands'] = '0'
    search_all['models'] = '0'
    search_all['code'] = form.code.data
    search_all['sap_code'] = form.sap_code.data
    search_all['log_s'] = ''
    search_all['log_e'] = ''
    if form.class2.data is not None and form.class2.data != '0':
        search_all['class2'] = form.class2.data
    if form.class3.data is not None and form.class3.data != '0':
        search_all['class3'] = form.class3.data
    if form.brands.data is not None and form.brands.data != '0':
        search_all['brands'] = form.brands.data
    if form.models.data is not None and form.models.data != '0':
        search_all['models'] = form.models.data
    if form.log_s.data:
        search_all['log_s'] = form.log_s.data
    if form.log_e.data:
        search_all['log_e'] = form.log_e.data
    conditions = get_condition_set(search_all)
    session['asset_report_current_page'] = page
    # 分页数据
    per_page = 5 # current_app.config['ITEM_COUNT_PER_PAGE']
    pagination = BizAssetMaster.query.filter(*conditions).order_by(BizAssetMaster.code).paginate(page, per_page)
    assets = pagination.items
    # 图表数据
    asset_all = BizAssetMaster.query.filter(*conditions).order_by(BizAssetMaster.code).all()
    asset_sum = [{'name': asset.class3.name, 'status': asset.status.display} for asset in asset_all]
    # for asset in asset_sum:
    #     for k, v in asset.items():
    #         print('{} : {}'.format(k, v))
    # print('-' * 80)
    # 资产名称别统计 - 柱图
    asset_sum.sort(key=itemgetter('name'))
    asset_bar = []
    for name, name_data in groupby(asset_sum, key=itemgetter('name')):
        name_data = [item for item in name_data]
        asset_bar.append({name: len(name_data)})
    # for item in asset_bar:
    #     print(item)
    # 资产状态别统计 - 饼图
    asset_pie = []
    asset_sum.sort(key=itemgetter('status'))
    for status, status_data in groupby(asset_sum, key=itemgetter('status')):
        status_data = [item for item in status_data]
        asset_pie.append({status: len(status_data)})
    # print('-' * 80)
    # for item in asset_pie:
    #     print(item)
    # Excel导出
    session['asset_export_all'] = search_all
    session['asset_export_per'] = [[asset.company.name if asset.company else '', asset.department.name if asset.department else '', asset.class3.name, asset.code, asset.sap_code, asset.brand.name, asset.model.name, asset.buy_date.strftime('%Y-%m-%d'), asset.vendor.name, asset.user.name if asset.user else '', asset.status.display, '已出库' if asset.is_out else '在库', asset.store.name] for asset in assets]     # 导出当前
    return render_template('biz/report/asset_rpt/index.html', form=form, assets=assets, pagination=pagination, asset_bar=json.dumps(asset_bar), asset_pie=json.dumps(asset_pie))
@bp_asset_rpt.route('/export/<int:sign>')
@login_required
@log_record('导出资产信息')
def export(sign):
    '''
    导出资产信息
    :param sign: 0:全部导出 1:导出当前页
    :return:
    '''
    excel.init_excel(current_app)
    page = session['asset_report_current_page']
    data_header = [['所属法人', '所属部门', '资产名称', '资产编号', 'SAP资产编号', '品牌', '型号', '采购日期', '供应商', '使用者', '资产状态', '库存状态', '仓库所属']]
    if sign == 0:
        search_all = session['asset_export_all']
        conditions = get_condition_set(search_all)
        asset_all = BizAssetMaster.query.filter(*conditions).order_by(BizAssetMaster.code).all()
        data_body = [[asset.company.name if asset.company else '', asset.department.name if asset.department else '', asset.class3.name, asset.code, asset.sap_code, asset.brand.name, asset.model.name, asset.buy_date.strftime('%Y-%m-%d'), asset.vendor.name, asset.user.name if asset.user else '', asset.status.display, '已出库' if asset.is_out else '在库', asset.store.name] for asset in asset_all]
    else:
        data_body = session['asset_export_per']
    data = data_header + data_body
    print('Data header : ', data_header)
    print('Data body : ', data_body)
    file_name = u'资产信息-all' if sign == 0 else u'资产信息-' + str(page)
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
    conditions.add(BizAssetMaster.code.like('%' + cm['code'] + '%'))
    conditions.add(BizAssetMaster.sap_code.like('%' + cm['sap_code'] + '%'))
    if cm['class2'] != '0':
        conditions.add(BizAssetMaster.class2_id == cm['class2'])
    if cm['class3'] != '0':
        conditions.add(BizAssetMaster.class3_id == cm['class3'])
    if cm['brands'] != '0':
        conditions.add(BizAssetMaster.brand_id == cm['brands'])
    if cm['models'] != '0':
        conditions.add(BizAssetMaster.model_id == cm['models'])
    if cm['log_s']:
        conditions.add(BizAssetMaster.createtime_loc >= datetime.strptime(cm['log_s'], '%Y-%m-%d'))
    if cm['log_e']:
        conditions.add(BizAssetMaster.createtime_loc <= datetime.strptime(cm['log_e'], '%Y-%m-%d'))
    return conditions