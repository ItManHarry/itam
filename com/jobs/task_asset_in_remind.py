from com.plugins import scheduler
from com.models import BizEmailConfig, BizAssetRepair
from time import time
from datetime import datetime, date, timedelta
from com.email import send_mail

def asset_in_remind_job():
    '''
    预计搬入到期提醒
    :return:
    '''
    # 使用上下文，否则报错
    with scheduler.app.app_context():
        # today = datetime.strptime(date.today().strftime('%Y-%m-%d'), '%Y-%m-%d')
        # 获取预计搬入的资产清单(实际搬入日期栏位为空)
        aps = BizAssetRepair.query.filter(BizAssetRepair.pre_in_date == date.today()).filter(BizAssetRepair.real_in_date == None).all()
        start_time = time()
        if aps:
            # 发送邮件
            ec = BizEmailConfig.query.filter_by(code='MT003').first()
            to = ec.email_to.split(',') if ec.email_to else []
            cc = ec.email_cc.split(',') if ec.email_cc else []
            if to:
                send_mail(subject='预计搬入到期提醒', to=to, cc=cc, template='emails/asset_in_remind', aps=aps)
        end_time = time()
        print('预计搬入到期提醒任务执行完成，耗时{:.1f}秒！'.format(end_time - start_time))