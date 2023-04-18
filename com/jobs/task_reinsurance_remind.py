from com.plugins import scheduler
from com.models import BizEmailConfig, BizAssetMaint
from time import time
from datetime import datetime, date, timedelta
from com.email import send_mail

def reinsurance_remind_job():
    '''
    维保到期提醒（提前30天）
    :return:
    '''
    # 使用上下文，否则报错
    with scheduler.app.app_context():
        today = datetime.strptime(date.today().strftime('%Y-%m-%d'), '%Y-%m-%d')
        # 获取即将30天维保到期的记录
        ams = BizAssetMaint.query.filter(BizAssetMaint.expire_date >= date.today(), BizAssetMaint.expire_date <= date.today() + timedelta(days=30), BizAssetMaint.check == True).all()
        start_time = time()
        if ams:
            days = {}  # 维保到期字典 key:资产ID， value:到期天数
            for am in ams:
                expire_date = datetime.strptime(am.expire_date.strftime('%Y-%m-%d'), '%Y-%m-%d')
                days_delta = (expire_date - today).days
                days[am.master.id] = days_delta
            for key, value in days.items():
                print('资产ID:{}, 到期时间:{}'.format(key, value))
            # 发送邮件
            ec = BizEmailConfig.query.filter_by(code='MT001').first()
            to = ec.email_to.split(',') if ec.email_to else []
            cc = ec.email_cc.split(',') if ec.email_cc else []
            if to:
                send_mail(subject='维保到期提醒', to=to, cc=cc, template='emails/asset_reinsurance_remind', ams=ams, days=days)
        end_time = time()
        print('维保到期提醒任务执行完成，耗时{:.1f}秒！'.format(end_time - start_time))