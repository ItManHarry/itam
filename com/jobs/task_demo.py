from pm.plugins import scheduler, db
from pm.models import SysUser, SysLog
import uuid
from pm.infs.If_HR import get_employees
def synch_demo(a, b):
    # 使用上下文，否则报错
    with scheduler.app.app_context():
        app = scheduler.app
        print('Config value is : ', app.config['SECRET_KEY'])
        print('Parameter a is %s b is %s' % (a, b))
        print('User total is : ', len(SysUser.query.all()))
        print('-' * 80)
        employees = get_employees()
        for employee in employees:
            print(employee)
        print('-' * 80)
        # 写入日志
        user = SysUser.query.filter_by(user_id='admin').first()
        log = SysLog(id=uuid.uuid4().hex, url='null', operation='Synchronize HR data successfully', create_id=user.id,
                     user_id=user.id)
        db.session.add(log)
        db.session.commit()