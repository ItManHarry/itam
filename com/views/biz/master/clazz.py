from flask import Blueprint, url_for, redirect, render_template
from flask_login import login_required, current_user
from com.plugins import db
from com.decorators import log_record
import uuid, time
bp_clazz = Blueprint('clazz', __name__)
@bp_clazz.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('biz/master/clazz/index.html')