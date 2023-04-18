'''
系统部门信息管理
'''
from flask import Blueprint, render_template, request, current_app, flash, redirect, url_for, jsonify, session
from flask_login import login_required, current_user
from com.models import BizDepartment, BizCompany, BizEnterprise, RelDepartment, BizEmployee
from com.plugins import db
from com.forms.biz.organization.department import DepartmentSearchForm, DepartmentForm
from com.decorators import log_record
from com.views.biz.organization.company import get_enterprises
import uuid, time
from datetime import datetime
bp_department = Blueprint('department', __name__)
@bp_department.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查询部门清单')
def index():
    form = DepartmentSearchForm()
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        try:
            code = session['department_view_search_code'] if session['department_view_search_code'] else ''  # 组织代码
            name = session['department_view_search_name'] if session['department_view_search_name'] else ''  # 组织名称
        except KeyError:
            code = ''
            name = ''
        form.code.data = code
        form.name.data = name
    if request.method == 'POST':
        page = 1
        code = form.code.data
        name = form.name.data
        session['department_view_search_code'] = code.strip()
        session['department_view_search_name'] = name.strip()
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']
    pagination = BizDepartment.query.filter(BizDepartment.code.like('%' + code.strip() + '%'), BizDepartment.name.like('%' + name.strip() + '%')).order_by( BizDepartment.code).paginate(page, per_page)
    '''
    if current_user.is_admin:
        pagination = BizDepartment.query.filter(BizDepartment.code.like('%'+code.strip()+'%'), BizDepartment.name.like('%'+name.strip()+'%')).order_by(BizDepartment.code).paginate(page, per_page)
    else:
        pagination = BizDepartment.query.with_parent(current_user.company).filter(BizDepartment.code.like('%' + code.strip() + '%'), BizDepartment.name.like('%' + name.strip() + '%')).order_by(BizDepartment.code).paginate(page, per_page)
    '''
    departments = pagination.items
    return render_template('biz/organization/department/index.html', pagination=pagination, departments=departments, form=form)
@bp_department.route('/add', methods=['GET', 'POST'])
@login_required
@log_record('新增部门信息')
def add():
    print('Request method is : ', request.method)
    form = DepartmentForm()
    enterprises, enterprise_options = get_enterprises()
    form.enterprise.choices = enterprise_options
    if not current_user.is_admin:
        form.enterprise.data = current_user.company.enterprise.id
        form.company_id.data = current_user.company.id
        form.company.data = current_user.company.name
    if form.validate_on_submit():
        department = BizDepartment(
            id=uuid.uuid4().hex,
            code=form.code.data.lower(),
            name=form.name.data,
            company_id=form.company_id.data if current_user.is_admin else current_user.company.id,
            create_id=current_user.id
        )
        db.session.add(department)
        db.session.commit()
        has_parent = form.has_parent.data
        if has_parent and form.parent_id.data is not None:
            department.set_parent_department(BizDepartment.query.get(form.parent_id.data))
        flash('部门信息添加成功！')
        return redirect(url_for('.index'))
    return render_template('biz/organization/department/add.html', form=form)
@bp_department.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
@log_record('修改部门信息')
def edit(id):
    form = DepartmentForm()
    enterprises, enterprise_options = get_enterprises()
    form.enterprise.choices = enterprise_options
    department = BizDepartment.query.get_or_404(id)
    if request.method == 'GET':
        form.id.data = department.id
        form.code.data = department.code
        form.name.data = department.name
        form.enterprise.data = department.company.enterprise.id
        form.company_id.data = department.company.id
        form.company.data = department.company.name
        parent = department.get_parent_department
        if parent:
            form.has_parent.data = True
            form.parent_id.data = parent.id
            form.parent.data = parent.name
    if form.validate_on_submit():
        department.code = form.code.data
        department.name = form.name.data
        department.company_id = form.company_id.data
        department.update_id = current_user.id
        department.updatetime_utc = datetime.utcfromtimestamp(time.time())
        department.updatetime_loc = datetime.fromtimestamp(time.time())
        db.session.commit()
        has_parent = form.has_parent.data
        if has_parent and form.parent_id.data is not None:
            department.set_parent_department(BizDepartment.query.get(form.parent_id.data))
        else:
            print('删除上级部门更新')
            parent_department = RelDepartment.query.filter_by(child_department_id=id).first()
            if parent_department:
                db.session.delete(parent_department)
                db.session.commit()
        flash('部门信息更新成功！')
        return redirect(url_for('.index', id=form.id.data))
    return render_template('biz/organization/department/edit.html', form=form)
# 递归获取子部门(多级部门)
def get_child_departments(parent, children):
    child_departments = parent.get_child_department
    if child_departments:
        for child in child_departments:
            children.append(child.child_department_id)
            get_child_departments(BizDepartment.query.get(child.child_department_id), children)
    else:
        return children
@bp_department.route('/status/<id>/<int:status>', methods=['POST'])
@log_record('更改部门状态')
def status(id, status):
    department = BizDepartment.query.get_or_404(id)
    department.active = True if status == 1 else False
    department.update_id = current_user.id
    department.updatetime_utc = datetime.utcfromtimestamp(time.time())
    department.updatetime_loc = datetime.fromtimestamp(time.time())
    db.session.commit()
    return jsonify(code=1, message='状态更新成功!')
def get_companies(enterprise):
    companies = BizCompany.query.with_parent(enterprise).order_by(BizCompany.name).all()
    company_options = []
    for company in companies:
        company_options.append((company.id, company.name))
    return (companies, company_options)
@bp_department.route('/companies/<enterprise_id>', methods = ['POST'])
@log_record('获取事业处法人信息')
def get_enterprise_companies(enterprise_id):
    all_companies = [('000000', '---请选择---')]
    enterprise = BizEnterprise.query.get(enterprise_id)
    print('Enterprise is : ', enterprise.name)
    _, companies = get_companies(enterprise)
    print('Companies are : ', companies)
    all_companies += companies
    return jsonify(all_companies)
@bp_department.route('/parents', methods = ['POST'])
@log_record('获取法人部门信息')
def get_parents():
    parent_departments = [('000000', '---请选择---')]
    params = request.get_json()
    action = params['action']
    company = BizCompany.query.get(params['company_id'])
    if action == 'add':
        departments = BizDepartment.query.with_parent(company).order_by(BizDepartment.code).all()
    if action == 'update':
        self_and_children = [params['department_id']]
        edit_department = BizDepartment.query.get(params['department_id'])
        get_child_departments(edit_department, self_and_children)  # 递归获取子部门及子子部门
        print('Self and child department ids : ', self_and_children)
        departments = BizDepartment.query.with_parent(edit_department.company).order_by(BizDepartment.code).all()
        for department in departments:
            if department.id not in self_and_children:
                parent_departments.append((department.id, department.name))
    for department in departments:
        parent_departments.append((department.id, department.name))
    return jsonify(parent_departments)
@bp_department.route('/get_employees/<department_id>', methods=['POST'])
@login_required
@log_record('获取部门下的雇员信息')
def get_employees(department_id):
    department = BizDepartment.query.get(department_id)
    return jsonify(employees=[(employee.id, employee.name, employee.code, employee.email) for employee in BizEmployee.query.with_parent(department).order_by(BizEmployee.name).all() if employee.active])