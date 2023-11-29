from flask import Blueprint, send_from_directory, render_template, flash, redirect, url_for, request,current_app,session, jsonify
from flask_login import login_required, current_user
from com.forms.biz.asset.apply import ApplySearchForm, ApplyForm
from com.models import BizAssetApply, BizCompany, BizDepartment, BizEmployee, BizAssetClass, BizBrandMaster, BizAssetItem
from com.plugins import db
from com.decorators import log_record
import uuid, time
from datetime import datetime
from com.utils import gen_bill_no #引用生成单号函数
bp_apply = Blueprint('apply', __name__)
@bp_apply.route('/index', methods=['GET', 'POST'])
@login_required ###必须登录画面
@log_record('查看资产登记信息')###记录操作日志
def index():
    form = ApplySearchForm()
    form.company.choices = [('0', '法人-All')] + [(company.id, company.name) for company in BizCompany.query.order_by(BizCompany.name).all()]
    form.department.choices = [('0', '部门-All')]
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        try:
            apply_no = session['apply_view_search_apply_no'] if session['apply_view_search_apply_no'] else ''  # 申请号
            draft_no = session['apply_view_search_draft_no'] if session['apply_view_search_draft_no'] else ''  # 草案号
            company = session['apply_view_search_company'] if session['apply_view_search_company'] else ''  # 申请法人
            department = session['apply_view_search_department'] if session['apply_view_search_department'] else ''  # 申请部门
        except KeyError:
            apply_no = ''
            draft_no = ''
            company = '0'
            department = '0'
        if company != '0':
            c = BizCompany.query.get(company)
            form.department.choices += [(department.id, department.name) for department in BizDepartment.query.with_parent(c).order_by().all()]
        form.apply_no.data = apply_no
        form.draft_no.data = draft_no
        form.company.data = company
        form.department.data = department
    if request.method == 'POST':
        page = 1
        apply_no = form.apply_no.data
        draft_no = form.draft_no.data
        company = form.company.data
        if company != '0':
            c = BizCompany.query.get(company)
            form.department.choices += [(department.id, department.name) for department in BizDepartment.query.with_parent(c).order_by().all()]
        department = form.department.data
        session['apply_view_search_apply_no'] = apply_no
        session['apply_view_search_draft_no'] = draft_no
        session['apply_view_search_company'] = company
        session['apply_view_search_department'] = department
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']
    conditions = set()
    conditions.add(BizAssetApply.bg_id == current_user.company_id)
    conditions.add(BizAssetApply.apply_no.like('%'+apply_no+'%'))
    conditions.add(BizAssetApply.draft_no.like('%'+draft_no+'%'))
    if company != '0':
        conditions.add(BizAssetApply.company_id == company)
    if department != '0':
        conditions.add(BizAssetApply.department_id == department)
    pagination = BizAssetApply.query.filter(*conditions).order_by(BizAssetApply.receive_date.desc()).paginate(page, per_page)
    applys = pagination.items
    return render_template('biz/asset/apply/index.html', pagination=pagination, form=form, applys=applys)
@bp_apply.route('/add', methods=['GET', 'POST'])
@login_required ###必须登录画面
@log_record('新增资产登记信息')###记录操作日志
def add():
    form = ApplyForm()
    if request.method == 'GET':
        # 执行清理临时申请记录
        clean_apply_items()
        form.items_tmp_id.data = uuid.uuid4().hex
    form.company.choices = [('00000000', '申请法人')]+[(company.id, company.name) for company in BizCompany.query.all()]
    form.department_slt.choices = [('00000000', '申请部门')] + [(department.id, department.name) for department in BizDepartment.query.all()]
    form.applicant_slt.choices = [('00000000', '申请人')] + [(employee.id, employee.name) for employee in BizEmployee.query.all()]
    form.class2_slt.choices = [('00000000', '资产类别-ALL')] + [(clazz.id, clazz.name) for clazz in BizAssetClass.query.filter_by(grade=2).order_by(BizAssetClass.code).all()]
    form.brand_slt.choices = [('00000000', '品牌-ALL')] + [(brand.id, brand.name) for brand in BizBrandMaster.query.order_by(BizBrandMaster.name).all()]
    if form.validate_on_submit():
        apply = BizAssetApply(id=uuid.uuid4().hex,
            apply_no=gen_bill_no('AY'),
            draft_no=form.draft_no.data,
            company_id=form.company_id.data,
            department_id=form.department.data,
            applicant_id=form.applicant.data,
            amount=form.amount.data,
            applicant_pos=form.applicant_pos.data,
            receive_date=datetime.strptime(form.receive_date.data, '%Y-%m-%d'),
            summary=form.summary.data,
            bg_id=current_user.company_id,
            create_id=current_user.id
        )
        if form.file.data:
            file_name = form.file.data.filename
            form.file.data.save(current_app.config['ASSET_APPLY_FILE_PATH']+'\\'+file_name)
            apply.file_path = file_name
        # 关联明细
        tmp_id = form.items_tmp_id.data
        items = BizAssetItem.query.filter_by(tmp_id=tmp_id).order_by(BizAssetItem.createtime_loc.desc()).all()
        for item in items:
            apply.items.append(item)
        db.session.add(apply)
        db.session.commit()
        flash('资产申请添加成功！')
        return redirect(url_for('.index'))
    else:
        print('Validation not passed!!!')
    return render_template('biz/asset/apply/add.html', form=form)
@bp_apply.route('/edit/<id>', methods=['GET', 'POST'])
@login_required ###必须登录画面
@log_record('修改资产申请信息')###记录操作日志
def edit(id):
    form = ApplyForm()
    form.company.choices = [('00000000', '申请法人')] + [(company.id, company.name) for company in BizCompany.query.all()]
    form.department_slt.choices = [('00000000', '申请部门')] + [(department.id, department.name) for department in BizDepartment.query.all()]
    form.applicant_slt.choices = [('00000000', '申请人')] + [(employee.id, employee.name) for employee in BizEmployee.query.all()]
    form.class2_slt.choices = [('00000000', '资产类别-ALL')] + [(clazz.id, clazz.name) for clazz in BizAssetClass.query.filter_by(grade=2).order_by(BizAssetClass.code).all()]
    form.brand_slt.choices = [('00000000', '品牌-ALL')] + [(brand.id, brand.name) for brand in BizBrandMaster.query.order_by(BizBrandMaster.name).all()]
    apply = BizAssetApply.query.get_or_404(id)
    file_name = apply.file_path
    if request.method == 'GET':
        # 执行清理临时申请记录
        clean_apply_items()
        form.id.data = apply.id
        form.apply_no.data = apply.apply_no
        form.draft_no.data = apply.draft_no
        form.company.data = apply.company_id
        form.company_id.data = apply.company_id
        form.department.data = apply.department_id
        form.department_slt.data = apply.department_id
        form.applicant.data = apply.applicant_id
        form.applicant_slt.data = apply.applicant_id
        form.amount.data = apply.amount
        form.receive_date.data = apply.receive_date.strftime('%Y-%m-%d')
        form.summary.data = apply.summary
        form.class2_id.data = apply.class2_id
        form.class3_id.data = apply.class3_id
        form.brand_id.data = apply.brand_id
        form.model_id.data = apply.model_id
        form.applicant_pos.data = apply.applicant_pos
    if form.validate_on_submit():
        if form.file.data:
            file_name = form.file.data.filename
            form.file.data.save(current_app.config['ASSET_APPLY_FILE_PATH'] + '\\' + file_name)
            apply.file_path = file_name
        apply.draft_no = form.draft_no.data
        apply.company_id = form.company_id.data
        apply.department_id = form.department.data
        apply.applicant_id = form.applicant.data
        apply.amount = form.amount.data
        apply.receive_date = datetime.strptime(form.receive_date.data, '%Y-%m-%d')
        apply.summary = form.summary.data
        apply.class2_id = form.class2_id.data
        apply.class3_id = form.class3_id.data
        apply.brand_id = form.brand_id.data
        apply.model_id = form.model_id.data
        apply.applicant_pos = form.applicant_pos.data
        apply.update_id = current_user.id
        apply.updatetime_utc = datetime.utcfromtimestamp(time.time())
        apply.updatetime_loc = datetime.fromtimestamp(time.time())
        db.session.commit()
        flash('资产申请更新成功！')
        return redirect(url_for('.index'))
    return render_template('biz/asset/apply/edit.html', form=form, file_name=file_name)
@bp_apply.route('/item/add', methods=['POST'])
@login_required 
@log_record('新增申请资产')
def item_add():
    data = request.get_json()
    tmp_id = data['tmp_id']
    item = BizAssetItem(id=uuid.uuid4().hex,
                        tmp_id=tmp_id,
                        class2_id=data['class2_id'],
                        class3_id=data['class3_id'],
                        brand_id=data['brand_id'],
                        model_id=data['model_id'],
                        user_id=data['user_id'],
                        amount=data['amount'])
    db.session.add(item)
    db.session.commit()
    items = BizAssetItem.query.filter_by(tmp_id=tmp_id).order_by(BizAssetItem.createtime_loc.desc()).all()
    total_amount = 0
    for item in items:
        total_amount += item.amount
    return render_template('biz/asset/apply/_items.html', items=items, total_amount=total_amount)
@bp_apply.route('/item/remove/<id>', methods=['POST'])
@login_required 
@log_record('移除申请资产')
def item_remove(id):
    item = BizAssetItem.query.get(id)
    tmp_id = item.tmp_id
    db.session.delete(item)
    db.session.commit()
    items = BizAssetItem.query.filter_by(tmp_id=tmp_id).order_by(BizAssetItem.createtime_loc.desc()).all()
    total_amount = 0
    for item in items:
        total_amount += item.amount
    return render_template('biz/asset/apply/_items.html', items=items, total_amount=total_amount)
@bp_apply.route('/get_file/<path:file_name>')
def get_file(file_name):
    return send_from_directory(current_app.config['ASSET_APPLY_FILE_PATH'], file_name)
@bp_apply.route('/get_info/<apply_no>', methods=['GET', 'POST'])
def get_info(apply_no):
    apply = BizAssetApply.query.filter(BizAssetApply.apply_no == apply_no).first()
    return jsonify(info={
        'applicant': apply.applicant.name if apply else '-',
        'asset_class': apply.class2.name if apply and apply.class2 else '-',
        'asset_name': apply.class3.name if apply and  apply.class3 else '-',
        'brand': apply.brand.name if apply and apply.brand else '-',
        'model': apply.model.name if apply and apply.model else '-',
    })
@bp_apply.route('/get_departments/<company_id>', methods=['GET', 'POST'])
@login_required ###必须登录画面
@log_record('获取部门信息')###记录操作日志
def get_departments(company_id):
    company = BizCompany.query.get(company_id)
    return jsonify(departments=[(department.id, department.name) for department in BizDepartment.query.with_parent(company).order_by().all()])
@bp_apply.route('/get_employees/<department_id>', methods=['GET', 'POST'])
@login_required ###必须登录画面
@log_record('获取人员信息')###记录操作日志
def get_employees(department_id):
    department = BizDepartment.query.get(department_id)#获取部门信息
    return jsonify(employees=[(employee.id, employee.name) for employee in
                                BizEmployee.query.with_parent(department).order_by().all()])
def clean_apply_items():
    '''
    清理临时申请记录：申请ID为空的记录
    :return:
    '''
    items = BizAssetItem.query.filter(BizAssetItem.apply_id==None).all()
    if items:
        for item in items:
            db.session.delete(item)
        db.session.commit()
    else:
        print('No item data to clean!')