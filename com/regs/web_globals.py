from flask import url_for, redirect
from com.utils import get_time, format_time, get_current_user, get_current_module, get_current_menu
def reg_web_global_path(app):
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))
def reg_web_global_context(app):
    @app.context_processor
    def config_template_conext():
        return dict(get_time=get_time,
                    format_time=format_time,
                    get_current_user=get_current_user,
                    get_current_module=get_current_module,
                    get_current_menu=get_current_menu)