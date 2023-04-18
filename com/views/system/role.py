'''
系统角色管理
'''
import uuid, time
from datetime import datetime
from flask import Blueprint, render_template, request, current_app, flash, redirect, url_for, jsonify, session
from flask_login import login_required, current_user
from com.forms.sys.role import RoleSearchForm, RoleForm
from com.models import SysRole, SysMenu, BizCompany
from com.decorators import log_record
from com.plugins import db
bp_role = Blueprint('role', __name__)
@bp_role.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查询系统角色清单')
def index():    
    form = RoleSearchForm()
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        try:
            name = session['role_view_search_name'] if session['role_view_search_name'] else ''  # 角色名称
        except KeyError:
            name = ''
        form.name.data = name
    if request.method == 'POST':
        page = 1
        name = form.name.data
        session['role_view_search_name'] = name
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']
    pagination = SysRole.query.filter(SysRole.name.like('%' + name + '%')).order_by(SysRole.name.desc()).paginate(page, per_page) if current_user.is_admin else SysRole.query.filter(SysRole.name.like('%' + name + '%'), SysRole.name != 'Administrator', SysRole.company_id == current_user.company_id).order_by(SysRole.name.desc()).paginate(page, per_page)
    roles = pagination.items
    return render_template('sys/role/index.html', form=form, pagination=pagination, roles=roles)
@bp_role.route('/add', methods=['GET', 'POST'])
@login_required
@log_record('新增系统角色')
def add():
    form = RoleForm()
    form.company.choices = [(company.id, company.name) for company in BizCompany.query.order_by(BizCompany.code).all()]
    if form.validate_on_submit():
        role = SysRole(
            id=uuid.uuid4().hex,
            name=form.name.data,
            create_id=current_user.id,
            company_id=current_user.company_id if current_user.company_id else form.company.data
        )
        db.session.add(role)
        db.session.commit()
        flash('角色添加成功！')
        return redirect(url_for('.index'))
    return render_template('sys/role/add.html', form=form)
@bp_role.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
@log_record('修改系统角色')
def edit(id):
    form = RoleForm()
    form.company.choices = [(company.id, company.name) for company in BizCompany.query.order_by(BizCompany.code).all()]
    role = SysRole.query.get_or_404(id)
    if request.method == 'GET':
        form.name.data = role.name
        form.company.data = role.company_id if role.company_id else ''
        form.id.data = role.id
    if form.validate_on_submit():
        role.name = form.name.data
        role.company_id = '' if role.name == 'Administrator' else current_user.company_id if current_user.company_id else form.company.data
        role.update_id = current_user.id
        role.updatetime_utc = datetime.utcfromtimestamp(time.time())
        role.updatetime_loc = datetime.fromtimestamp(time.time())
        db.session.commit()
        flash('角色修改成功！')
        return redirect(url_for('.index'))
    return render_template('sys/role/edit.html', form=form)
@bp_role.route('/menus/<id>', methods=['POST'])
@login_required
def menus(id):
    all_menus = []
    # 非管理员只能分发自己已分配的权限
    if current_user.is_admin:
        for menu in SysMenu.query.order_by(SysMenu.code, SysMenu.order_by).all():
            all_menus.append((menu.id, menu.module.name + ' / ' + menu.name))
    else:
        for menu in SysMenu.query.filter(SysMenu.code.in_(current_user.menus)).order_by(SysMenu.code, SysMenu.order_by).all():
            all_menus.append((menu.id, menu.module.name+' / '+menu.name))
    #print('All menus : ', all_menus)
    role = SysRole.query.get_or_404(id)
    authed_menus = []
    for menu in role.menus:
        authed_menus.append(menu.id)
    print('Authed menus : ', authed_menus)
    return jsonify(all_menus=all_menus, authed_menus=authed_menus)
@bp_role.route('/auth', methods=['POST'])
@login_required
def auth():
    data = request.get_json()
    role_id = data['role_id']
    menu_ids = data['menu_ids']
    print(role_id)
    role = SysRole.query.get_or_404(role_id)
    # 首先移除已授权菜单
    for menu in role.menus:
        role.menus.remove(menu)
        db.session.commit()
    # 添加新授权的菜单
    for menu_id in menu_ids:
        role.menus.append(SysMenu.query.get(menu_id))
    db.session.commit()
    return jsonify(code=1, message='授权成功！')