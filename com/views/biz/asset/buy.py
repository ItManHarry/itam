from flask import Blueprint, render_template, flash, redirect, url_for, request, session, current_app, jsonify
from flask_login import login_required, current_user
from com.models import BizAssetApply,BizAssetBuy
from com.plugins import db
from com.decorators import log_record
from com.forms.biz.asset.buy import BuySearchForm, BuyForm
import uuid, time
from datetime import datetime
from com.utils import gen_bill_no
bp_buy = Blueprint('buy', __name__)
@bp_buy.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查看资产购买信息')
def index():    
    form = BuySearchForm()
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        try:
            application_no = session['buy_view_search_application_no'] if session['buy_view_search_application_no'] else ''  # 申请单号
            buy_no = session['buy_view_search_buy_no'] if session['buy_view_search_buy_no'] else ''  # 购买号
            draft_no = session['buy_view_search_draft_no'] if session['buy_view_search_draft_no'] else ''  # 草案号
        except KeyError:
            application_no = ''
            buy_no = ''
            draft_no = ''
        form.application_no.data = application_no
        form.buy_no.data = buy_no
        form.draft_no.data = draft_no
    if request.method == 'POST':
        page = 1
        application_no = form.application_no.data
        buy_no = form.buy_no.data
        draft_no = form.draft_no.data
        session['buy_view_search_application_no'] = application_no
        session['buy_view_search_buy_no'] = buy_no
        session['buy_view_search_draft_no'] = draft_no
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']
    pagination = BizAssetBuy.query.filter(BizAssetBuy.bg_id == current_user.company_id).filter(BizAssetBuy.application_no.like('%'+application_no+'%'), BizAssetBuy.buy_no.like('%'+buy_no+'%'), BizAssetBuy.draft_no.like('%'+draft_no+'%')).order_by(BizAssetBuy.application_no).paginate(page, per_page)
    buys = pagination.items
    return render_template('biz/asset/buy/index.html', pagination=pagination, buys=buys, form=form)
@bp_buy.route('/add', methods=['GET', 'POST'])
@login_required
@log_record('新增资产购买信息')
def add():
    form = BuyForm()
    form.application_no.choices = [('00000000', '申请单号')] + [(apply.apply_no, apply.apply_no) for apply in BizAssetApply.query.order_by(BizAssetApply.createtime_loc.desc()).all()]
    if form.validate_on_submit():
        apply = BizAssetApply.query.filter(BizAssetApply.apply_no == form.application_no.data).first()
        buy = BizAssetBuy(id=uuid.uuid4().hex,
             application_no=form.application_no.data,
             application_id=apply.id,
             buy_no=gen_bill_no('BY'),
             draft_no=form.draft_no.data,
             bill_date=datetime.strptime(form.bill_date.data, '%Y-%m-%d'),
             receive_due_date=datetime.strptime(form.receive_due_date.data, '%Y-%m-%d'),
             total_price=form.total_price.data,
             bg_id=current_user.company_id,
             create_id = current_user.id
        )
        db.session.add(buy)
        db.session.commit()
        flash('资产购买添加成功！')
        return redirect(url_for('.index'))
    return render_template('biz/asset/buy/add.html', form=form)
@bp_buy.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
@log_record('修改资产购买信息')
def edit(id):
    form = BuyForm()
    buy = BizAssetBuy.query.get_or_404(id)
    form.application_no.choices = [(apply.apply_no, apply.apply_no) for apply in BizAssetApply.query.order_by(BizAssetApply.createtime_loc.desc()).all()]
    if request.method == 'GET':
        form.id.data = buy.id
        form.buy_no.data = buy.buy_no
        form.application_no.data = buy.application_no
        form.bill_date.data = buy.bill_date.strftime('%Y-%m-%d')
        form.draft_no.data = buy.draft_no
        form.total_price.data = buy.total_price
        form.receive_due_date.data = buy.receive_due_date.strftime('%Y-%m-%d')
        form.applicant.data = buy.application.applicant.name if buy.application else '-'
        form.asset_class.data = buy.application.class2.name if buy.application and buy.application.class2 else '-'
        form.asset_name.data = buy.application.class3.name if buy.application and buy.application.class3 else '-'
        form.brand.data = buy.application.brand.name if buy.application and buy.application.brand else '-'
        form.model.data = buy.application.model.name if buy.application and buy.application.model else '-'
    if form.validate_on_submit():
        apply = BizAssetApply.query.filter(BizAssetApply.apply_no == form.application_no.data).first()
        buy.application_id = apply.id
        buy.buy_no = form.buy_no.data
        buy.application_no = form.application_no.data
        buy.bill_date = datetime.strptime(form.bill_date.data, '%Y-%m-%d'),
        buy.draft_no = form.draft_no.data
        buy.total_price = form.total_price.data
        buy.receive_due_date = datetime.strptime(form.receive_due_date.data, '%Y-%m-%d'),
        buy.update_id = current_user.id
        buy.updatetime_utc = datetime.utcfromtimestamp(time.time())
        buy.updatetime_loc = datetime.fromtimestamp(time.time())
        db.session.commit()
        flash('资产购买更新成功！')
        return redirect(url_for('.index'))
    return render_template('biz/asset/buy/edit.html', form=form)