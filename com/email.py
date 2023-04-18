from flask import current_app, render_template
from flask_mail import Message
from com.plugins import mail, db
from com.models import SysUser, SysLog
from threading import Thread
import uuid

def execute_send_mail(app, message):
    '''
    执行发送邮件
    :param app:
    :param message:
    :return:
    '''
    with app.app_context():
        user = SysUser.query.filter_by(user_id='admin').first()
        try:
            mail.send(message)
            log = SysLog(id=uuid.uuid4().hex, url='null', operation='邮件提醒发送成功', create_id=user.id, user_id=user.id)
            db.session.add(log)
        except Exception as e:
            log = SysLog(id=uuid.uuid4().hex, url='null', operation='邮件提醒发送失败;Exception is : '+e, create_id=user.id, user_id=user.id)
            db.session.add(log)
        db.session.commit()
def send_mail(subject, to, cc, template, **kwargs):
    '''
    启动邮件发送线程，异步发送邮件
    :param subject:
    :param to:
    :param template:
    :param kwargs:
    :return:
    '''
    subject = current_app.config['MAIL_SUBJECT_PREFIX']+subject
    # print('Subject is : ', subject, ', to : ', to, ', template is : ', template)
    message = Message(subject, recipients=to, cc=cc) if cc else Message(subject, recipients=to)
    # message.body = render_template(template+'.txt', **kwargs)
    message.html = render_template(template+'.html', **kwargs)
    app = current_app._get_current_object()
    thread = Thread(target=execute_send_mail, args=[app, message])
    thread.start()
    return thread