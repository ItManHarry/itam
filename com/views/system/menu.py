'''
系统菜单管理
'''
from flask import Blueprint, render_template, request, current_app, flash, redirect, url_for, jsonify, session
from flask_login import login_required, current_user
from com.models import SysMenu, SysModule, SysRole
from com.plugins import db
from com.decorators import log_record
from com.forms.sys.menu import MenuForm, MenuSearchForm
from com.utils import change_entity_order
import uuid, time
from datetime import datetime
bp_menu = Blueprint('menu', __name__)
@bp_menu.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查看系统菜单清单')
def index():
    form = MenuSearchForm()
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        try:
            name = session['menu_view_search_name'] if session['menu_view_search_name'] else ''  # 菜单名称
        except KeyError:
            name = ''
        form.name.data = name
    if request.method == 'POST':
        page = 1
        name = form.name.data
        session['menu_view_search_name'] = name
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']
    pagination = SysMenu.query.filter(SysMenu.name.like('%'+name+'%')).order_by(SysMenu.code, SysMenu.order_by).paginate(page, per_page)
    menus = pagination.items
    return render_template('sys/menu/index.html', form=form, pagination=pagination, menus=menus)
@bp_menu.route('/add', methods=['GET', 'POST'])
@login_required
@log_record('新增系统菜单')
def add():
    form = MenuForm()
    form.module.choices = get_modules()
    if form.validate_on_submit():
        menu = SysMenu(
            id=uuid.uuid4().hex,
            code=form.code.data,
            name=form.name.data,
            url=form.url.data,
            remark=form.remark.data,
            module_id=form.module.data,
            icon=form.icon.data,
            order_by=form.order_by.data,
            create_id=current_user.id
        )
        change_entity_order(form.order_by.data, 0, menu)
        db.session.add(menu)
        db.session.commit()
        flash('新增菜单成功！')
        return redirect(url_for('.index'))
    return render_template('sys/menu/add.html', form=form)

@bp_menu.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
@log_record('修改系统菜单')
def edit(id):
    form = MenuForm()
    menu = SysMenu.query.get_or_404(id)
    form.module.choices = get_modules()
    if request.method == 'GET':
        form.id.data = menu.id
        form.code.data = menu.code
        form.name.data = menu.name
        form.url.data = menu.url
        form.remark.data = menu.remark
        form.icon.data = menu.icon
        form.module.data = menu.module_id
        form.order_by.data = menu.order_by
    if form.validate_on_submit():
        change_entity_order(form.order_by.data, 1, menu)
        menu.code = form.code.data
        menu.name = form.name.data
        menu.url = form.url.data
        menu.remark = form.remark.data
        menu.icon = form.icon.data
        menu.module_id = form.module.data
        menu.order_by = form.order_by.data
        menu.update_id = current_user.id
        menu.updatetime_utc = datetime.utcfromtimestamp(time.time())
        menu.updatetime_loc = datetime.fromtimestamp(time.time())
        db.session.commit()
        flash('菜单修改成功！')
        return redirect(url_for('.index'))
    return render_template('sys/menu/edit.html', form=form)
@bp_menu.route('/status/<id>/<int:status>', methods=['POST'])
@login_required
@log_record('启用/停用系统菜单')
def status(id, status):
    menu = SysMenu.query.get_or_404(id)
    menu.active = True if status == 1 else False
    menu.update_id = current_user.id
    menu.updatetime_utc = datetime.utcfromtimestamp(time.time())
    menu.updatetime_loc = datetime.fromtimestamp(time.time())
    db.session.commit()
    return jsonify(code=1, message='菜单状态修改成功！')
def get_modules():
    modules = []
    for module in SysModule.query.order_by(SysModule.name.desc()).all():
        modules.append((module.id, module.name))
    return modules
@bp_menu.route('/roles/<id>', methods=['POST'])
@login_required
def get_roles(id):
    menu = SysMenu.query.get_or_404(id)
    print('Menu id is : ', id, ', menu name is : ', menu.name)
    print('Roles are : ', len(menu.roles))
    print('Current user company id is : ', current_user.company_id)
    roles = [role for role in menu.roles if role.company_id == current_user.company_id]
    print('Roles are : ', len(roles))
    return render_template('sys/menu/_roles.html', roles=roles)
    # return jsonify(code=1, roles=[])
@bp_menu.route('/roles/unlink/<role_id>/<menu_id>', methods=['POST'])
@login_required
def unlink_role(role_id, menu_id):
    role = SysRole.query.get_or_404(role_id)
    menu = SysMenu.query.get_or_404(menu_id)
    # print('Role id is : ', role_id, ', role name is : ', role.name)
    # print('Menu id is : ', menu_id, ', menu name is : ', menu.name)
    role.menus.remove(menu)
    db.session.commit()
    return jsonify(code=1, message='角色权限已断开！')