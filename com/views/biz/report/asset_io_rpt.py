from flask import Blueprint, render_template, current_app, jsonify, session, request
from flask_login import login_required, current_user
from com.models import BizAssetClass, BizBrandMaster, BizStockHistory
from com.decorators import log_record
from com.utils import get_options
from com.forms.biz.report.asset_io_rpt import SearchForm
import flask_excel as excel
bp_asset_io_rpt = Blueprint('asset_io_rpt', __name__)
@bp_asset_io_rpt.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查看资产报表')
def index():
    form = SearchForm()
    # classes_1 = BizAssetClass.query.filter(BizAssetClass.code._in('01', '02'), BizAssetClass.bg_id == current_user.company_id).order_by(BizStockHistory.code).all()
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
    form.io_class.choices = [('0', '出入库类型-All')] + get_options('D010')
    if request.method == 'GET':
        page = request.args.get('page', type=int) if request.args.get('page') else 0
        # 如果是分页的话，就要取对应的搜索值，否则所有条件置空
        if page: # 分页查看
            searched = False
            try:
                session['asset_io_report_search_class2']
                searched = True
            except KeyError:
                print('NOT SEARCHED AT ALL!')
            form.class2.data = session['asset_io_report_search_class2'] if searched else '0'
            form.brands.data = session['asset_io_report_search_brand'] if searched else '0'
            form.code.data = session['asset_io_report_search_code'] if searched else ''
            form.sap_code.data = session['asset_io_report_search_sap_code'] if searched else ''
            form.io_class.data = session['asset_io_report_search_class'] if searched else '0'
            if form.class2.data is None or form.class2.data == '0':
                form.class3.choices = [('0', '资产名称-All')]
            else:
                class_2 = BizAssetClass.query.get(form.class2.data)
                form.class3.choices = [('0', '资产名称-All')]+[(rel.child_class_id, rel.child_class.name) for rel in class_2.get_child_class]
                form.class3.data = session['asset_io_report_search_class3'] if searched else '0'
            if form.brands.data is None or form.brands.data == '0':
                form.models.choices = [('0', '型号-All')]
            else:
                brand = BizBrandMaster.query.get(form.brands.data)
                form.models.choices = [('0', '型号-All')]+[(model.id, model.name) for model in brand.models]
                form.models.data = session['asset_io_report_search_model'] if searched else '0'
        else: # 初始登录
            page = 1
            try:
                del session['asset_io_report_search_class2']
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
            session['asset_io_report_search_class2']
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
                if session['asset_io_report_search_class2'] is not None and session['asset_io_report_search_class2'] != form.class2.data:
                    form.class3.data = '0'
        if form.brands.data == '0':
            form.models.choices = [('0', '型号-All')]
            form.models.data = '0'
        else:
            brand = BizBrandMaster.query.get(form.brands.data)
            form.models.choices = [('0', '型号-All')] + [(model.id, model.name) for model in brand.models]
            if not first_search:
                if session['asset_io_report_search_brand'] is not None and session['asset_io_report_search_brand'] != form.brands.data:
                    form.models.data = '0'
        session['asset_io_report_search_class2'] = form.class2.data
        session['asset_io_report_search_class3'] = form.class3.data
        session['asset_io_report_search_brand'] = form.brands.data
        session['asset_io_report_search_model'] = form.models.data
        session['asset_io_report_search_code'] = form.code.data
        session['asset_io_report_search_sap_code'] = form.sap_code.data
        session['asset_io_report_search_class'] = form.io_class.data
    # 搜索条件
    print('Asset code is {}, sap code is {}.'.format(form.code.data, form.sap_code.data))
    search_all = {}
    search_all['class2'] = '0'
    search_all['class3'] = '0'
    search_all['brands'] = '0'
    search_all['models'] = '0'
    search_all['code'] = form.code.data
    search_all['sap_code'] = ''
    search_all['io_class'] = '0'
    if form.sap_code.data.strip():
        search_all['sap_code'] = form.sap_code.data
    if form.class2.data is not None and form.class2.data != '0':
        search_all['class2'] = form.class2.data
    if form.class3.data is not None and form.class3.data != '0':
        search_all['class3'] = form.class3.data
    if form.brands.data is not None and form.brands.data != '0':
        search_all['brands'] = form.brands.data
    if form.models.data is not None and form.models.data != '0':
        search_all['models'] = form.models.data
    if form.io_class.data is not None and form.io_class.data != '0':
        search_all['io_class'] = form.io_class.data
    conditions = get_condition_set(search_all)
    session['asset_io_report_current_page'] = page
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']
    pagination = BizStockHistory.query.filter(*conditions).order_by(BizStockHistory.asset_id).paginate(page, per_page)
    histories = pagination.items
    session['asset_io_export_all'] = search_all
    session['asset_io_export_per'] = [[history.asset.class3.name, history.asset.code, history.asset.sap_code, history.asset.brand.name, history.asset.model.name, history.asset.vendor.name, history.asset.user.name if history.asset.user else '', history.io_class.display if history.io_class else '', history.amount] for history in histories]      # 导出当前
    return render_template('biz/report/asset_io_rpt/index.html', form=form, histories=histories, pagination=pagination)
@bp_asset_io_rpt.route('/export/<int:sign>')
@login_required
@log_record('导出出入库履历信息')
def export(sign):
    '''
    导出出入库履历信息
    :param sign: 0:全部导出 1:导出当前页
    :return:
    '''
    excel.init_excel(current_app)
    page = session['asset_io_report_current_page']
    data_header = [['资产名称', '资产编号', 'SAP资产编号', '品牌', '型号', '供应商', '使用者', '出入库类型', '出入库数量']]
    if sign == 0:
        search_all = session['asset_io_export_all']
        conditions = get_condition_set(search_all)
        histories_all = BizStockHistory.query.filter(*conditions).order_by(BizStockHistory.asset_id).all()
        data_body = [[history.asset.class3.name, history.asset.code, history.asset.sap_code, history.asset.brand.name, history.asset.model.name, history.asset.vendor.name, history.asset.user.name if history.asset.user else '', history.io_class.display if history.io_class else '', history.amount] for history in histories_all]  # 导出全部
    else:
        data_body = session['asset_io_export_per']
    data = data_header + data_body
    print('Data header : ', data_header)
    print('Data body : ', data_body)
    file_name = u'资产出入库履历信息-all' if sign == 0 else u'资产出入库履历信息-' + str(page)
    print('Excel file name is : ', file_name)
    return excel.make_response_from_array(data, file_name=file_name, file_type='xlsx')
def get_condition_set(cm):
    '''
    获取查询条件
    :param cm:
    :return:
    '''
    conditions = set()
    conditions.add(BizStockHistory.bg_id == current_user.company_id)
    conditions.add(BizStockHistory.code.like('%' + cm['code'] + '%'))
    if cm['sap_code']:
        conditions.add(BizStockHistory.sap_code.like('%' + cm['sap_code'] + '%'))
    if cm['class2'] != '0':
        conditions.add(BizStockHistory.class2_id == cm['class2'])
    if cm['class3'] != '0':
        conditions.add(BizStockHistory.class3_id == cm['class3'])
    if cm['brands'] != '0':
        conditions.add(BizStockHistory.brand_id == cm['brands'])
    if cm['models'] != '0':
        conditions.add(BizStockHistory.model_id == cm['models'])
    if cm['io_class'] != '0':
        conditions.add(BizStockHistory.io_class_id == cm['io_class'])
    return conditions