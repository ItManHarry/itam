from flask import url_for, redirect, flash, session, request, make_response
from flask_wtf.csrf import CSRFError
from com.utils import get_time, format_time, get_current_user, get_current_module, get_current_menu, format_date, format_date_year, cal_delta_time
def reg_web_global_path(app):
    @app.route('/')
    def index():
        session['user_id'] = '000000'
        return redirect(url_for('auth.login'))

    @app.before_request
    def request_intercept_before():
        # 判断登录是否超时
        time_out = False
        try:
            session['user_id']
        except:
            time_out = True
        request_path = request.path
        ajax_request = True if request.headers.get('x-requested-with') is not None and request.headers.get('x-requested-with') == 'XMLHttpRequest' else False
        exclude_urls = [url_for('index'), url_for('auth.login'), url_for('auth.logout')]
        exclude = False
        if request_path in exclude_urls or 'static' in request_path:
            exclude = True
        # print('请求地址 : ', request_path, '是否属于非检查URL : ', exclude)
        response = make_response()
        if not exclude:
            print('<', request_path, '>检查session是否超时!')
            if time_out:
                if ajax_request:
                    response.headers['login_timeout'] = 'Y'
                    return response
                else:
                    flash('登录超时，请重新登录！')
                    return redirect(url_for('index'))
        else:
            print('<', request_path, '>不执行session超时检查!')
    @app.errorhandler(CSRFError)
    def csrf_error(e):
        flash('登录长时间未输入账号信息，请重新输入！')
        return redirect(url_for('index'))
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