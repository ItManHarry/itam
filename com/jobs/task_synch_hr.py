from com.plugins import scheduler, db
from com.models import SysUser, SysLog, BizDepartment, BizCompany, RelDepartment, BizEmployee
import uuid, time
from datetime import datetime
from com.infs.If_HR import get_employees, get_departments
def synchronize_hr_data_job():
    '''
    同步HR部门/雇员信息
    :return:
    '''
    # 使用上下文，否则报错
    with scheduler.app.app_context():
        app = scheduler.app
        user = SysUser.query.filter_by(user_id='admin').first()
        department_added = 0
        department_updated = 0
        employee_added = 0
        employee_updated = 0
        print('-' * 80)
        # 法人代码/ID字典
        company_map = {company.code: company.id for company in BizCompany.query.all()}
        start_time = time.time()
        print('开始同步部门信息')
        items = get_departments()
        department_total = len(items)
        for item in items:
            department = BizDepartment.query.filter_by(code=item.code).first()
            if department:
                #print('Department name : ', item.name, ', type : ', type(item.name))
                department.name = item.name,
                department.company_id = company_map[item.company_code]
                department.update_id = user.id
                department.updatetime_utc = datetime.utcfromtimestamp(time.time())
                department.updatetime_loc = datetime.fromtimestamp(time.time())
                department_updated += 1
            else:
                department = BizDepartment(
                    id=uuid.uuid4().hex,
                    code=item.code,
                    name=item.name,
                    company_id=company_map[item.company_code],
                    create_id=user.id
                )
                db.session.add(department)
                department_added += 1
            db.session.commit()
        print('同步部门信息完成，开始维护上级部门信息')
        # 批量删除关联关系后重新创建
        db.session.query(RelDepartment).delete()
        db.session.commit()
        # 重新创建上级部门信息
        for item in items:
            department = BizDepartment.query.filter_by(code=item.code).first()
            upper_department = BizDepartment.query.filter_by(code=item.upper_department_code).first()
            if department and upper_department:
                department.set_parent_department(upper_department)
        print('上级部门关系维护完成')
        print('开始同步雇员信息')
        # 部门代码/ID字典
        department_map = {department.code: department.id for department in BizDepartment.query.all()}
        items = get_employees()
        employee_total = len(items)
        print('雇员数量 : ', len(items))
        #count = 0
        for item in items:
            #count += 1
            employee = BizEmployee.query.filter_by(code=item.code).first()
            if employee:
                #print('Item(%d)执行雇员更新:职号(%s) --- ' %(count, item.code))
                employee.name = item.name
                employee.company_id = company_map[item.company_id]
                employee.department_id = department_map[item.department_code]
                employee.email = item.email
                employee.phone = item.phone
                if item[4] != '3':
                    employee.active = False
                employee.update_id = user.id
                employee.updatetime_utc = datetime.utcfromtimestamp(time.time())
                employee.updatetime_loc = datetime.fromtimestamp(time.time())
                employee_updated += 1
            else:
                #print('Item(%d)执行雇员新增:职号(%s) --- ' %(count, item[2]))
                employee = BizEmployee(
                    id=uuid.uuid4().hex,
                    code=item.code,
                    name=item.name,
                    active=True if item.status == '3' else False,
                    company_id=company_map[item.company_id],
                    department_id=department_map[item.department_code],
                    email=item.email,
                    phone=item.phone,
                    create_id=user.id
                )
                db.session.add(employee)
                employee_added += 1
            db.session.commit()
        print('雇员信息同步完成')
        finish_time = time.time()
        # 后台打印并写入日志
        log_str = 'HR组织人员信息同步完成:部门信息总计{}条,新增{}条,更新{}条;雇员共计{}条,新增{}条,更新{}条;共耗时{:.2f}秒!'.format(department_total,
                                                                                              department_added,
                                                                                              department_updated,
                                                                                              employee_total,
                                                                                              employee_added,
                                                                                              employee_updated,
                                                                                              finish_time - start_time)
        print(log_str)
        # 写入日志
        user = SysUser.query.filter_by(user_id='admin').first()
        log = SysLog(id=uuid.uuid4().hex, url='null', operation=log_str, create_id=user.id, user_id=user.id)
        db.session.add(log)
        db.session.commit()