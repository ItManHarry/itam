from flask import Blueprint, url_for, request,redirect, jsonify, session, render_template, current_app, flash
from com.forms.biz.organization.employee import EmployeeForm, EmployeeSearchForm
from flask_login import login_required, current_user
from com.models import BizEmployee, BizDepartment
from com.plugins import db
from com.decorators import log_record
import uuid, time
from datetime import datetime
import flask_excel as excel
bp_employee = Blueprint('employee', __name__)
@bp_employee.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查看雇员清单')
def index():
    form = EmployeeSearchForm()
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        try:
            code = session['employee_view_search_code'] if session['employee_view_search_code'] else ''  # 组织代码
            name = session['employee_view_search_name'] if session['employee_view_search_name'] else ''  # 组织名称
        except KeyError:
            code = ''
            name = ''
        form.code.data = code
        form.name.data = name
    if request.method == 'POST':
        page = 1
        code = form.code.data
        name = form.name.data
        session['employee_view_search_code'] = code.strip()
        session['employee_view_search_name'] = name.strip()
    session['employee_current_page'] = page
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']
    # pagination = BizEmployee.query.filter(BizEmployee.code.like('%' + code.strip() + '%'), BizEmployee.name.like('%' + name.strip() + '%')).order_by(BizEmployee.name).paginate(page, per_page)
    if current_user.is_admin:
        pagination = BizEmployee.query.filter(BizEmployee.code.like('%'+code.strip()+'%'), BizEmployee.name.like('%'+name.strip()+'%')).order_by(BizEmployee.code).paginate(page, per_page)
    else:
        pagination = BizEmployee.query.with_parent(current_user.company).filter(BizEmployee.code.like('%' + code.strip() + '%'), BizEmployee.name.like('%' + name.strip() + '%')).order_by(BizEmployee.code).paginate(page, per_page)
    employees = pagination.items
    return render_template('biz/organization/employee/index.html', form=form, pagination=pagination, employees=employees)
@bp_employee.route('/add', methods=['GET', 'POST'])
@login_required
@log_record('新增雇员')
def add():
    form = EmployeeForm()
    departments, department_options = get_departments()
    form.department.choices = department_options
    form.company.data = current_user.company.id
    if form.validate_on_submit():
        employee = BizEmployee(
            id=uuid.uuid4().hex,
            code=form.code.data,
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            company_id=current_user.company.id,
            department_id=form.department.data,
            create_id=current_user.id
        )
        db.session.add(employee)
        db.session.commit()
        flash('雇员添加成功！')
        '''
        # 生成二维码
        from com.utils import gen_qrcode
        data = "{'code'='123456789', 'name'='Compute'}"
        gen_qrcode(current_app.config['QR_CODE_PATH']+'\\'+'test.png', data)
        '''
        return redirect(url_for('.index'))
    return render_template('biz/organization/employee/add.html', form=form)
@bp_employee.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
@log_record('修改雇员信息')
def edit(id):
    form = EmployeeForm()
    employee = BizEmployee.query.get_or_404(id)
    departments, department_options = get_departments()
    form.department.choices = department_options
    if request.method == 'GET':
        form.id.data = employee.id
        form.code.data = employee.code
        form.name.data = employee.name
        form.email.data = employee.email
        form.phone.data = employee.phone
        form.company.data = employee.company_id
        form.department.data = employee.department_id
    if form.validate_on_submit():
        employee.code = form.code.data.upper()
        employee.name = form.name.data
        employee.email = form.email.data
        employee.phone = form.phone.data
        employee.department_id = form.department.data
        employee.update_id = current_user.id
        employee.updatetime_utc = datetime.utcfromtimestamp(time.time())
        employee.updatetime_loc = datetime.fromtimestamp(time.time())
        db.session.commit()
        flash('雇员修改成功！')
        return redirect(url_for('.index'))
    return render_template('biz/organization/employee/edit.html', form=form)
@bp_employee.route('/status/<id>/<int:status>', methods=['POST'])
@log_record('更改部门状态')
def status(id, status):
    employee = BizEmployee.query.get_or_404(id)
    employee.active = True if status == 1 else False
    employee.update_id = current_user.id
    employee.updatetime_utc = datetime.utcfromtimestamp(time.time())
    employee.updatetime_loc = datetime.fromtimestamp(time.time())
    db.session.commit()
    return jsonify(code=1, message='状态更新成功!')
def get_departments():
    departments = BizDepartment.query.with_parent(current_user.company).order_by(BizDepartment.name).all()
    department_options = []
    for department in departments:
        department_options.append((department.id, department.name))
    return (departments, department_options)
@bp_employee.route('/export/<int:sign>')
@login_required
@log_record('导出雇员信息')
def export(sign):
    '''
    导出雇员信息
    :param sign: 0:全部导出 1:导出当前页
    :return:
    '''
    excel.init_excel(current_app)
    page = session['employee_current_page']
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']
    data_header = [['法人', '职号', '姓名', '部门', '邮箱', '电话', '状态']]
    data_body = []
    try:
        beforeSearch = False if session['employee_view_search_code'] or session['employee_view_search_name'] else True
    except KeyError:
        beforeSearch = True
    if beforeSearch:
        if current_user.is_admin:
            employees = BizEmployee.query.order_by(BizEmployee.code).all() if sign == 0 else BizEmployee.query.order_by(BizEmployee.code).paginate(page, per_page).items
        else:
            employees = BizEmployee.query.with_parent(current_user.company).order_by(BizEmployee.code).all() if sign == 0 else BizEmployee.query.with_parent(current_user.company).order_by(BizEmployee.code).paginate(page, per_page).items
    else:
        if current_user.is_admin:
            employees = BizEmployee.query.filter(BizEmployee.code.like('%' + session['employee_view_search_code'] + '%'), BizEmployee.name.like('%' + session['employee_view_search_name'] + '%')).order_by(BizEmployee.code).all() if sign == 0 else BizEmployee.query.filter(BizEmployee.code.like('%' + session['employee_view_search_code'] + '%'), BizEmployee.name.like('%' + session['employee_view_search_name'] + '%')).order_by(BizEmployee.code).paginate(page, per_page).items
        else:
            employees = BizEmployee.query.with_parent(current_user.company).filter(
                BizEmployee.code.like('%' + session['employee_view_search_code'] + '%'),
                BizEmployee.name.like('%' + session['employee_view_search_name'] + '%')).order_by(
                BizEmployee.code).all() if sign == 0 else BizEmployee.query.with_parent(current_user.company).filter(
                BizEmployee.code.like('%' + session['employee_view_search_code'] + '%'),
                BizEmployee.name.like('%' + session['employee_view_search_name'] + '%')).order_by(
                BizEmployee.code).paginate(page, per_page).items
    for employee in employees:
        data_body.append([employee.company.name, employee.code, employee.name, employee.department.name, employee.email if employee.email else '-', employee.phone if employee.phone else '-', '在职' if employee.active else '离职'])
    data = data_header + data_body
    print('Data header : ', data_header)
    print('Data body : ', data_body)
    file_name = u'雇员信息-all' if sign == 0 else u'雇员信息-' + str(page)
    print('Excel file name is : ', file_name)
    return excel.make_response_from_array(data, file_name=file_name, file_type='xlsx')