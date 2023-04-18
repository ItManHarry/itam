'''
Flask扩展
'''
from flask import request, current_app
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_moment import Moment
from flask_mail import Mail
from flask_ckeditor import CKEditor
from flask_migrate import Migrate
from flask_login import LoginManager, AnonymousUserMixin
from flask_wtf.csrf import CSRFProtect
from flask_dropzone import Dropzone
from flask_apscheduler import APScheduler
from flask_babel import Babel
# 创建扩展实例
bootstrap = Bootstrap()
dropzone = Dropzone()
db = SQLAlchemy()
moment = Moment()
mail = Mail()
ckeditor = CKEditor()
migrate = Migrate()
csrf = CSRFProtect()
scheduler = APScheduler()
login_manager = LoginManager()
# 配置login_required对应的跳转信息
login_manager.login_view = 'auth.login'
login_manager.login_message = '登录后才能进行相关操作!!!'
login_manager.login_message_category = 'warning'
# 加载用户
# 集成flask-login后必须实现此方法，否则系统异常
@login_manager.user_loader
def load_user(user_id):
    from com.models import SysUser
    user = SysUser.query.get(user_id)
    return user
class Guest(AnonymousUserMixin):
    pass
login_manager.anonymous_user = Guest
babel = Babel()
#设置区域选择函数
@babel.localeselector
def get_locale():
    locale = request.cookies.get('locale')
    if locale is not None:
        return locale
    #if current_user.is_authenticated and current_user.locale is not None:
    #    return current_user.locale
    return request.accept_languages.best_match(current_app.config['SYS_LOCALES'])