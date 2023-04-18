from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from com.models import AuditBizCode
from com.plugins import db
from com.decorators import log_record
from com.forms.biz.audit.bizcode import BizcodeForm
import uuid, time
from datetime import datetime
bp_bizcode = Blueprint('bizcode', __name__)
@bp_bizcode.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查看业务代码')
def index():
    bizcodes = AuditBizCode.query.filter(AuditBizCode.bg_id == current_user.company_id).all()
    return render_template('biz/audit/bizcode/index.html',bizcodes=bizcodes)
@bp_bizcode.route('/add', methods=['GET', 'POST'])
@login_required
@log_record('新增业务代码')
def add():
    form = BizcodeForm()
    if form.validate_on_submit():
        bizcode = AuditBizCode(id=uuid.uuid4().hex,
                               code=form.code.data.upper(),
                               name=form.name.data,
                               bg_id=current_user.company_id,
                               create_id=current_user.id
                               )
        db.session.add(bizcode)
        db.session.commit()
        flash('业务代码添加成功')
        return redirect(url_for('.index'))
    return render_template('biz/audit/bizcode/add.html', form=form)
@bp_bizcode.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
@log_record('修改业务码信息')
def edit(id):
    form = BizcodeForm()
    bizcode = AuditBizCode.query.get_or_404(id)
    if request.method == 'GET':
        form.id.data = id
        form.code.data = bizcode.code
        form.name.data = bizcode.name

    if form.validate_on_submit():
        bizcode.code = form.code.data
        bizcode.name = form.name.data

        bizcode.update_id = current_user.id
        bizcode.updatetime_utc = datetime.utcfromtimestamp(time.time())
        bizcode.updatetime_loc = datetime.fromtimestamp(time.time())
        db.session.commit()
        flash('业务代码修改成功')
        return redirect(url_for('.index'))
    return render_template('biz/audit/bizcode/edit.html', form=form)