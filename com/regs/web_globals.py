from flask import url_for, redirect, flash, session, request, make_response
from flask_wtf.csrf import CSRFError
from com.utils import get_time, format_time, get_current_user, get_current_module, get_current_menu, format_date, format_date_year, cal_delta_time
def reg_web_global_path(app):
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    @app.before_request
    def request_intercept_before():
        time_out = False
        try:
            session['user_id']
        except:
            time_out = True
        request_path = request.path
        ajax_request = True if request.headers.get('x-requested-with') is not None and request.headers.get('x-requested-with') == 'XMLHttpRequest' else False
        print('Ajax Request' if ajax_request else 'Not Ajax Request')
        exclude_urls = [url_for('index'), url_for('auth.login'), url_for('auth.logout')]
        response = make_response()
        if request_path not in exclude_urls:
            if ajax_request:
                if time_out:
                    response.headers['login_timeout'] = 'Y'
            else:
                if time_out:
                    flash('登录超时，请重新登录！')
                    return redirect(url_for('auth.logout'))

    @app.errorhandler(CSRFError)
    def csrf_error(e):
        print('CSRF token error ......................')
def reg_web_global_context(app):
    @app.context_processor
    def config_template_conext():
        return dict(get_time=get_time,
                    format_time=format_time,
                    format_date=format_date,
                    format_date_year=format_date_year,
                    get_current_user=get_current_user,
                    get_current_module=get_current_module,
                    get_current_menu=get_current_menu,
                    cal_delta_time=cal_delta_time)