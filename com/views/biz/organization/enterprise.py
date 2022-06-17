from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from com.models import BizEnterprise
from com.plugins import db
from com.decorators import log_record
from com.forms.biz.organization.enterprise import EnterpriseForm
import uuid, time
from datetime import datetime
bp_enterprise = Blueprint('enterprise', __name__)
@bp_enterprise.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查看事业处信息')
def index():
    enterprises = BizEnterprise.query.order_by(BizEnterprise.name).all()
    return render_template('biz/organization/enterprise/index.html', enterprises=enterprises)
@bp_enterprise.route('/add', methods=['GET', 'POST'])
@login_required
@log_record('新增事业处信息')
def add():
    form = EnterpriseForm()
    if form.validate_on_submit():
        enterprise = BizEnterprise(
            id=uuid.uuid4().hex,
            code=form.code.data.upper(),
            name=form.name.data,
            create_id=current_user.id
        )
        db.session.add(enterprise)
        db.session.commit()
        flash('事业处新增成功!')
        return redirect(url_for('.index'))
    return render_template('biz/organization/enterprise/add.html', form=form)
@bp_enterprise.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
@log_record('编辑事业处信息')
def edit(id):
    form = EnterpriseForm()
    enterprise = BizEnterprise.query.get_or_404(id)
    if request.method == 'GET':
        form.id.data = enterprise.id
        form.code.data = enterprise.code
        form.name.data = enterprise.name
    if form.validate_on_submit():
        enterprise.code = form.code.data.upper()
        enterprise.name = form.name.data
        enterprise.update_id = current_user.id
        enterprise.updatetime_utc = datetime.utcfromtimestamp(time.time())
        enterprise.updatetime_loc = datetime.fromtimestamp(time.time())
        db.session.commit()
        flash('事业处修改成功！')
        return redirect(url_for('.index'))
    return render_template('biz/organization/enterprise/edit.html', form=form)
@bp_enterprise.route('/get_companies/<enterprise_id>', methods=['POST'])
def get_companies(enterprise_id):
    enterprise = BizEnterprise.query.get(enterprise_id)
    companies = enterprise.companies
    company_options = []
    for company in companies:
        company_options.append((company.id, company.name))
    return jsonify(companies=company_options)
