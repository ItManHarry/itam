from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from flask_login import login_required, current_user
from com.plugins import db
from com.models import SysMenu
bp_main = Blueprint('main', __name__)
@bp_main.route('/index')
@login_required
def index():
    '''
    跳转主页，暂未使用
    :return:
    '''
    print('Current module main index : ', session['active_module'])
    print('Current menu main index : ', session['active_menu'])
    session.pop('active_module', None)
    session.pop('active_menu', None)
    return render_template('main/index.html')
'''
点击导航及菜单项执行页面跳转逻辑处理
:return:
'''
@bp_main.route('/redirect_uri')
@login_required
def redirect_uri():
    '''
        获取当前模块ID
        逻辑：
        1. 如果module_id传递过来，取传递过来的module_id
        2. 没有传递取session中的active_module_id
        3. session没有取用户授权模块清单中的第一个模块的ID
    '''
    module_id = request.args.get('module_id') if request.args.get('module_id') else session['active_module'] if session['active_module'] else current_user.authed_modules[0].id
    '''
        获取当前菜单ID
        逻辑：
        1. 如果menu_id传递过来，取传递过来的menu_id
        2. 如果没有传递，取当前模块下菜单清单中第一个菜单ID
    '''
    menu_id = request.args.get('menu_id') if request.args.get('menu_id') else current_user.authed_menus[module_id][0].id
    return redirect(url_for('.to_uri', module_id=module_id, menu_id=menu_id))
'''
执行跳转至对应的功能画面
'''
@bp_main.route('/to_uri/<module_id>/<menu_id>')
@login_required
def to_uri(module_id, menu_id):
    print('Parameter module id is : ', module_id)
    print('Parameter menu id is : ', menu_id)
    session['active_module'] = module_id    # 用于head导航栏栏nav active判断
    session['active_menu'] = menu_id        # 用于左侧菜单menu active判断
    menu = SysMenu.query.get_or_404(menu_id)
    print('Menu url is : ', menu.url)
    print('Menu name is : ', menu.name)
    return redirect(url_for(menu.url))
    # return render_template('main/index.html')
@bp_main.route('/to_function', methods=['GET', 'POST'])
@login_required
def to_function():
    # 使用过的菜单项
    used_menus = current_user.used_menus
    # 已授权菜单ID数据:code list
    authed_menus = current_user.menus
    for menu in used_menus:
        if menu.code not in authed_menus:
            current_user.used_menus.remove(menu)
            db.session.commit()
    # 重新获取已使用的菜单项
    used_menus = current_user.used_menus
    if request.method == 'POST':
        menu_code = request.form['menu_code']
        menu = SysMenu.query.filter_by(code=menu_code.upper()).first()
        if menu:
            # 判断是否具有权限
            if menu_code.upper() in current_user.menus:
                session['active_module'] = menu.module.id
                session['active_menu'] = menu.id
                if menu not in current_user.used_menus:
                    current_user.used_menus.append(menu)
                    db.session.commit()
                return redirect(url_for(menu.url))
            else:
                flash('您没有该功能画面权限，请联系管理员！')
        else:
            flash('功能代码错误,没有对应的画面！')
    return render_template('main/home.html', used_menus=used_menus)