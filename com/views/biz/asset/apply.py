from flask import Blueprint, render_template, flash, redirect, url_for, request,current_app,session
from flask_login import login_required, current_user
from com.models import BizVendorMaster
from com.plugins import db
from com.decorators import log_record
from com.forms.biz.master.vendor import VendorSearchForm,VendorForm
import uuid, time
from datetime import datetime
bp_apply = Blueprint('apply', __name__)
@bp_apply.route('/index', methods=['GET', 'POST'])
@login_required ###必须登录画面
@log_record('查看资产登记信息')###记录操作日志
def index():
    pass
