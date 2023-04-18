from com.plugins import scheduler
from com.models import BizEmailConfig, BizStockOut
from time import time
from datetime import datetime, date, timedelta
from com.email import send_mail

def borrow_remind_job():
    '''
    借用到期提醒
    :return:
    '''
    # 使用上下文，否则报错
    with scheduler.app.app_context():
        # today = datetime.strptime(date.today().strftime('%Y-%m-%d'), '%Y-%m-%d')
        # 获取借用今天到期的所有出库单(借用发放单)
        bills = BizStockOut.query.filter(BizStockOut.back_date == date.today()).all()
        start_time = time()
        if bills:
            # 发送邮件
            ec = BizEmailConfig.query.filter_by(code='MT002').first()
            to = ec.email_to.split(',') if ec.email_to else []
            cc = ec.email_cc.split(',') if ec.email_cc else []
            if to:
                send_mail(subject='借用到期提醒', to=to, cc=cc, template='emails/asset_borrow_remind', bills=bills)
        end_time = time()
        print('借用到期提醒任务执行完成，耗时{:.1f}秒！'.format(end_time - start_time))