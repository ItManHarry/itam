from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from com.models import BizEmailConfig
from com.plugins import db
from com.decorators import log_record
from com.forms.biz.master.email import EmailForm

import uuid, time
from datetime import datetime
bp_email = Blueprint('email', __name__)
@bp_email.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查看邮件配置信息')
def index():
    emails = BizEmailConfig.query.all()
    return render_template('biz/master/email/index.html',emails=emails)
@bp_email.route('/add', methods=['GET', 'POST'])
@login_required
@log_record('新增邮件配置信息')
def add():
    form = EmailForm()
    if form.validate_on_submit():
        email = BizEmailConfig(id=uuid.uuid4().hex,
                               code=form.code.data.upper(),
                               name=form.name.data,
                               email_to=form.email_to.data,
                               email_cc=form.email_cc.data,
                               create_id=current_user.id
                               )
        db.session.add(email)
        db.session.commit()
        flash('邮箱信息添加成功')
        return redirect(url_for('.index'))
    return render_template('biz/master/email/add.html', form=form)
@bp_email.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
@log_record('修改邮件配置信息')
def edit(id):
    form = EmailForm()
    email = BizEmailConfig.query.get_or_404(id)
    if request.method == 'GET':
        form.id.data = id
        form.code.data = email.code
        form.name.data = email.name
        form.email_to.data = email.email_to
        form.email_cc.data = email.email_cc
    if form.validate_on_submit():
        email.code = form.code.data
        email.name = form.name.data
        email.email_to = form.email_to.data
        email.email_cc = form.email_cc.data
        email.update_id = current_user.id
        email.updatetime_utc = datetime.utcfromtimestamp(time.time())
        email.updatetime_loc = datetime.fromtimestamp(time.time())
        db.session.commit()
        flash('邮箱配置修改成功')
        return redirect(url_for('.index'))
    return render_template('biz/master/email/edit.html', form=form)