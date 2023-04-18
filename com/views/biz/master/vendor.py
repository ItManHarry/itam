from flask import Blueprint, render_template, flash, redirect, url_for, request,current_app,session,jsonify
from flask_login import login_required, current_user
from com.models import BizVendorMaster
from com.plugins import db
from com.decorators import log_record
from com.forms.biz.master.vendor import VendorSearchForm,VendorForm
import uuid, time
from datetime import datetime
bp_vendor = Blueprint('vendor', __name__)
@bp_vendor.route('/index', methods=['GET', 'POST'])
@login_required ###必须登录画面
@log_record('查看供应商信息')###记录操作日志
def index():
    form = VendorSearchForm()
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        try:
            code = session['vendor_view_search_code'] if session['vendor_view_search_code'] else ''  # 字典代码
            name = session['vendor_view_search_name'] if session['vendor_view_search_name'] else ''  # 字典名称
        except KeyError:
            code = ''
            name = ''
        form.code.data = code
        form.name.data = name
    if request.method == 'POST':
        page = 1
        code = form.code.data
        name = form.name.data
        session['vendor_view_search_code'] = code
        session['vendor_view_search_name'] = name
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']
    pagination = BizVendorMaster.query.filter(BizVendorMaster.bg_id==current_user.company_id).filter(BizVendorMaster.code.like('%'+code+'%'), BizVendorMaster.name.like('%'+name+'%')).order_by(BizVendorMaster.code).paginate(page, per_page)
    vendors = pagination.items

    return render_template('biz/master/vendor/index.html',pagination=pagination,form=form,vendors=vendors)
@bp_vendor.route('/add', methods=['GET', 'POST'])
@login_required ###必须登录画面
@log_record('新增供应商信息')###记录操作日志
def add():
    form = VendorForm()
    if form.validate_on_submit():
        vendor = BizVendorMaster(id=uuid.uuid4().hex,
                                 code=form.code.data.upper(),
                                 name=form.name.data,
                                 contact_person=form.contact_person.data,
                                 contact_phone=form.contact_phone.data,
                                 bg_id=current_user.company_id,
                                 create_id=current_user.id)
        db.session.add(vendor)
        db.session.commit()
        flash('供应商添加成功')
        return redirect(url_for('.index'))
    return render_template('biz/master/vendor/add.html',form=form)
@bp_vendor.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
@log_record('修改字典信息')
def edit(id):
    form = VendorForm()
    vendor = BizVendorMaster.query.get_or_404(id)
    if request.method =='GET':
        form.id.data = id
        form.code.data = vendor.code
        form.name.data = vendor.name
        form.contact_person.data = vendor.contact_person
        form.contact_phone.data = vendor.contact_phone
    if form.validate_on_submit():
        vendor.code = form.code.data
        vendor.name = form.name.data
        vendor.contact_person = form.contact_person.data
        vendor.contact_phone  = form.contact_phone.data
        vendor.update_id = current_user.id
        vendor.updatetime_utc = datetime.utcfromtimestamp(time.time())
        vendor.updatetime_loc = datetime.fromtimestamp(time.time())
        db.session.commit()
        flash('供应商修改成功！')
        return redirect(url_for('.index'))
    ###开始保存
    return render_template('biz/master/vendor/edit.html',form=form)
@bp_vendor.route('/get_vendor_info/<vendor_id>', methods=['POST'])
@login_required
@log_record('获取供应商联系人&联系电话信息')
def get_vendor_info(vendor_id):
    vendor = BizVendorMaster.query.get(vendor_id)
    return jsonify(contactor=vendor.contact_person, phone=vendor.contact_phone)