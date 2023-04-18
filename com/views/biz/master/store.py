from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from com.models import BizStoreMaster
from com.plugins import db
from com.decorators import log_record
from com.forms.biz.master.store import StoreForm
import uuid, time
from datetime import datetime
bp_store = Blueprint('store', __name__)
@bp_store.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查看仓库信息')
def index():
    stores = BizStoreMaster.query.filter(BizStoreMaster.bg_id == current_user.company_id).all()
    return render_template('biz/master/store/index.html',stores=stores)
@bp_store.route('/add', methods=['GET', 'POST'])
@login_required
@log_record('新增仓库信息')
def add():
    form = StoreForm()
    if form.validate_on_submit():
        store = BizStoreMaster(id=uuid.uuid4().hex,
                               code=form.code.data.upper(),
                               name=form.name.data,
                               place=form.place.data,
                               bg_id=current_user.company_id,
                               create_id=current_user.id
                               )
        db.session.add(store)
        db.session.commit()
        flash('仓库添加成功')
        return redirect(url_for('.index'))
    return render_template('biz/master/store/add.html', form=form)
@bp_store.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
@log_record('修改仓库信息')
def edit(id):
    form = StoreForm()
    store = BizStoreMaster.query.get_or_404(id)
    if request.method == 'GET':
        form.id.data = id
        form.code.data = store.code
        form.name.data = store.name
        form.place.data = store.place
    if form.validate_on_submit():
        store.code = form.code.data
        store.name = form.name.data
        store.place = form.place.data
        store.update_id = current_user.id
        store.updatetime_utc = datetime.utcfromtimestamp(time.time())
        store.updatetime_loc = datetime.fromtimestamp(time.time())
        db.session.commit()
        flash('仓库修改成功')
        return redirect(url_for('.index'))
    return render_template('biz/master/store/edit.html', form=form)
@bp_store.route('/get_stores', methods=['GET', 'POST'])
@login_required
@log_record('获取所有仓库信息')
def get_stores():
    stores = BizStoreMaster.query.order_by(BizStoreMaster.name).all()
    options = [(store.id, store.name) for store in stores]
    return jsonify(options=options)