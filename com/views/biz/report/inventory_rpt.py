from flask import Blueprint, render_template, current_app, jsonify, session, request
from flask_login import login_required, current_user
from com.models import BizAssetCheck, RelAssetCheckItem
from com.decorators import log_record
from com.forms.biz.report.inventory_rpt import SearchForm
import flask_excel as excel
from collections import namedtuple
from flask_sqlalchemy import Pagination
from operator import itemgetter
from itertools import groupby
from datetime import date
import json
bp_inventory_rpt = Blueprint('inventory_rpt', __name__)
@bp_inventory_rpt.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查看资产报表')
def index():
    form = SearchForm()
    companies = [current_user.company]
    if request.method == 'GET':
        page = request.args.get('page', type=int) if request.args.get('page') else 0
        # 如果是分页的话，就要取对应的搜索值，否则所有条件置空
        if page: # 分页查看
            searched = False
            try:
                session['inventory_report_search_year']
                searched = True
            except KeyError:
                print('NOT SEARCHED AT ALL!')
            form.inventory_year.data = session['inventory_report_search_year'] if searched else ''
            form.inventory_batch.data = session['inventory_report_search_batch'] if searched else ''
            form.inventory_by_id.data = session['inventory_report_search_handler'] if searched else ''
            form.status.data = session['inventory_report_search_status'] if searched else '0'
        else:  # 初始登录
            page = 1
            try:
                del session['inventory_report_search_year']
            except KeyError:
                print('NOT SET THIS KEY!!!')
            form.inventory_year.data = date.today().strftime('%Y')
            form.inventory_batch.data = ''
            form.inventory_by_id.data = ''
            form.status.data = '0'
    if request.method == 'POST':
        page = 1
        session['inventory_report_search_year'] = form.inventory_year.data
        session['inventory_report_search_batch'] = form.inventory_batch.data
        session['inventory_report_search_handler'] = form.inventory_by_id.data
        session['inventory_report_search_status'] = form.status.data
    # 执行查询
    conditions = set()
    conditions.add(BizAssetCheck.bg_id == current_user.company_id)
    if form.inventory_year.data:
        conditions.add(BizAssetCheck.check_year == form.inventory_year.data)
    conditions.add(BizAssetCheck.check_batch.like('%' + form.inventory_batch.data + '%'))
    if form.inventory_by_id.data:
        conditions.add(BizAssetCheck.checker_id == form.inventory_by_id.data)
    inventories = BizAssetCheck.query.filter(*conditions).order_by(BizAssetCheck.check_year.desc(), BizAssetCheck.check_batch).all()
    rels = RelAssetCheckItem.query.filter(RelAssetCheckItem.check_id.in_([inventory.id for inventory in inventories])).all()
    it_result_dict = {rel.check_id+rel.asset_id: rel.passed_it for rel in rels}
    # for k, v in it_result_dict.items():
    #     print('Check key : {}, value : {}'.format(k, v))
    InventoryInfo = namedtuple('InventoryInfo', ['i_year', 'i_batch', 'i_start_dt', 'i_finish_dt', 'i_handler', 'a_code', 'a_sap_code',  'a_name', 'a_status', 'a_company', 'a_department', 'a_user', 'a_buy_dt', 'a_store', 'i_finished'])
    items = []
    for inventory in inventories:
        if inventory.assets:
            for asset in inventory.assets:
                row = [inventory.check_year, inventory.check_batch, inventory.plan_start_date.strftime('%Y-%m-%d'), inventory.plan_finish_date.strftime('%Y-%m-%d'), inventory.checker.name, asset.code, asset.sap_code, asset.class3.name, asset.is_out, asset.company.name if asset.company else '', asset.department.name if asset.department else '', asset.user.name if asset.user else '', asset.buy_date.strftime('%Y-%m-%d'), asset.store.name, it_result_dict[inventory.id+asset.id]]
                items.append(InventoryInfo(*row))
    if form.status.data == '1':     # 在库
        items = [item for item in items if not item.a_status]
    elif form.status.data == '2':   # 已出库
        items = [item for item in items if item.a_status]
    session['asset_inventory_current_page'] = page
    per_page = 5    # current_app.config['ITEM_COUNT_PER_PAGE']
    items_per_page = items[(page-1) * per_page: page * per_page] if items else []
    items_per = [[item.i_year, item.i_batch, item.i_handler, item.i_start_dt, item.i_finish_dt, item.a_code, item.a_sap_code, item.a_name, '出库' if item.a_status else '在库', item.a_company, item.a_department, item.a_user, item.a_buy_dt, item.a_store, 'Y' if item.i_finished else 'N'] for item in items_per_page]
    items_all = [[item.i_year, item.i_batch, item.i_handler, item.i_start_dt, item.i_finish_dt, item.a_code, item.a_sap_code, item.a_name, '出库' if item.a_status else '在库', item.a_company, item.a_department, item.a_user, item.a_buy_dt, item.a_store, 'Y' if item.i_finished else 'N'] for item in items]
    # 汇总数据
    sum_data = [{'y_b_h': item.i_year+'-'+item.i_batch+'-'+item.i_handler, 'i_year': item.i_year, 'i_batch': item.i_batch, 'i_handler': item.i_handler, 'a_status': item.a_status, 'i_finished': item.i_finished, 'a_name': item.a_name} for item in items]
    # for data in sum_data:
    #     for k, v in data.items():
    #         print('Key is : {}, value is : {}'.format(k, v))
    sum_data.sort(key=itemgetter('i_year'))
    total_data = []
    for year, data_year in groupby(sum_data, key=itemgetter('i_year')):
        sub_data = {}
        data_year = [item for item in data_year]
        # print('Year ', year, 'Items ', len(data_year))
        sub_data['Y-'+year] = len(data_year)
        data_year.sort(key=itemgetter('i_batch'))
        for batch, batch_data in groupby(data_year, key=itemgetter('i_batch')):
            batch_data = [item for item in batch_data]
            # print('  Batch ', batch, 'Items ', len(batch_data))
            sub_data['B-'+batch] = len(batch_data)
            batch_data.sort(key=itemgetter('i_handler'))
            for handler, handler_data in groupby(batch_data, key=itemgetter('i_handler')):
                handler_data = [item for item in handler_data]
                # print('    Handler ', handler, 'Items ', len(handler_data))
                sub_data['C-'+batch+'-'+handler] = len(handler_data)
        total_data.append(sub_data)
    # for group in total_data:
    #     for k, v in group.items():
    #         print('Key {} value {}.'.format(k, v))
    # print('-' * 80)
    # 图表使用 - 担当别
    chart_data = []
    sum_data.sort(key=itemgetter('y_b_h'))
    for handler, handler_data in groupby(sum_data, key=itemgetter('y_b_h')):
        handler_data = [item for item in handler_data]
        plan_amount = len(handler_data)                                                 # 盘点总数量
        fin_amount = len([item for item in handler_data if item['i_finished']])         # 完成数量
        un_amount = len([item for item in handler_data if not item['i_finished']])      # 未完成数量
        chart_data.append({handler: [plan_amount, fin_amount, un_amount]})
        # print('Handler ', handler, 'Items ', len(handler_data))
        # for item in handler_data:
        #     print('\t', item)
    print(json.dumps(chart_data))
    # 图表使用 - 资产别
    dash_data = []
    sum_data.sort(key=itemgetter('a_name'))
    for asset, asset_data in groupby(sum_data, key=itemgetter('a_name')):
        asset_data = [item for item in asset_data]
        plan_amount = len(asset_data)                                               # 总数量
        fin_amount = len([item for item in asset_data if item['i_finished']])       # 完成数量
        un_amount = len([item for item in asset_data if not item['i_finished']])    # 未完成数量
        dash_data.append({asset: [plan_amount, fin_amount, un_amount, round((fin_amount / plan_amount) * 100, 2)]})
        # print('Asset : ', asset)
        # for item in asset_data:
        #     print('\t', item)
    # 数据导出
    session['asset_inventory_export_all'] = items_all
    session['asset_inventory_export_per'] = items_per
    # 分页
    pagination = Pagination('', page, per_page, len(items), items_per_page)
    return render_template('biz/report/inventory_rpt/index.html', form=form, companies=companies, items=items_per_page, pagination=pagination, total_data=total_data, chart_data=json.dumps(chart_data), dash_data=json.dumps(dash_data))
@bp_inventory_rpt.route('/export/<int:sign>')
@login_required
@log_record('导出盘点明细信息')
def export(sign):
    '''
    导出盘点明细信息
    :param sign: 0:全部导出 1:导出当前页
    :return:
    '''
    excel.init_excel(current_app)
    page = session['asset_inventory_current_page']
    data_header = [['盘点年度', '盘点批次', '盘点担当', '计划开始时间', '计划结束时间', '资产编号', 'SAP资产编号', '资产名称', '资产状态', '所属法人', '所属部门', '使用人', '购买日期', '存放位置', '盘点完成']]
    if sign == 0:
        data_body = session['asset_inventory_export_all']
    else:
        data_body = session['asset_inventory_export_per']
    data = data_header + data_body
    print('Data header : ', data_header)
    print('Data body : ', data_body)
    file_name = u'资产盘点履历信息-all' if sign == 0 else u'资产盘点履历信息-' + str(page)
    print('Excel file name is : ', file_name)
    return excel.make_response_from_array(data, file_name=file_name, file_type='xlsx')