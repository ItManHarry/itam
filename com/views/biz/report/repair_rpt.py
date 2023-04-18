from flask import Blueprint, render_template, flash, redirect, url_for, request, session, current_app, jsonify
from flask_login import login_required, current_user
from com.models import BizAssetRepair, BizAssetMaster
from com.plugins import db
from com.utils import get_options
from com.decorators import log_record
from com.forms.biz.report.repair_rpt import Repair_rptSearchForm
import flask_excel as excel
bp_repair_rpt = Blueprint('repair_rpt', __name__)
@bp_repair_rpt.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查看资产维修信息')
def index():    
    form = Repair_rptSearchForm()
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        try:
            asset_no = session['repair_rpt_view_search_asset_no'] if session['repair_rpt_view_search_asset_no'] else ''  # 资产编号
            repair_no = session['repair_rpt_view_search_repair_no'] if session['repair_rpt_view_search_repair_no'] else ''  # 维修单号
            check_year = session['repair_rpt_view_search_check_year'] if session['repair_rpt_view_search_check_year'] else ''  # 维修年度

        except KeyError:
            asset_no = ''
            repair_no = ''
            check_year = ''

        form.asset_no.data = asset_no
        form.repair_no.data = repair_no
        form.check_year.data = check_year

    if request.method == 'POST':
        page = 1
        asset_no = form.asset_no.data
        repair_no = form.repair_no.data
        check_year = form.check_year.data

        session['repair_rpt_view_search_asset_no'] = asset_no
        session['repair_rpt_view_search_repair_no'] = repair_no
        session['repair_rpt_view_search_check_year'] = check_year
    session['repair_rpt_current_page'] = page
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']
    assets = BizAssetMaster.query.filter(BizAssetMaster.code.like('%'+asset_no+'%')).all()
    asset_ids = [asset.id for asset in assets]
    pagination = BizAssetRepair.query.filter(BizAssetRepair.bg_id == current_user.company_id).filter(BizAssetRepair.repair_no.like('%'+repair_no+'%')).filter(BizAssetRepair.asset_id.in_(asset_ids)).filter(BizAssetRepair.createtime_loc.like('%'+check_year+'%')).order_by(BizAssetRepair.repair_no).paginate(page, per_page)
    repairs = pagination.items
    repair_types = get_options('D006')  # 维修类型
    repair_states = get_options('D007')  # 维修状态
    return render_template('biz/report/repair_rpt/index.html', pagination=pagination, repairs=repairs, form=form, repair_types=repair_types, repair_states=repair_states)

@bp_repair_rpt.route('/export/<int:sign>')
@login_required
@log_record('导出资产维修信息')
def export(sign):
    '''
    导出资产维修信息
    :param sign: 0:全部导出 1:导出当前页
    :return:
    '''
    excel.init_excel(current_app)
    page = session['repair_rpt_current_page']
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']
    data_header = [['法人', '部门', '申请Draft', '接收日期', '使用担当', '物料类型', '物料状态', '品牌', '型号', '维修Draft', '订单日期', '维修费', '处理担当', '资产编号', '资产名称', '维修单号', '维修类型', '搬出日期', '预计完成日期', '预计搬入日期', '实际完成日期', '实际搬入日期', '维修状态']]
    data_body = []
    try:
        beforeSearch = False if session['repair_rpt_view_search_asset_no'] or session['repair_rpt_view_search_repair_no'] else True
    except KeyError:
        beforeSearch = True
    if beforeSearch:
        repairs = BizAssetRepair.query.order_by(BizAssetRepair.repair_no).all() if sign == 0 else BizAssetRepair.query.order_by(BizAssetRepair.repair_no).paginate(page, per_page).items
    else:
        asset_no = session['repair_rpt_view_search_asset_no'] if session['repair_rpt_view_search_asset_no'] else ''  # 资产编号
        repair_no = session['repair_rpt_view_search_repair_no'] if session['repair_rpt_view_search_repair_no'] else ''  # 维修单号
        check_year = session['repair_rpt_view_search_check_year'] if session['repair_rpt_view_search_check_year'] else ''  # 维修年度
        assets = BizAssetMaster.query.filter(BizAssetMaster.code.like('%' + asset_no + '%')).all()
        asset_ids = [asset.id for asset in assets]
        repairs = BizAssetRepair.query.filter(BizAssetRepair.bg_id == current_user.company_id).filter(
            BizAssetRepair.repair_no.like('%' + repair_no + '%')).filter(
            BizAssetRepair.asset_id.in_(asset_ids)).filter(BizAssetRepair.createtime_loc.like('%'+check_year+'%')).order_by(BizAssetRepair.repair_no).all() if sign == 0 else BizAssetRepair.query.filter(BizAssetRepair.bg_id == current_user.company_id).filter(
            BizAssetRepair.repair_no.like('%' + repair_no + '%')).filter(
            BizAssetRepair.asset_id.in_(asset_ids)).filter(BizAssetRepair.createtime_loc.like('%'+check_year+'%')).order_by(BizAssetRepair.repair_no).paginate(page, per_page).items

    for repair in repairs:
        data_body.append([repair.asset.user.company.name if repair.asset.user else '', repair.asset.department.name if repair.asset.department else '', repair.request_draft if repair.request_draft else '', repair.request_accept_dt if repair.request_accept_dt else '', repair.asset.user.name if repair.asset.user else '', repair.asset.class2.name, repair.asset.status.display, repair.asset.brand.name, repair.asset.model.name, repair.repair_draft if repair.repair_draft else '', repair.createtime_loc.strftime('%Y-%m-%d') if repair.createtime_loc else '', repair.fee if repair.fee else '', repair.repair_handler.name if repair.repair_handler else '', repair.asset.code, repair.asset.class3.name, repair.repair_no, repair.repair_type.display, repair.out_date if repair.out_date else '', repair.pre_finish_date if repair.pre_finish_date else '', repair.pre_in_date if repair.pre_in_date else '', repair.rel_finish_date if repair.rel_finish_date else '', repair.real_in_date if repair.real_in_date else '', repair.repair_state.display])
    data = data_header + data_body
    print('Data header : ', data_header)
    print('Data body : ', data_body)
    file_name = u'资产维修信息-all' if sign == 0 else u'资产维修信息-' + str(page)
    print('Excel file name is : ', file_name)
    return excel.make_response_from_array(data, file_name=file_name, file_type='xlsx')
@bp_repair_rpt.route('/info/<repair_id>', methods=['POST'])
@login_required
@log_record('获取当前资产维修信息')
def info(repair_id):

    repair = BizAssetRepair.query.get(repair_id)
    print('Repair id ', repair.pre_finish_date.strftime('%Y-%m-%d'))
    return jsonify(repair_no=repair.repair_no, pre_finish_date=repair.pre_finish_date.strftime('%Y-%m-%d'), rel_finish_date=repair.rel_finish_date.strftime('%Y-%m-%d') if repair.rel_finish_date else '', repair_type=repair.repair_type_id, repair_state=repair.repair_state_id, fee=repair.fee, out_date=repair.out_date.strftime('%Y-%m-%d') if repair.out_date else '', pre_in_date=repair.pre_in_date.strftime('%Y-%m-%d') if repair.pre_in_date else '', real_in_date=repair.real_in_date.strftime('%Y-%m-%d') if repair.real_in_date else '')