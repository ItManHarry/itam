from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from com.models import BizEnterprise, BizCompany
from com.plugins import db
from com.decorators import log_record
from com.forms.biz.organization.company import CompanyForm, CompanySearchForm
import uuid, time
from datetime import datetime
bp_brand = Blueprint('brand', __name__)
@bp_brand.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查看品牌分类信息')
def index():
    return render_template('biz/master/brand/index.html')