'''
系统字典信息管理
'''
from flask import Blueprint, render_template, request, current_app, flash, redirect, url_for, jsonify, session
from flask_login import login_required, current_user
from com.models import SysDict, SysEnum
from com.plugins import db
from com.forms.sys.dicts import DictForm, DictSearchForm
from com.decorators import log_record
import uuid, time
from datetime import datetime
bp_dict = Blueprint('dict', __name__)
@bp_dict.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查询系统字典清单')
def index():   
    form = DictSearchForm()
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        try:
            code = session['dict_view_search_code'] if session['dict_view_search_code'] else ''  # 字典代码
            name = session['dict_view_search_name'] if session['dict_view_search_name'] else ''  # 字典名称
        except KeyError:
            code = ''
            name = ''
        form.code.data = code
        form.name.data = name
    if request.method == 'POST':
        page = 1
        code = form.code.data
        name = form.name.data
        session['dict_view_search_code'] = code
        session['dict_view_search_name'] = name
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']
    pagination = SysDict.query.filter(SysDict.code.like('%'+code+'%'), SysDict.name.like('%'+name+'%')).order_by(SysDict.code).paginate(page, per_page)
    dictionaries = pagination.items
    return render_template('sys/dict/index.html', pagination=pagination, dictionaries=dictionaries, form=form)
@bp_dict.route('/add', methods=['GET', 'POST'])
@login_required
@log_record('新增字典信息')
def add():
    form = DictForm()
    if form.validate_on_submit():
        dictionary = SysDict(id=uuid.uuid4().hex, code=form.code.data.upper(), name=form.name.data, create_id=current_user.id)
        db.session.add(dictionary)
        db.session.commit()
        flash('字典信息添加成功！')
        return redirect(url_for('.index'))
    return render_template('sys/dict/add.html', form=form)
@bp_dict.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
@log_record('修改字典信息')
def edit(id):
    form = DictForm()
    dictionary = SysDict.query.get_or_404(id)    
    if request.method == 'GET':
        form.id.data = dictionary.id
        form.code.data = dictionary.code
        form.name.data = dictionary.name
    if form.validate_on_submit():
        dictionary.code = form.code.data
        dictionary.name = form.name.data
        dictionary.update_id = current_user.id
        dictionary.updatetime_utc = datetime.utcfromtimestamp(time.time())
        dictionary.updatetime_loc = datetime.fromtimestamp(time.time())
        db.session.commit()
        flash('字典信息更新成功！')
        return redirect(url_for('.index'))
    return render_template('sys/dict/edit.html', form=form)
@bp_dict.route('/enums/<dict_id>', methods=['POST'])
@login_required
@log_record('获取字典枚举信息')
def enums(dict_id):
    dictionary = SysDict.query.get_or_404(dict_id)
    enums = []
    for enum in dictionary.enums:
        enums.append((enum.id, enum.display, enum.item if enum.item else ''))
    return jsonify(enums=enums)
@bp_dict.route('/enum_add', methods=['POST'])
@login_required
@log_record('修改字典枚举信息')
def enum_add():
    data = request.get_json()
    dict_id = data['dict_id']
    dictionary = SysDict.query.get_or_404(dict_id)
    # 先移除已关联的枚举值
    for enum in dictionary.enums:
        dictionary.enums.remove(enum)
        db.session.commit()
    # 移除的枚举执行删除
    removed = data['removed']
    print('Removed : ', removed)
    for enum_id in removed:
        enum = SysEnum.query.get(enum_id)
        if enum:
            db.session.delete(enum)
            db.session.commit()
    # 关联枚举值
    enums = data['p_enums']
    for enum in enums:
        print('Enum id : ', enum['id'], ', key : ', enum['key'], ', display : ', enum['display'])
        enumeration = SysEnum.query.get(str(enum['id']))
        if enumeration:
            enumeration.item = enum['key']
            enumeration.display = enum['display']
            enumeration.update_id = current_user.id
            enumeration.updatetime_utc = datetime.utcfromtimestamp(time.time())
            enumeration.updatetime_loc = datetime.fromtimestamp(time.time())
            db.session.commit()
        else:
            enumeration = SysEnum(id=uuid.uuid4().hex, item=enum['key'], display=enum['display'], create_id=current_user.id)
            db.session.add(enumeration)
            db.session.commit()
        dictionary.enums.append(enumeration)
        db.session.commit()
    return jsonify(code=1, message='枚举维护成功!')