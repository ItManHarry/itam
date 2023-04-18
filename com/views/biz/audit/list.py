from flask import Blueprint, render_template, flash, redirect, url_for, request, session, current_app, jsonify
from flask_login import login_required, current_user

from com.email import send_mail
from com.models import AuditLine, RelAuditLineRole, AuditRole, AuditInstance, BizStockIn, AuditItem, BizStockOut, \
    BizAssetMaster, BizStockHistory
from com.plugins import db
from com.decorators import log_record
from com.forms.biz.audit.list import ListSearchForm, ListForm
import uuid, time
from datetime import datetime

from com.views.system.dicts import get_enum_value

bp_list = Blueprint('list', __name__)


@bp_list.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查看待审批及审批信息')
def index():
    class1 = request.args.get('class1', type=int) if request.args.get('class1') else 1  # 1:待审批 0:审批完成  默认为1
    print(class1)
    form = ListSearchForm()
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        try:
            code = session['list_view_search_code'] if session['list_view_search_code'] else ''  # 模板代码
            name = session['list_view_search_name'] if session['list_view_search_name'] else ''  # 模板名称
        except KeyError:
            code = ''
            name = ''
        form.code.data = code
        form.name.data = name
    if request.method == 'POST':
        page = 1
        code = form.code.data
        name = form.name.data
        session['list_view_search_code'] = code
        session['list_view_search_name'] = name
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']

    if class1 == 1:
        pagination = AuditInstance.query.filter(AuditInstance.finished == 0,AuditInstance.user_id ==current_user.id ).order_by(
            AuditInstance.id).paginate(page, per_page)
        lists = pagination.items
        return render_template('biz/audit/list/index.html', pagination=pagination, lists=lists)
    else:
        pagination = AuditInstance.query.filter(AuditInstance.finished == 1).order_by(
            AuditInstance.id).paginate(page, per_page)
        lists = pagination.items
        return render_template('biz/audit/list/index0.html', pagination=pagination, lists=lists)
@bp_list.route('/detail/<id>', methods=['GET', 'POST'])
@login_required
@log_record('审批信息明细')
def detail(id):
    class1 = request.args.get('class1', type=int) if request.args.get('class1') else 1  # 1:待审批 0:审批完成  默认为1
    form = ListForm()
    list = AuditInstance.query.get_or_404(id)
    audit = BizStockIn.query.filter(BizStockIn.in_no == list.audit_item.bill_no).first()
    bso   = BizStockOut.query.filter(BizStockOut.out_no == list.audit_item.bill_no).first()
    # audit.len()---获取列表的长度
    print('billtype的值',list.audit_item.bill_type)
    if list.audit_item.bill_type == 'SO':
        form.id.data = id
        form.bill_type.data = list.audit_item.bill_type
        form.out_no.data = list.audit_item.bill_no
        form.out_date.data = bso.out_date
        form.outcharger_id.data = bso.charger.user_name
        form.outstate_id.data = bso.state.display
        form.summary.data = bso.summary
        return render_template('biz/audit/list/edit.html', form=form, assets=bso.assets)
    else:
        form.id.data = id
        form.bill_type.data = list.audit_item.bill_type
        form.in_no.data = list.audit_item.bill_no
        form.in_date.data = audit.in_date
        form.charger_id.data = audit.charger.user_name
        form.state_id.data = audit.state.display
        return render_template('biz/audit/list/edit.html', form=form, assets=audit.assets)
@bp_list.route('/detail1/<id>', methods=['GET', 'POST'])
@login_required
@log_record('审批信息明细')
def detail1(id):
    class1 = request.args.get('class1', type=int) if request.args.get('class1') else 1  # 1:待审批 0:审批完成  默认为1
    form = ListForm()
    list1 = AuditInstance.query.get_or_404(id)
    audit = BizStockIn.query.filter(BizStockIn.in_no == list1.audit_item.bill_no).first()
    bso = BizStockOut.query.filter(BizStockOut.out_no == list1.audit_item.bill_no).first()#出库单明细
    # audit.len()---获取列表的长度
    if list1.audit_item.bill_type == 'SO':
        form.id.data = id
        form.bill_type.data = list1.audit_item.bill_type
        form.out_no.data = list1.audit_item.bill_no
        form.out_date.data = bso.out_date.strftime('%Y-%m-%d')
        form.outcharger_id.data = bso.charger.user_name
        form.outstate_id.data = bso.state.display
        form.summary.data = bso.summary
        form.remark.data = list1.remark
        return render_template('biz/audit/list/edit0.html', form=form, assets=bso.assets)
    else:
        form.id.data = id
        form.bill_type.data = list1.audit_item.bill_type
        form.in_no.data = list1.audit_item.bill_no
        form.in_date.data = audit.in_date
        form.charger_id.data = audit.charger.user_name
        form.state_id.data = audit.state.display
        form.remark.data = list1.remark
        return render_template('biz/audit/list/edit0.html', form=form, assets=audit.assets)
@bp_list.route('/approve/<id>/<remark>', methods=['POST'])
@log_record('审批通过')
def approve(id,remark):
    # if remark == '01':
    #     print('备注',remark)
    # else:
    #     print('备注',remark)
    # print('备注',remark)
    # class1 = request.args.get('class1', type=int) if request.args.get('class1') else 1  # 1:待审批 0:审批完成  默认为1
    audit = AuditItem.query.filter(AuditItem.bill_no == id).first()
    lines = AuditLine.query.filter(AuditLine.code == audit.audit_line.code).first()
    lengths = len(lines.audit_roles)#用于判断长度
    flag  = audit.audit_level       #用于获取当前的审批状态如果和审批模板一致则是终审，否则继续申批
    print('name is : ', audit.audit_line.name,'CODE is : ',audit.audit_line.code)#获取模板code用于确认审批人员
    #循环遍历取出未审批的内容
    if lengths == flag:
        print('我是相等的')
        #更新audit_instance表
        for instance in audit.audit_instances:
            if instance.finished == 0:
                # auditemid = instance.id
                if remark == '01':
                    instance.remark = ''
                else:
                    instance.remark = remark
                auditemid = instance.id
                instance.finished = 1
                # instance.remark = remark
                instance.update_id = current_user.id
                instance.updatetime_utc = datetime.utcfromtimestamp(time.time())
                instance.updatetime_loc = datetime.fromtimestamp(time.time())
                # 更新biz_stock_in状态为已审批
                if instance.audit_item.bill_type == 'SI':
                    bizsk = BizStockIn.query.filter(BizStockIn.in_no == id).first()
                    e = get_enum_value('D004', '3')  # 用于获取字典信息的字典明细方法是code加value,3表示已完成
                    bizsk.state_id = e.id if e else ''
                    bizsk.update_id = current_user.id
                    bizsk.updatetime_utc = datetime.utcfromtimestamp(time.time())
                    bizsk.updatetime_loc = datetime.fromtimestamp(time.time())
                    # 更新audit_item内容
                    audit.audit_finish = 1  ######0表示false，1表示true
                    audit.update_id = current_user.id
                    audit.updatetime_utc = datetime.utcfromtimestamp(time.time())
                    audit.updatetime_loc = datetime.fromtimestamp(time.time())
                # print('长度是2341234124:', lengths, '标记是：', flag)

                    db.session.commit()
                else:
                    bizsko = BizStockOut.query.filter(BizStockOut.out_no == id).first()
                    e = get_enum_value('D004', '3')  # 用于获取字典信息的字典明细方法是code加value,3表示已完成
                    bizsko.state_id = e.id if e else ''
                    bizsko.update_id = current_user.id
                    bizsko.updatetime_utc = datetime.utcfromtimestamp(time.time())
                    bizsko.updatetime_loc = datetime.fromtimestamp(time.time())
                    # 更新audit_item内容
                    audit.audit_finish = 1  ######0表示false，1表示true
                    audit.update_id = current_user.id
                    audit.updatetime_utc = datetime.utcfromtimestamp(time.time())
                    audit.updatetime_loc = datetime.fromtimestamp(time.time())
                    # print('长度是2341234124:', lengths, '标记是：', flag)

                    db.session.commit()
        db.session.commit()

    else:
        print('我是不相等的')
        #更新audit_item的audit_level 加1
        print('是否已经加一',audit.audit_level)
        audit.audit_level = audit.audit_level + 1
        audit.update_id = current_user.id
        audit.updatetime_utc = datetime.utcfromtimestamp(time.time())
        audit.updatetime_loc = datetime.fromtimestamp(time.time())
        db.session.commit()
        #更新当前instance
        print('备注是:', id)#同一个单据多个审批人时要同时finishi
        # 更新audit_instance表
        for instance in audit.audit_instances:
            if instance.finished == 0:
                instance.finished = 1
                if remark == '01':
                    instance.remark = ''
                else:
                    instance.remark = remark
                # instance.remark = remark
                instance.update_id = current_user.id
                instance.updatetime_utc = datetime.utcfromtimestamp(time.time())
                instance.updatetime_loc = datetime.fromtimestamp(time.time())
        # db.session.commit()
        #开始发邮件调用相关的函数使用audit_level进行人员判断
        # 发送邮件提醒
        #获取assets信息list1 = AuditInstance.query.get_or_404(id)
        #list1.audit_item.bill_type
            if instance.audit_item.bill_type == 'SO':
                master = BizStockOut.query.filter(BizStockOut.out_no == id).first()
            else:
                biskin = BizStockIn.query.filter(BizStockIn.in_no == id).first()
                master1 = BizAssetMaster.query.filter(BizAssetMaster.in_bill_id == biskin.id).first()
            # audit_line = AuditLine.query.filter_by(code='T001').first()#code需要设置成参数
            rel = RelAuditLineRole.query.filter(RelAuditLineRole.audit_line_id == lines.id,
                                                RelAuditLineRole.audit_grade == audit.audit_level).first()
            if rel:
                audit_role = AuditRole.query.get(rel.audit_role_id)
                auditors = audit_role.auditors
                if auditors:
                    # 生成Work To Do
                    for user in auditors:
                        audit_instance = AuditInstance(
                            id=uuid.uuid4().hex,
                            audit_item_id=audit.id,
                            user_id=user.id
                        )
                        db.session.add(audit_instance)
                    db.session.commit()
                    to = [user.email for user in auditors]
                else:
                    to = []
                if to:
                    print('Send mail to : ', to)
                    #subject要根据出库or入库标记判断
                    if audit.bill_type == 'SI':
                        send_mail(subject='资产登记审批提醒', to=to, cc=[], template='emails/asset_approve_remind', asset=master1)
                    else:
                        send_mail(subject='资产出库审批提醒', to=to, cc=[], template='emails/stockout_approve_remind',
                                  asset=master.assets)
        flash('审批成功！')

    # print(lines.audit_roles,len(lines.audit_roles))#len（）函数用于算数量
    # print('name is : ', audit.audit_line.name,'CODE is : ',audit.audit_line.code)#获取模板code用于确认审批人员
    #audit_instance 判断是否继续审批的标准是userid和finished不等于0
    #如果退回时只更新表完成状态audit_instance，不插入数据；更新biz_stock_in对应单据的state——in栏位为已退回状态
    #audit_item最终审批时要通过audit——level判断是否始终申，每次审批后audit-level自动加1
    #通过时最终要更新biz_stock_in对应单据的state——in栏位为已审批状态
    return jsonify(code=1, message='审批完成！')
@bp_list.route('/reject/<id>/<remark>', methods=['POST'])
@log_record('审批否决')
def reject(id,remark):
    print('id的值：', id, '备注', remark)
    audit = AuditItem.query.filter(AuditItem.bill_no == id).first()
    lines = AuditLine.query.filter(AuditLine.code == audit.audit_line.code).first()
    lengths = len(lines.audit_roles)  # 用于判断长度

    # print('name is : ', audit.audit_line.name, 'CODE is : ', audit.audit_line.code,'lines is:',lines.id)  # 获取模板code用于确认审批人员
    # 更新audit_instance表
    for instance in audit.audit_instances:
        if instance.finished == 0:
            auditemid = instance.id
            if remark == '01':
                instance.remark = ''
            else:
                instance.remark = remark
            instance.finished = 1
            # instance.remark = remark
            instance.update_id = current_user.id
            instance.updatetime_utc = datetime.utcfromtimestamp(time.time())
            instance.updatetime_loc = datetime.fromtimestamp(time.time())
            # 更新audit_item的audit_level
            audit.audit_level = 1
            audit.update_id = current_user.id
            audit.updatetime_utc = datetime.utcfromtimestamp(time.time())
            audit.updatetime_loc = datetime.fromtimestamp(time.time())
            db.session.commit()
            # 更新biz_stock_in状态为已审批
            # 开始发送邮件
            print('type is ',instance.audit_item.bill_type)
            if instance.audit_item.bill_type == 'SO':
                print('我是出库单')
                bizsko = BizStockOut.query.filter(BizStockOut.out_no == id).first()
                # 获取数量
                asset_ids = []
                asset_ams = []
                items = BizStockHistory.query.filter_by(bill_no=id).all()
                if items:
                    for item in items:
                        asset_ids.append(item.asset_id)
                        asset_ams.append(str(item.amount))
                    amount_dict = dict(zip(asset_ids, asset_ams))
                else:
                    amount_dict = {}

                # for asset in bizsko.assets:
                #     for bill in asset.out_bills:
                #         print('出库单',bill.out_no)
                master = BizAssetMaster.query.filter(BizAssetMaster.out_bills == bizsko.id).first()
                e = get_enum_value('D004', '0')  # 用于获取字典信息的字典明细方法是code加value,4表示已退回
                bizsko.state_id = e.id if e else ''
                bizsko.update_id = current_user.id
                bizsko.updatetime_utc = datetime.utcfromtimestamp(time.time())
                bizsko.updatetime_loc = datetime.fromtimestamp(time.time())
                db.session.commit()


            else:
                # 出库单据获取资产信息

                bizsk = BizStockIn.query.filter(BizStockIn.in_no == id).first()
                master1 = BizAssetMaster.query.filter(BizAssetMaster.in_bill_id == bizsk.id ).first()
                # for asset in bizsk.assets:
                #     print('资产入库单',asset.in_bill,'型号',asset.model.name,'资产名称',asset.class3.name,)

                e = get_enum_value('D004', '4')  # 用于获取字典信息的字典明细方法是code加value,4表示已退回
                bizsk.state_id = e.id if e else ''
                bizsk.update_id = current_user.id
                bizsk.updatetime_utc = datetime.utcfromtimestamp(time.time())
                bizsk.updatetime_loc = datetime.fromtimestamp(time.time())
                db.session.commit()
                # master = BizStockIn.query.filter(BizStockIn.in_no == id).first()
            # audit_line = AuditLine.query.filter_by(code='T001').first()#code需要设置成参数,audit_grade相当于等级
            level = audit.audit_level  # 用于获取当前的审批状态如果和审批模板一致则是终审，否则继续申批
            rel = RelAuditLineRole.query.filter(RelAuditLineRole.audit_line_id == lines.id,
                                                RelAuditLineRole.audit_grade == level).first()
            if rel:
                audit_role = AuditRole.query.get(rel.audit_role_id)
                auditors = audit_role.auditors
                if auditors:
                    # 生成Work To Do
                    for user in auditors:
                        audit_instance = AuditInstance(
                            id=uuid.uuid4().hex,
                            audit_item_id=audit.id,
                            user_id=user.id
                        )
                        db.session.add(audit_instance)
                    db.session.commit()
                    to = [user.email for user in auditors]
                else:
                    to = []
                if to:
                    print('Send mail to : ', to)
                    # subject要根据出库or入库标记判断
                    if audit.bill_type == 'SI':
                        print('到我了','到底了')
                        send_mail(subject='资产登记审批提醒', to=to, cc=[], template='emails/asset_approve_remind',
                                  asset=master1)
                    else:
                        send_mail(subject='资产出库审批提醒', to=to, cc=[], template='emails/stockout_approve_remind',
                                  amount_dict=amount_dict, asset=bizsko.assets)
    flash('审批成功！')
    db.session.commit()
    return jsonify(code=1, message='退回审批完成！')