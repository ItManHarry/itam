from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from com.models import BizEnterprise, BizCompany, BizDepartment
from com.plugins import db
from com.decorators import log_record
from com.forms.biz.organization.company import CompanyForm, CompanySearchForm
import uuid, time
from datetime import datetime
bp_company = Blueprint('company', __name__)
@bp_company.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查看法人信息')
def index():
    form = CompanySearchForm()
    enterprises, enterprise_options = get_enterprises()
    form.enterprise.choices = enterprise_options
    if request.method == 'GET':
        enterprise = enterprises[0] if enterprises else None
    if request.method == 'POST':
        enterprise = BizEnterprise.query.get(form.enterprise.data)
    if enterprise:
        companies = BizCompany.query.with_parent(enterprise).order_by(BizCompany.name).all()
    else:
        companies = BizCompany.query.order_by(BizCompany.name).all()
    return render_template('biz/organization/company/index.html', companies=companies, form=form)
@bp_company.route('/add', methods=['GET', 'POST'])
@login_required
@log_record('新增法人信息')
def add():
    form = CompanyForm()
    form.enterprise.choices = get_enterprises()[1]
    if form.validate_on_submit():
        company = BizCompany(
            id=uuid.uuid4().hex,
            code=form.code.data.upper(),
            name=form.name.data,
            enterprise_id=form.enterprise.data,
            create_id=current_user.id
        )
        db.session.add(company)
        db.session.commit()
        flash('法人新增成功!')
        return redirect(url_for('.index'))
    return render_template('biz/organization/company/add.html', form=form)
@bp_company.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
@log_record('编辑法人信息')
def edit(id):
    form = CompanyForm()
    form.enterprise.choices = get_enterprises()[1]
    company = BizCompany.query.get_or_404(id)
    if request.method == 'GET':
        form.id.data = company.id
        form.code.data = company.code
        form.name.data = company.name
        form.enterprise.data = company.enterprise_id
    if form.validate_on_submit():
        company.code = form.code.data.upper()
        company.name = form.name.data
        company.enterprise_id = form.enterprise.data
        company.update_id = current_user.id
        company.updatetime_utc = datetime.utcfromtimestamp(time.time())
        company.updatetime_loc = datetime.fromtimestamp(time.time())
        db.session.commit()
        flash('法人修改成功！')
        return redirect(url_for('.index'))
    return render_template('biz/organization/company/edit.html', form=form)
def get_enterprises():
    enterprises = BizEnterprise.query.order_by(BizEnterprise.code.desc()).all()
    enterprise_options = []
    for enterprise in enterprises:
        enterprise_options.append((enterprise.id, enterprise.name))
    return (enterprises, enterprise_options)
@bp_company.route('/get_departments/<company_id>', methods=['POST'])
@login_required
@log_record('获取法人下的部门信息')
def get_departments(company_id):
    company = BizCompany.query.get(company_id)
    return jsonify(departments=[(department.id, department.name) for department in BizDepartment.query.with_parent(company).order_by(BizDepartment.name).all()])