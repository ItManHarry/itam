from flask import Blueprint, render_template, flash, redirect, url_for, request, session, current_app, jsonify
from flask_login import login_required, current_user
from com.models import BizAssetScrap, BizAssetMaster
from com.plugins import db
from com.utils import get_options
from com.decorators import log_record
from com.forms.biz.report.scrap_rpt import Scrap_rptSearchForm
import flask_excel as excel
bp_scrap_rpt = Blueprint('scrap_rpt', __name__)
@bp_scrap_rpt.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查看资产报废信息')
def index():
    form = Scrap_rptSearchForm()
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        try:
            asset_no = session['scrap_rpt_view_search_asset_no'] if session['scrap_rpt_view_search_asset_no'] else ''  # 资产编号
            scrap_no = session['scrap_rpt_view_search_scrap_no'] if session['scrap_rpt_view_search_scrap_no'] else ''  # 报废单号
            check_year = session['scrap_rpt_view_search_check_year'] if session['scrap_rpt_view_search_check_year'] else ''  # 报废年度
        except KeyError:
            asset_no = ''
            scrap_no = ''
            check_year = ''

        form.asset_no.data = asset_no
        form.scrap_no.data = scrap_no
        form.check_year.data = check_year

    if request.method == 'POST':
        page = 1
        asset_no = form.asset_no.data
        scrap_no = form.scrap_no.data
        check_year = form.check_year.data

        session['scrap_rpt_view_search_asset_no'] = asset_no
        session['scrap_rpt_view_search_scrap_no'] = scrap_no
        session['scrap_rpt_view_search_check_year'] = check_year
    session['scrap_rpt_current_page'] = page
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']
    assets = BizAssetMaster.query.filter(BizAssetMaster.code.like('%'+asset_no+'%')).all()
    asset_ids = [asset.id for asset in assets]
    pagination = BizAssetScrap.query.filter(BizAssetScrap.bg_id == current_user.company_id).filter(BizAssetScrap.scrap_no.like('%'+scrap_no+'%')).filter(BizAssetScrap.asset_id.in_(asset_ids)).filter(BizAssetScrap.finish_date.like('%'+check_year+'%')).order_by(BizAssetScrap.scrap_no).paginate(page, per_page)
    scraps = pagination.items
    scrap_reasons = get_options('D008')  # 报废原因
    scrap_states = get_options('D009')  # 报废状态
    return render_template('biz/report/scrap_rpt/index.html', pagination=pagination, scraps=scraps, form=form, scrap_reasons=scrap_reasons, scrap_states=scrap_states)

@bp_scrap_rpt.route('/export/<int:sign>')
@login_required
@log_record('导出资产报废信息')
def export(sign):
    '''
    导出资产报废信息
    :param sign: 0:全部导出 1:导出当前页
    :return:
    '''
    excel.init_excel(current_app)
    page = session['scrap_rpt_current_page']
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']

    data_header = [['法人', '报废年度', '物料类型', '品牌', '型号', '部门', '使用担当', '判定日期', '报废原因', '报废完成日', '资产编号', '资产名称', '报废单号', '判定人', '报废Draft号', 'SAP是否报废', '报废状态']]
    data_body = []
    try:
        beforeSearch = False if session['scrap_rpt_view_search_asset_no'] or session['scrap_rpt_view_search_scrap_no'] or session['scrap_rpt_view_search_check_year'] else True
    except KeyError:
        beforeSearch = True
    if beforeSearch:
        scraps = BizAssetScrap.query.order_by(BizAssetScrap.scrap_no).all() if sign == 0 else BizAssetScrap.query.order_by(BizAssetScrap.scrap_no).paginate(page, per_page).items
    else:
        asset_no = session['scrap_rpt_view_search_asset_no'] if session['scrap_rpt_view_search_asset_no'] else ''  # 资产编号
        scrap_no = session['scrap_rpt_view_search_scrap_no'] if session['scrap_rpt_view_search_scrap_no'] else ''  # 报废单号
        check_year = session['scrap_rpt_view_search_check_year'] if session['scrap_rpt_view_search_check_year'] else ''  # 报废年度
        assets = BizAssetMaster.query.filter(BizAssetMaster.code.like('%' + asset_no + '%')).all()
        asset_ids = [asset.id for asset in assets]
        scraps = BizAssetScrap.query.filter(BizAssetScrap.bg_id == current_user.company_id).filter(
            BizAssetScrap.scrap_no.like('%' + scrap_no + '%')).filter(
            BizAssetScrap.asset_id.in_(asset_ids)).filter(BizAssetScrap.finish_date.like('%'+check_year+'%')).order_by(BizAssetScrap.scrap_no).all() if sign == 0 else BizAssetScrap.query.filter(BizAssetScrap.bg_id == current_user.company_id).filter(
            BizAssetScrap.scrap_no.like('%' + scrap_no + '%')).filter(
            BizAssetScrap.asset_id.in_(asset_ids)).filter(BizAssetScrap.finish_date.like('%'+check_year+'%')).order_by(BizAssetScrap.scrap_no).paginate(page, per_page).items

    for scrap in scraps:
        data_body.append([scrap.asset.user.company.name if scrap.asset.user else '', scrap.finish_date.strftime('%Y年'), scrap.asset.class2.name, scrap.asset.brand.name, scrap.asset.model.name, scrap.asset.department.name if scrap.asset.department else '', scrap.asset.user.name if scrap.asset.user else '', scrap.scrap_date, scrap.scrap_reason.display, scrap.finish_date, scrap.asset.code, scrap.asset.class3.name, scrap.scrap_no, scrap.scraper.user_name if scrap.scraper else '', scrap.scrap_draft, '是' if scrap.sap_scrap else '否', scrap.scrap_state.display])
    data = data_header + data_body
    print('Data header : ', data_header)
    print('Data body : ', data_body)
    file_name = u'资产报废信息-all' if sign == 0 else u'资产报废信息-' + str(page)
    print('Excel file name is : ', file_name)
    return excel.make_response_from_array(data, file_name=file_name, file_type='xlsx')
@bp_scrap_rpt.route('/info/<scrap_id>', methods=['POST'])
@login_required
@log_record('获取当前资产报废信息')
def info(scrap_id):
    scrap = BizAssetScrap.query.get(scrap_id)
    return jsonify(scrap_no=scrap.scrap_no, scrap_date=scrap.scrap_date.strftime('%Y-%m-%d'), finish_date=scrap.finish_date.strftime('%Y-%m-%d') if scrap.finish_date else '', scrap_draft=scrap.scrap_draft, scrap_reason=scrap.scrap_reason_id, scrap_state=scrap.scrap_state_id, sap_scrap=scrap.sap_scrap)