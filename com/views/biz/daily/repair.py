from flask import Blueprint, render_template, flash, redirect, url_for, request, session, current_app, jsonify
from flask_login import login_required, current_user
from com.models import BizAssetRepair, BizAssetMaster, BizCompany
from com.utils import get_options
from com.decorators import log_record
from com.forms.biz.daily.repair import RepairSearchForm
import flask_excel as excel
bp_repair = Blueprint('repair', __name__)
@bp_repair.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查看资产维修信息')
def index():    
    form = RepairSearchForm()
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        try:
            asset_no = session['repair_view_search_asset_no'] if session['repair_view_search_asset_no'] else ''  # 资产编号
            repair_no = session['repair_view_search_repair_no'] if session['repair_view_search_repair_no'] else ''  # 维修单号
            request_by_id = session['repair_view_search_request_by_id'] if session['repair_view_search_request_by_id'] else ''  # 维修申请人
        except KeyError:
            asset_no = ''
            repair_no = ''
            request_by_id = ''
        form.asset_no.data = asset_no
        form.repair_no.data = repair_no
        form.request_by_id.data = request_by_id
    if request.method == 'POST':
        page = 1
        asset_no = form.asset_no.data
        repair_no = form.repair_no.data
        request_by_id = form.request_by_id.data
        session['repair_view_search_asset_no'] = asset_no
        session['repair_view_search_repair_no'] = repair_no
        session['repair_view_search_request_by_id'] = request_by_id
    session['repair_current_page'] = page
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']
    assets = BizAssetMaster.query.filter(BizAssetMaster.code.like('%'+asset_no+'%')).all()
    asset_ids = [asset.id for asset in assets]
    conditions = set()
    conditions.add(BizAssetRepair.bg_id == current_user.company_id)
    conditions.add(BizAssetRepair.asset_id.in_(asset_ids))
    conditions.add(BizAssetRepair.repair_no.like('%'+repair_no+'%'))
    if form.request_by_id.data:
        conditions.add(BizAssetRepair.requested_by_id == form.request_by_id.data)
    pagination = BizAssetRepair.query.filter(*conditions).order_by(BizAssetRepair.repair_no).paginate(page, per_page)
    repairs = pagination.items
    repair_types = get_options('D006')      # 维修类型
    repair_states = get_options('D007')     # 维修状态
    repair_parts = get_options('D011')      # 故障部位
    companies = BizCompany.query.order_by(BizCompany.name).all()
    return render_template('biz/daily/repair/index.html', pagination=pagination, repairs=repairs, form=form, repair_types=repair_types, repair_states=repair_states, repair_parts=repair_parts, companies=companies)

@bp_repair.route('/export/<int:sign>')
@login_required
@log_record('导出资产维修信息')
def export(sign):
    '''
    导出雇员信息
    :param sign: 0:全部导出 1:导出当前页
    :return:
    '''
    excel.init_excel(current_app)
    page = session['repair_current_page']
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']
    data_header = [['资产编号', '资产名称', '维修单号', '维修类型', '预计完成日期', '实际完成日期', '维修状态']]
    data_body = []
    try:
        beforeSearch = False if session['repair_view_search_asset_no'] or session['repair_view_search_repair_no'] else True
    except KeyError:
        beforeSearch = True
    if beforeSearch:
        repairs = BizAssetRepair.query.order_by(BizAssetRepair.repair_no).all() if sign == 0 else BizAssetRepair.query.order_by(BizAssetRepair.repair_no).paginate(page, per_page).items
    else:
        asset_no = session['repair_view_search_asset_no'] if session['repair_view_search_asset_no'] else ''  # 资产编号
        repair_no = session['repair_view_search_repair_no'] if session['repair_view_search_repair_no'] else ''  # 维修单号
        assets = BizAssetMaster.query.filter(BizAssetMaster.code.like('%' + asset_no + '%')).all()
        asset_ids = [asset.id for asset in assets]
        repairs = BizAssetRepair.query.filter(BizAssetRepair.bg_id == current_user.company_id).filter(
            BizAssetRepair.repair_no.like('%' + repair_no + '%')).filter(
            BizAssetRepair.asset_id.in_(asset_ids)).order_by(BizAssetRepair.repair_no).all() if sign == 0 else BizAssetRepair.query.filter(BizAssetRepair.bg_id == current_user.company_id).filter(
            BizAssetRepair.repair_no.like('%' + repair_no + '%')).filter(
            BizAssetRepair.asset_id.in_(asset_ids)).order_by(BizAssetRepair.repair_no).paginate(page, per_page).items

    for repair in repairs:
        data_body.append([repair.asset.code, repair.asset.class3.name, repair.repair_no, repair.repair_type.display, repair.pre_finish_date, repair.rel_finish_date if repair.rel_finish_date else '', repair.repair_state.display])
    data = data_header + data_body
    print('Data header : ', data_header)
    print('Data body : ', data_body)
    file_name = u'资产维修信息-all' if sign == 0 else u'资产维修信息-' + str(page)
    print('Excel file name is : ', file_name)
    return excel.make_response_from_array(data, file_name=file_name, file_type='xlsx')
@bp_repair.route('/info/<repair_id>', methods=['POST'])
@login_required
@log_record('获取当前资产维修信息')
def info(repair_id):
    repair = BizAssetRepair.query.get(repair_id)
    return jsonify(repair_no=repair.repair_no,
                   pre_finish_date=repair.pre_finish_date.strftime('%Y-%m-%d') if repair.pre_finish_date else '',
                   rel_finish_date=repair.rel_finish_date.strftime('%Y-%m-%d') if repair.rel_finish_date else '',
                   repair_type=repair.repair_type_id,
                   repair_state=repair.repair_state_id,
                   request_draft=repair.request_draft,
                   request_accept_dt=repair.request_accept_dt.strftime('%Y-%m-%d') if repair.request_accept_dt else '',
                   requested_by_id=repair.requested_by_id if repair.requested_by_id else '',
                   requested_by_nm='{}({})'.format(repair.requested_by.name, repair.requested_by.code) if repair.requested_by else '',
                   repair_draft=repair.repair_draft,
                   repair_handler_id=repair.repair_handler_id if repair.repair_handler_id else '',
                   repair_handler_nm='{}({})'.format(repair.repair_handler.name, repair.repair_handler.code) if repair.repair_handler_id else '',
                   fee=repair.fee,
                   out_date=repair.out_date.strftime('%Y-%m-%d') if repair.out_date else '',
                   pre_in_date=repair.pre_in_date.strftime('%Y-%m-%d') if repair.pre_in_date else '',
                   real_in_date=repair.real_in_date.strftime('%Y-%m-%d') if repair.real_in_date else '',
                   repair_part_id=repair.repair_part_id,
                   repair_content=repair.repair_content)