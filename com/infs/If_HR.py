import pymssql
from flask import current_app
from collections import namedtuple
from com.email import send_mail
from datetime import date
def get_connection():
    connection = pymssql.connect(server=current_app.config['HR_SERVER'],
                              user=current_app.config['HR_USER'],
                              password=current_app.config['HR_PASSWORD'],
                              database=current_app.config['HR_DATABASE'])
    return connection
def get_departments():
    '''
        获取HR部门信息,过滤条件如下：
            获取HR部门信息：所属法人(HDICC/HDICI/HDCFL/HDISD)
        同步逻辑如下：
            判断是否存在：如果存在更新，不存在则新增
        :return:
    '''
    try:
        connection = get_connection()
        cursor = connection.cursor()
        if cursor:
            print('HR数据库MS SQLServer连接成功......')
        else:
            print('HR数据库MS SQLServer连接失败......')
        sql = '''
           select rootorgunitid     --法人代码
               ,upperorgunitid      --上级部门代码    
               ,orgunitid           --部门代码
               ,DeptShortName_ZH    --部门名称
           from viewghrisdeptmaster2
           where 1 = 1
           and rootorgunitid <>upperorgunitid
           and upperorgunitid <> '03000001'
           and rootorgunitid in ('01920601','01920773','01920052','01920000')        
       '''
        cursor.execute(sql)
        departments = []
        Department = namedtuple('Department', ['company_code', 'upper_department_code', 'code', 'name'])
        print('-' * 80)
        for row in cursor:
            departments.append(Department(*row))
        cursor.close()
        connection.close()
    except:
        send_mail(subject='IT资产管理系统接口异常通知', to=['guoqian.cheng@hyundai-di.com'], cc=[], template='email/inf_remind',
          inf_name='HR组织信息数据同步', remind_date=date.today().strftime('%Y-%m-%d'))
    return tuple(departments)
def get_employees():
    '''
        获取HR人员信息,过滤条件如下：
            1. 所属部门不为空
            2. AD账号不为空
            3. 所属法人：HDICC/HDICI/HDCFL/HDISD
            4. 状态不为3的置为停用状态
        同步逻辑如下：
            判断是否存在：存在更新，不存在则新增
        :return:
    '''
    try:
        connection = get_connection()
        cursor = connection.cursor()
        if cursor:
            print('MS SQL 连接成功......')
        else:
            print('MS SQL 连接失败......')
        sql = '''
            select 
                b.rootorgunitid as company_id           --法人代码
                ,a.orgunitid as department_code         --部门代码            
                ,a.userid as employee_code              --雇员职号
                ,a.name_zh as employee_name             --雇员姓名
                ,a.employeestatus as employee_status    --在职状态
                ,a.mail as employee_email               --邮箱地址
                ,a.mobilenumber as employee_phone       --电话号码
            from viewghrisusermaster2_china a
            left join viewghrisdeptmaster2 b on a.orgunitid = b.orgunitid
            where 1 = 1
            and a.orgunitid is not null
            and a.userid <> '' 
            and b.rootorgunitid in ('01920601','01920773','01920052','01920000')
        '''
        cursor.execute(sql)
        employees = []
        Employee = namedtuple('Employee', ['company_id', 'department_code', 'code', 'name', 'status', 'email', 'phone'])
        print('-' * 80)
        for row in cursor:
            employees.append(Employee(*row))
        cursor.close()
        connection.close()
    except:
        send_mail(subject='IT资产管理接口异常通知', to=['guoqian.cheng@hyundai-di.com'], cc=[], template='email/inf_remind',
                  inf_name='HR雇员信息数据同步', remind_date=date.today().strftime('%Y-%m-%d'))
    return tuple(employees)