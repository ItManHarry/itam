'''
系统模块管理
'''
import uuid, time
from datetime import datetime
from flask import Blueprint, render_template, request, current_app, flash, redirect, url_for, jsonify, session
from flask_login import login_required, current_user
from com.forms.sys.module import ModuleSearchForm, ModuleForm
from com.models import SysModule
from com.decorators import log_record
from com.plugins import db
from com.utils import change_entity_order
bp_module = Blueprint('module', __name__)
@bp_module.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查询系统模块清单')
def index():    
    form = ModuleSearchForm()
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        try:
            name = session['module_view_search_name'] if session['module_view_search_name'] else ''  # 模块名称
        except KeyError:
            name = ''
        form.name.data = name
    if request.method == 'POST':
        page = 1
        name = form.name.data
        session['module_view_search_name'] = name
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']
    pagination = SysModule.query.filter(SysModule.name.like('%' + name + '%')).order_by(SysModule.order_by).paginate(page, per_page)
    modules = pagination.items
    return render_template('sys/module/index.html', form=form, pagination=pagination, modules=modules)
@bp_module.route('/add', methods=['GET', 'POST'])
@login_required
@log_record('新增系统模块')
def add():
    form = ModuleForm()
    if form.validate_on_submit():
        module = SysModule(
            id=uuid.uuid4().hex,
            code=form.code.data,
            name=form.name.data,
            order_by=form.order_by.data,
            create_id=current_user.id
        )
        change_entity_order(form.order_by.data, 0, module)
        db.session.add(module)
        db.session.commit()
        flash('模块添加成功！')
        return redirect(url_for('.index'))
    return render_template('sys/module/add.html', form=form)
@bp_module.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
@log_record('修改系统模块')
def edit(id):
    form = ModuleForm()
    module = SysModule.query.get_or_404(id)
    if request.method == 'GET':
        form.name.data = module.name
        form.code.data = module.code
        form.order_by.data = module.order_by
        form.id.data = module.id
    if form.validate_on_submit():
        change_entity_order(form.order_by.data, 1, module)
        module.name = form.name.data
        module.code = form.code.data
        module.order_by = form.order_by.data
        module.update_id = current_user.id
        module.updatetime_utc = datetime.utcfromtimestamp(time.time())
        module.updatetime_loc = datetime.fromtimestamp(time.time())
        db.session.commit()
        flash('模块修改成功！')
        return redirect(url_for('.index'))
    return render_template('sys/module/edit.html', form=form)
@bp_module.route('/menus/<id>', methods=['POST'])
@login_required
@log_record('查看模块下的菜单')
def menus(id):
    module = SysModule.query.get_or_404(id)
    menus = []
    for menu in module.menus:
        menus.append(menu.name)
    return jsonify(menus=menus, module=module.name)