from flask import Blueprint, render_template, flash, redirect, url_for, request, session, current_app, jsonify
from flask_login import login_required, current_user
from com.models import BizAssetScrap, BizAssetMaster, BizStockAmount, BizAssetClass, BizBrandMaster
from com.plugins import db
from com.utils import get_options
from com.decorators import log_record
from com.forms.biz.report.stock_rpt import Stock_rptSearchForm
import flask_excel as excel
bp_stock_rpt = Blueprint('stock_rpt', __name__)
@bp_stock_rpt.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查看库存履历信息')
def index():
    form = Stock_rptSearchForm()
    form.class1.choices = [('0', '资产分类-All')]
    classes_1 = BizAssetClass.query.filter_by(grade=1).order_by(BizAssetClass.code).all()
    if classes_1:
        form.class1.choices += [(clazz.id, clazz.name) for clazz in classes_1]
    form.class2.choices = [('0', '二级级分类-All')]
    classes_2 = BizAssetClass.query.filter_by(grade=2).order_by(BizAssetClass.name).all()
    if classes_2:
        form.class2.choices += [(clazz.id, clazz.name) for clazz in classes_2]
    form.class3.choices = [('0', '三级级分类-All')]
    classes_3 = BizAssetClass.query.filter_by(grade=3).order_by(BizAssetClass.name).all()
    if classes_3:
        form.class3.choices += [(clazz.id, clazz.name) for clazz in classes_3]
    form.brands.choices = [('0', '品牌-All')]
    brands = BizBrandMaster.query.filter(BizBrandMaster.bg_id == current_user.company_id).order_by(
        BizBrandMaster.name).all()
    if brands:
        form.brands.choices += [(brand.id, brand.name) for brand in brands]
    if request.method == 'GET':
        page = request.args.get('page', type=int) if request.args.get('page') else 0
        # 如果是分页的话，就要取对应的搜索值，否则所有条件置空
        if page:  # 分页查看
            searched = False
            try:
                session['asset_stock_search_class2']
                searched = True
            except KeyError:
                print('NOT SEARCHED AT ALL!')
            form.class2.data = session['asset_stock_search_class2'] if searched else '0'
            form.brands.data = session['asset_stock_search_brand'] if searched else '0'
            # form.code.data = session['asset_report_search_code'] if searched else ''
            # form.sap_code.data = session['asset_report_search_sap_code'] if searched else ''
            if form.class2.data is None or form.class2.data == '0':
                form.class3.choices = [('0', '三级分类-All')]
            else:
                class_2 = BizAssetClass.query.get(form.class2.data)
                form.class3.choices = [('0', '三级分类-All')] + [(rel.child_class_id, rel.child_class.name) for rel in
                                                             class_2.get_child_class]
                form.class3.data = session['asset_stock_search_class3'] if searched else '0'
            if form.brands.data is None or form.brands.data == '0':
                form.models.choices = [('0', '型号-All')]
            else:
                brand = BizBrandMaster.query.get(form.brands.data)
                form.models.choices = [('0', '型号-All')] + [(model.id, model.name) for model in brand.models]
                form.models.data = session['asset_stock_search_model'] if searched else '0'
        else:  # 初始登录
            page = 1
            try:
                del session['asset_stock_search_class2']
            except KeyError:
                print('NOT SET THIS KEY!!!')
            form.class3.choices = [('0', '三级分类-All')]
            form.models.choices = [('0', '型号-All')]
            # form.code.data = ''
            # form.sap_code.data = ''
    if request.method == 'POST':
        page = 1
        first_search = True
        try:
            session['asset_stock_search_class1']
            first_search = False
        except KeyError:
            print('THIS IS FIRST TIME OF SEARCHING!')
        if form.class1.data == '0':
            form.class2.choices = [('0', '二级分类-All')]
            form.class2.data = '0'
            form.class3.choices = [('0', '三级分类-All')]
            form.class3.data = '0'
        else:
            class_1 = BizAssetClass.query.get(form.class1.data)
            form.class2.choices = [('0', '二级分类-All')] + [(rel.child_class_id, rel.child_class.name) for rel in class_1.get_child_class]
            if form.class2.data and form.class2.data != '0':
                class_2 = BizAssetClass.query.get(form.class2.data)
                form.class3.choices = [('0', '三级分类-All')] + [(rel.child_class_id, rel.child_class.name) for rel in class_2.get_child_class]
            else:
                form.class3.choices = [('0', '三级分类-All')]
            if not first_search:
                if session['asset_stock_search_class1'] is not None and session['asset_stock_search_class1'] != form.class1.data:
                    form.class2.data = '0'
                    form.class3.data = '0'
        if form.brands.data == '0':
            form.models.choices = [('0', '型号-All')]
            form.models.data = '0'
        else:
            brand = BizBrandMaster.query.get(form.brands.data)
            form.models.choices = [('0', '型号-All')] + [(model.id, model.name) for model in brand.models]
            if not first_search:
                if session['asset_stock_search_brand'] is not None and session['asset_stock_search_brand'] != form.brands.data:
                    form.models.data = '0'
        session['asset_stock_search_class1'] = form.class1.data
        session['asset_stock_search_class2'] = form.class2.data
        session['asset_stock_search_class3'] = form.class3.data
        session['asset_stock_search_brand'] = form.brands.data
        session['asset_stock_search_model'] = form.models.data
        # session['asset_report_search_code'] = form.code.data
        # session['asset_report_search_sap_code'] = form.sap_code.data
    # 搜索条件
    conditions = set()
    conditions.add(BizStockAmount.bg_id == current_user.company_id)
    # conditions.add(BizAssetMaster.code.like('%' + form.code.data + '%'))
    # conditions.add(BizAssetMaster.sap_code.like('%' + form.sap_code.data + '%'))
    if form.class1.data is not None and form.class1.data != '0':
        conditions.add(BizStockAmount.class1_id == form.class1.data)
    if form.class2.data is not None and form.class2.data != '0':
        conditions.add(BizStockAmount.class2_id == form.class2.data)
    if form.class3.data is not None and form.class3.data != '0':
        conditions.add(BizStockAmount.class3_id == form.class3.data)
    if form.brands.data is not None and form.brands.data != '0':
        conditions.add(BizStockAmount.brand_id == form.brands.data)
    if form.models.data is not None and form.models.data != '0':
        conditions.add(BizStockAmount.model_id == form.models.data)
    session['asset_stock_current_page'] = page
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']
    pagination = BizStockAmount.query.filter(*conditions).order_by(BizStockAmount.class1_id).order_by(BizStockAmount.class2_id).order_by(BizStockAmount.class3_id).order_by(BizStockAmount.brand_id).order_by(BizStockAmount.model_id).paginate(page, per_page)
    stocks = pagination.items
    stock_all = BizStockAmount.query.filter(*conditions).order_by(BizStockAmount.id).all()
    session['stock_export_all'] = [[stock.class1.name, stock.class2.name, stock.class3.name, stock.brand.name, stock.model.name, stock.amount] for stock in stock_all]     # 导出全部
    session['stock_export_per'] = [[stock.class1.name, stock.class2.name, stock.class3.name, stock.brand.name, stock.model.name, stock.amount] for stock in stocks]         # 导出当前
    # return render_template('biz/report/asset_rpt/index.html', form=form, assets=assets, pagination=pagination)
    return render_template('biz/report/stock_rpt/index.html',  form=form, stocks=stocks, pagination=pagination)
@bp_stock_rpt.route('/export/<int:sign>')
@login_required
@log_record('导出资产信息')
def export(sign):
    '''
    导出库存余额信息
    :param sign: 0:全部导出 1:导出当前页
    :return:
    '''
    excel.init_excel(current_app)
    page = session['asset_stock_current_page']
    data_header = [['资产分类', '二级分类', '三级分类', '品牌', '型号', '库存数量']]
    if sign == 0:
        data_body = session['stock_export_all']
    else:
        data_body = session['stock_export_per']
    data = data_header + data_body
    # print('Data header : ', data_header)
    # print('Data body : ', data_body)
    file_name = u'库存余额-all' if sign == 0 else u'库存余额-' + str(page)
    # print('Excel file name is : ', file_name)
    return excel.make_response_from_array(data, file_name=file_name, file_type='xlsx')