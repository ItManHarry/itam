from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from com.plugins import db
from datetime import datetime
import uuid
'''
通用模型
'''
class BaseModel():
    id = db.Column(db.String(32), primary_key=True)                     # 表主键ID
    active = db.Column(db.Boolean, default=True)                        # 是否使用(默认已使用)
    createtime_utc = db.Column(db.DateTime, default=datetime.utcnow)    # 创建时间(UTC标准时间)
    createtime_loc = db.Column(db.DateTime, default=datetime.now)       # 创建时间(本地时间)
    create_id = db.Column(db.String(32))                                # 创建人员
    updatetime_utc = db.Column(db.DateTime, default=datetime.utcnow)    # 更新时间(UTC标准时间)
    updatetime_loc = db.Column(db.DateTime, default=datetime.now)       # 更新时间(本地时间)
    update_id = db.Column(db.String(32))                                # 更新人员
'''
系统用户
'''
class SysUser(BaseModel, db.Model, UserMixin):
    user_id = db.Column(db.String(16), unique=True)                                         # 用户代码
    user_name = db.Column(db.String(24))                                                    # 用户姓名
    user_pwd_hash = db.Column(db.String(128))                                               # 用户密码(加密后)
    is_ad = db.Column(db.Boolean, default=False)                                            # 工厂AD
    is_admin = db.Column(db.Boolean, default=False)                                         # 是否是系统管理员(只在初始化时为True,其他均莫非False)
    email = db.Column(db.String(128))                                                       # 邮箱
    phone = db.Column(db.String(24))                                                        # 电话
    role_id = db.Column(db.String(32), db.ForeignKey('sys_role.id'))                        # 系统角色ID
    role = db.relationship('SysRole', back_populates='users')                               # 系统角色
    company_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))                  # 所属法人ID
    company = db.relationship('BizCompany', back_populates='users')                                 # 所属法人
    used_menus = db.relationship('SysMenu', secondary='rel_user_menu', back_populates='users')      # 使用过的菜单项(用于主页显示)
    in_charger = db.relationship('BizStockIn', back_populates='charger')                            # 资产入库操作人员
    out_charger = db.relationship('BizStockOut', back_populates='charger')                          # 资产出库操作人员
    asset_scraper = db.relationship('BizAssetScrap', back_populates='scraper')                      # 报废判定人员
    audit_roles = db.relationship('AuditRole', secondary='rel_audit_role_user', back_populates='auditors')  # 审批角色
    audit_list = db.relationship('AuditInstance', back_populates='user')
    logs = db.relationship('SysLog', back_populates='user')                                                 # 操作日志

    def set_password(self, password):
        self.user_pwd_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.user_pwd_hash, password)
    # 已授权菜单code数据
    @property
    def menus(self):
        ms = self.role.menus
        return [menu.code for menu in ms]
    # 用户菜单权限(返回:模块ID-菜单List字典)
    @property
    def authed_menus(self):
        module_menu = {}
        modules = self.authed_modules
        menus = self.role.menus
        menu_ids = []
        for menu in menus:
            menu_ids.append(menu.id)
        for module in modules:
            module_menu[module.id] = SysMenu.query.filter(SysMenu.module_id == module.id).filter(SysMenu.id.in_(menu_ids)).order_by(SysMenu.order_by).all()
        return module_menu
    # 用户模块权限
    @property
    def authed_modules(self):
        '''
        获取当前用户的菜单权限
        '''
        menus = self.role.menus
        if menus:
            '''
            获取用户模块权限
            '''
            module_ids = []
            for menu in menus:
                if menu.module_id not in module_ids:
                    module_ids.append(menu.module_id)
            '''
            重新查询并排序
            '''
            modules = SysModule.query.filter(SysModule.id.in_(module_ids)).order_by(SysModule.order_by.desc()).all()
        else:
            return []
        return modules

'''
用户菜单关联表(多对多) - 用于主页显示使用过的功能项
'''
rel_user_menu = db.Table('rel_user_menu',
    db.Column('user_id', db.String(32), db.ForeignKey('sys_user.id')),
    db.Column('menu_id', db.String(32), db.ForeignKey('sys_menu.id'))
)
'''
角色菜单关联表(多对多)
'''
rel_role_menu = db.Table('rel_role_menu',
    db.Column('role_id', db.String(32), db.ForeignKey('sys_role.id')),
    db.Column('menu_id', db.String(32), db.ForeignKey('sys_menu.id'))
)
'''
系统角色
'''
class SysRole(BaseModel, db.Model):
    name = db.Column(db.String(64), unique=True)                                            # 角色名称
    company_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))                  # 所属法人ID
    company = db.relationship('BizCompany', back_populates='roles')                         # 所属法人
    users = db.relationship('SysUser', back_populates='role')                               # 用户
    menus = db.relationship('SysMenu', secondary='rel_role_menu', back_populates='roles')   # 菜单
'''
系统模块
'''
class SysModule(BaseModel, db.Model):
    code = db.Column(db.String(12), unique=True)                # 模块代码(用以导航状态)
    name = db.Column(db.String(24), unique=True)                # 模块名称
    order_by = db.Column(db.Integer)                            # 排序
    menus = db.relationship('SysMenu', back_populates='module') # 和菜单建立一对多关联关系
'''
系统菜单
'''
class SysMenu(BaseModel, db.Model):
    code = db.Column(db.String(12), unique=True)    # 菜单代码
    name = db.Column(db.String(64))                 # 菜单名
    url = db.Column(db.String(24))                  # URL地址
    remark = db.Column(db.String(128))              # 菜单描述
    icon = db.Column(db.String(24))                 # 图标
    order_by = db.Column(db.Integer)                # 排序
    module_id = db.Column(db.String(32), db.ForeignKey('sys_module.id'))
    module = db.relationship('SysModule', back_populates='menus')
    roles = db.relationship('SysRole', secondary='rel_role_menu', back_populates='menus')
    users = db.relationship('SysUser', secondary='rel_user_menu', back_populates='used_menus')
'''
下拉字典
'''
class SysDict(BaseModel, db.Model):
    code = db.Column(db.String(24), unique=True)    # 字典代码
    name = db.Column(db.String(24), unique=True)    # 字典名称
    enums = db.relationship('SysEnum', back_populates='dictionary', cascade='all')
'''
下拉字典枚举值
'''
class SysEnum(BaseModel, db.Model):
    item = db.Column(db.String(8))                                           # 枚举value(对应<option>标签中的value属性)
    display = db.Column(db.String(128))                                      # 枚举view(对应<option>?</option>的显示值)
    order_by = db.Column(db.Integer)                                         # 排序
    dict_id = db.Column(db.String(32), db.ForeignKey('sys_dict.id'))         # 所属字典ID
    dictionary = db.relationship('SysDict', back_populates='enums')          # 所属字典
    asset_status = db.relationship('BizAssetMaster', back_populates='status', lazy=True, primaryjoin='BizAssetMaster.status_id == SysEnum.id')  # 资产状态
    in_state = db.relationship('BizStockIn', back_populates='state', lazy=True, primaryjoin='BizStockIn.state_id == SysEnum.id')                # 入库登记审批状态
    out_state = db.relationship('BizStockOut', back_populates='state', lazy=True, primaryjoin='BizStockOut.state_id == SysEnum.id')             # 出库登记审批状态
    out_type = db.relationship('BizStockOut', back_populates='out_type', lazy=True, primaryjoin='BizStockOut.out_type_id == SysEnum.id')        # 出库类型
    repair_type = db.relationship('BizAssetRepair', back_populates='repair_type', lazy=True, primaryjoin='BizAssetRepair.repair_type_id == SysEnum.id')     # 故障维修类型
    repair_state = db.relationship('BizAssetRepair', back_populates='repair_state', lazy=True, primaryjoin='BizAssetRepair.repair_state_id == SysEnum.id')  # 故障维修状态
    scrap_reason = db.relationship('BizAssetScrap', back_populates='scrap_reason', lazy=True, primaryjoin='BizAssetScrap.scrap_reason_id == SysEnum.id')    # 报废原因
    scrap_state = db.relationship('BizAssetScrap', back_populates='scrap_state', lazy=True, primaryjoin='BizAssetScrap.scrap_state_id == SysEnum.id')       # 报废状态
    stock_io_class = db.relationship('BizStockHistory', back_populates='io_class')
'''
系统操作日志
'''
class SysLog(BaseModel, db.Model):
    url = db.Column(db.String(250))             # 菜单url
    operation = db.Column(db.Text)              # 操作内容
    user_id = db.Column(db.String(32), db.ForeignKey('sys_user.id'))
    user = db.relationship('SysUser', back_populates='logs')
'''
事业处信息表
'''
class BizEnterprise(BaseModel, db.Model):
    code = db.Column(db.String(10), unique=True)            # 事业处代码
    name = db.Column(db.String(128))                        # 事业处名称
    companies = db.relationship('BizCompany', back_populates='enterprise')
    # 初始化事业处
    @staticmethod
    def init_enterprises():
        enterprises = (
            ('HDI', '现代斗山'),
            ('HCE', '苏州建机'),
        )
        for item in enterprises:
            enterprise = BizEnterprise.query.filter_by(code=item[0]).first()
            if enterprise is None:
                enterprise = BizEnterprise(
                    id=uuid.uuid4().hex,
                    code=item[0],
                    name=item[1]
                )
                db.session.add(enterprise)
                db.session.commit()
'''
法人信息表
'''
class BizCompany(BaseModel, db.Model):
    code = db.Column(db.String(10))                         # 法人代码
    name = db.Column(db.String(128))                        # 法人名称
    enterprise_id = db.Column(db.String(32), db.ForeignKey('biz_enterprise.id'))
    enterprise = db.relationship('BizEnterprise', back_populates='companies')
    users = db.relationship('SysUser', back_populates='company')                # 用户
    roles = db.relationship('SysRole', back_populates='company')                # 角色
    departments = db.relationship('BizDepartment', back_populates='company')    # 部门
    employees = db.relationship('BizEmployee', back_populates='company')        # 雇员
    stores = db.relationship('BizStoreMaster', back_populates='bg')             # 仓库
    vendors = db.relationship('BizVendorMaster', back_populates='bg')           # 供应商
    brands = db.relationship('BizBrandMaster', back_populates='bg')             # 品牌
    applications = db.relationship('BizAssetApply', back_populates='company', lazy=True, primaryjoin='BizAssetApply.company_id == BizCompany.id')   # 业务别物料申请单
    apply_bills = db.relationship('BizAssetApply', back_populates='bg', lazy=True, primaryjoin='BizAssetApply.bg_id == BizCompany.id')              # 单据别物料申请单
    buy_bills = db.relationship('BizAssetBuy', back_populates='bg')             # 单据别物料购买单
    in_bills = db.relationship('BizStockIn', back_populates='bg')               # 入库单
    out_bills = db.relationship('BizStockOut', back_populates='bg')             # 出库单
    asset_classes = db.relationship('BizAssetClass', back_populates='bg')       # 资产类别
    biz_assets = db.relationship('BizAssetMaster', back_populates='company', lazy=True, primaryjoin='BizAssetMaster.company_id == BizCompany.id')   # 业务层物料清单
    sys_assets = db.relationship('BizAssetMaster', back_populates='bg', lazy=True, primaryjoin='BizAssetMaster.bg_id == BizCompany.id')             # 数据层物料清单
    stock_history = db.relationship('BizStockHistory', back_populates='bg')     # 资产出入库履历
    stock_amount = db.relationship('BizStockAmount', back_populates='bg')       # 资产库存余额
    asset_repair = db.relationship('BizAssetRepair', back_populates='bg')       # 资产维修履历
    asset_scrap = db.relationship('BizAssetScrap', back_populates='bg')         # 资产报废清单
    asset_check = db.relationship('BizAssetCheck', back_populates='bg')         # 资产盘点单
    audit_codes = db.relationship('AuditBizCode', back_populates='bg')          # 审批业务
    audit_lines = db.relationship('AuditLine', back_populates='bg')             # 审批线
    audit_roles = db.relationship('AuditRole', back_populates='bg')             # 审批角色
    audit_items = db.relationship('AuditItem', back_populates='bg')             # 审批单据
    payment_bgs = db.relationship('BizPaymentBgMaster', back_populates='company')   # 结算BG信息
    # 初始化法人
    @staticmethod
    def init_companies():
        # 数据说明：法人代码 法人名称 事业处代码
        companies = (
            ('01920601', 'HDICC', 'HDI'),
            ('01920773', 'HDCFL', 'HDI'),
            ('01920052', 'HDISD', 'HDI'),
            ('01920000', 'HDICI', 'HDI'),
        )
        for item in companies:
            company = BizCompany.query.filter_by(code=item[0]).first()
            enterprise = BizEnterprise.query.filter_by(code=item[2]).first()
            if company is None:
                company = BizCompany(
                    id=uuid.uuid4().hex,
                    code=item[0],
                    name=item[1],
                    enterprise_id=enterprise.id if enterprise else ''
                )
                db.session.add(company)
                db.session.commit()
'''
部门层级关系
'''
class RelDepartment(BaseModel, db.Model):
    parent_department_id = db.Column(db.String(32), db.ForeignKey('biz_department.id'))
    parent_department = db.relationship('BizDepartment', foreign_keys=[parent_department_id], back_populates='parent_department', lazy='joined')    # 父部门
    child_department_id = db.Column(db.String(32), db.ForeignKey('biz_department.id'))
    child_department = db.relationship('BizDepartment', foreign_keys=[child_department_id], back_populates='child_department', lazy='joined')       # 子部门
'''
部门
'''
class BizDepartment(BaseModel, db.Model):
    code = db.Column(db.String(32))                                         # 部门代码
    name = db.Column(db.Text)                                               # 部门名称
    company_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))  # 所属法人ID
    company = db.relationship('BizCompany', back_populates='departments')   # 所属法人
    employees = db.relationship('BizEmployee', back_populates='department')
    parent_department = db.relationship('RelDepartment', foreign_keys=[RelDepartment.parent_department_id], back_populates='parent_department', lazy='dynamic', cascade='all')  # 父部门
    child_department = db.relationship('RelDepartment', foreign_keys=[RelDepartment.child_department_id], back_populates='child_department', lazy='dynamic', cascade='all')     # 子部门
    applications = db.relationship('BizAssetApply', back_populates='department')    # 物料申请单
    assets = db.relationship('BizAssetMaster', back_populates='department')         # 资产清单
    payment_bg_id = db.Column(db.String(32))                                        # 部门结算BG信息
    @property
    def payment_bg(self):
        return BizPaymentBgMaster.query.get(self.payment_bg_id) if self.payment_bg_id else None
    # 设置父部门
    def set_parent_department(self, department):
        '''
        逻辑：首先判断是否已经维护父部门，如果存在则执行删除后新增
        :param dept:
        :return:
        '''
        ref = RelDepartment.query.filter_by(child_department_id=self.id).first()
        if ref:
            db.session.delete(ref)
            db.session.commit()
        parent = RelDepartment(id=uuid.uuid4().hex, child_department=self, parent_department=department)
        db.session.add(parent)
        db.session.commit()
    @property
    def get_parent_department(self):
        dept = RelDepartment.query.filter_by(child_department_id=self.id).first()
        return dept.parent_department if dept else None
    # 设置子部门
    def set_child_department(self, department):
        '''
        逻辑：首先解除子部门原有的部门关系，然后再添加到当前部门下
        :param dept:
        :return:
        '''
        ref = RelDepartment.query.filter_by(child_department_id=department.id).first()
        if ref:
            db.session.delete(ref)
            db.session.commit()
        child = RelDepartment(id=uuid.uuid4().hex, child_department=department, parent_department=self)
        db.session.add(child)
        db.session.commit()
    @property
    def get_child_department(self):
        return RelDepartment.query.filter_by(parent_department_id=self.id).order_by(RelDepartment.createtime_loc.desc()).all()
'''
雇员信息
'''
class BizEmployee(BaseModel, db.Model):
    code = db.Column(db.String(32))     # 职号
    name = db.Column(db.String(128))    # 姓名
    email = db.Column(db.String(128))   # 邮箱
    phone = db.Column(db.String(100))   # 电话
    company_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))          # 所属法人ID
    company = db.relationship('BizCompany', back_populates='employees')             # 所属法人
    department_id = db.Column(db.String(32), db.ForeignKey('biz_department.id'))    # 所属部门ID
    department = db.relationship('BizDepartment', back_populates='employees')       # 所属部门
    applications = db.relationship('BizAssetApply', back_populates='applicant')     # 物料申请单
    repair_request_list = db.relationship('BizAssetRepair', back_populates='requested_by', lazy=True, primaryjoin='BizAssetRepair.requested_by_id == BizEmployee.id')   # 维修申请
    repair_handle_list = db.relationship('BizAssetRepair', back_populates='repair_handler', lazy=True, primaryjoin='BizAssetRepair.repair_handler_id == BizEmployee.id')# 维修处理
    managed_assets = db.relationship('BizAssetMaster', back_populates='manager', lazy=True, primaryjoin='BizAssetMaster.manager_id == BizEmployee.id')  # 管理资产
    used_assets = db.relationship('BizAssetMaster', back_populates='user', lazy=True, primaryjoin='BizAssetMaster.user_id == BizEmployee.id')           # 使用资产
    asset_checker = db.relationship('BizAssetCheck', back_populates='checker')      # 盘点担当
    asset_give_by = db.relationship('RelAssetOutItem', back_populates='give_by', lazy=True, primaryjoin='RelAssetOutItem.give_by_id == BizEmployee.id')         # 资产发放人
    asset_take_by = db.relationship('RelAssetOutItem', back_populates='take_by', lazy=True, primaryjoin='RelAssetOutItem.take_by_id == BizEmployee.id')         # 资产领用人
    asset_return_by = db.relationship('RelAssetOutItem', back_populates='return_by', lazy=True, primaryjoin='RelAssetOutItem.return_by_id == BizEmployee.id')   # 资产返回人
    asset_old_holder = db.relationship('BizAssetChange', back_populates='old_holder', lazy=True, primaryjoin='BizAssetChange.old_holder_id == BizEmployee.id')  # 资产上一持有者
    asset_new_holder = db.relationship('BizAssetChange', back_populates='new_holder', lazy=True, primaryjoin='BizAssetChange.new_holder_id == BizEmployee.id')  # 资产最新持有者
'''
存放位置-仓库表
'''
class BizStoreMaster(BaseModel, db.Model):
    code = db.Column(db.String(16))     # 仓库代码
    name = db.Column(db.String(64))     # 仓库名称
    place = db.Column(db.String(256))   # 仓库地点
    assets = db.relationship('BizAssetMaster', back_populates='store')  # 存放资产
    bg_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))   # 所属法人ID
    bg = db.relationship('BizCompany', back_populates='stores')         # 所属法人
'''
供应商信息表
'''
class BizVendorMaster(BaseModel, db.Model):
    code = db.Column(db.String(16))             # 供应商代码
    name = db.Column(db.String(64))             # 供应商名称
    contact_person = db.Column(db.String(32))   # 联系人
    contact_phone = db.Column(db.String(24))    # 联系人电话
    assets = db.relationship('BizAssetMaster', back_populates='vendor')     # 资产供应商
    maintains = db.relationship('BizAssetMaint', back_populates='vendor')   # 维保供应商
    bg_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))       # 所属法人ID
    bg = db.relationship('BizCompany', back_populates='vendors')            # 所属法人
'''
品牌信息表
'''
class BizBrandMaster(BaseModel, db.Model):
    code = db.Column(db.String(24), unique=True)    # 品牌代码
    name = db.Column(db.String(64), unique=True)    # 品牌名称
    models = db.relationship('BizBrandModel', back_populates='brand', cascade='all') # 型号
    assets = db.relationship('BizAssetMaster', back_populates='brand')          # 资产
    brand_amount = db.relationship('BizStockAmount', back_populates='brand')    # 品牌库存数量
    brand_io = db.relationship('BizStockHistory', back_populates='brand')       # 品牌出入库履历
    bg_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))           # 所属法人ID
    bg = db.relationship('BizCompany', back_populates='brands')                 # 所属法人
'''
品牌型号表
'''
class BizBrandModel(BaseModel, db.Model):
    code = db.Column(db.String(128))                                              # 型号代码
    name = db.Column(db.String(128))                                              # 型号名称
    brand_id = db.Column(db.String(32), db.ForeignKey('biz_brand_master.id'))     # 所属品牌ID
    brand = db.relationship('BizBrandMaster', back_populates='models')            # 所属品牌
    assets = db.relationship('BizAssetMaster', back_populates='model')            # 资产
    model_amount = db.relationship('BizStockAmount', back_populates='model')      # 型号库存数量
    model_io = db.relationship('BizStockHistory', back_populates='model')         # 型号库存数量
'''
定时邮件配置表
'''
class BizEmailConfig(BaseModel, db.Model):
    code = db.Column(db.String(64))         # 定时任务类型代码
    name = db.Column(db.String(128))        # 定时任务类型代码(维保到期提醒/借用到期提醒/预计维修搬入日提醒等)
    email_to = db.Column(db.String(256))    # 收件人(以逗号隔开)
    email_cc = db.Column(db.String(256))    # 参照人(以逗号隔开)
'''
资产申请登记
'''
class BizAssetApply(BaseModel, db.Model):
    apply_no = db.Column(db.String(32))     # 申请号:系统自动生成(规则:AY20220616+随机四位整数)
    draft_no = db.Column(db.String(32))     # 草案号(DooDream)
    receive_date = db.Column(db.Date())     # 接收日期
    company_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))                                          # 申请法人ID
    company = db.relationship('BizCompany', back_populates='applications', lazy=True, foreign_keys=[company_id])    # 申请法人
    department_id = db.Column(db.String(32), db.ForeignKey('biz_department.id'))                                    # 申请部门ID
    department = db.relationship('BizDepartment', back_populates='applications')                                    # 申请部门
    applicant_id = db.Column(db.String(32), db.ForeignKey('biz_employee.id'))                                       # 申请人ID
    applicant = db.relationship('BizEmployee', back_populates='applications')                                       # 申请人
    applicant_pos = db.Column(db.String(48))                                                                        # 申请人职位
    class2_id = db.Column(db.String(32))                                                                            # 资产分类-弃用
    class3_id = db.Column(db.String(32))                                                                            # 资产名称-弃用
    brand_id = db.Column(db.String(32))                                                                             # 品牌-弃用
    model_id = db.Column(db.String(32))                                                                             # 型号-弃用
    file_path = db.Column(db.String(128))                                                                           # 附件路径
    summary = db.Column(db.Text)                                                                                    # 申请概要
    amount = db.Column(db.Integer)                                                                                  # 申请数量-合计明细后更新即可
    bg_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))                                               # 单据所属法人ID
    bg = db.relationship('BizCompany', back_populates='apply_bills', lazy=True, foreign_keys=[bg_id])               # 单据所属法人
    buy_bill = db.relationship('BizAssetBuy', uselist=False, back_populates='application')                          # 购买订单-弃用
    # 2023年升级新增字段
    e_approval_app_dt = db.Column(db.Date())    # E-Approval申请日期
    e_approval_fin_dt = db.Column(db.Date())    # E-Approval完成日期
    e_approval_url = db.Column(db.String(256))  # E-Approval链接URL
    items = db.relationship('BizAssetItem', back_populates='apply')    # 申请明细
    # 资产分类
    @property
    def class2(self):
        return BizAssetClass.query.get(self.class2_id) if self.class2_id else None
    # 资产名称
    @property
    def class3(self):
        return BizAssetClass.query.get(self.class3_id) if self.class3_id else None
    # 品牌
    @property
    def brand(self):
        return BizBrandMaster.query.get(self.brand_id) if self.brand_id else None
    # 型号
    @property
    def model(self):
        return BizBrandModel.query.get(self.model_id) if self.model_id else None
class RelAssetBuyItem(BaseModel, db.Model):
    asset_item_id = db.Column(db.String(32), db.ForeignKey('biz_asset_item.id'))    # 资产申请明细ID
    asset_buy_id = db.Column(db.String(32), db.ForeignKey('biz_asset_buy.id'))      # 资产购买订单ID
    amount = db.Column(db.Integer)                                                  # 购买数量
    is_stock_in = db.Column(db.Boolean, default=False)                              # 是否已入库(默认否)
'''
资产申请/购买明细
实现逻辑：
    1. 临时ID-用于表单中新增时执行明细异步增删改查，修改时按照apply_id来执行异步增删改查
    2. 每次新增/编辑申请单时，先执行申请明细查询，apply_id为空的执行物理删除，清除垃圾数据
'''
class BizAssetItem(BaseModel, db.Model):
    tmp_id = db.Column(db.String(32))           # 临时ID
    class2_id = db.Column(db.String(32))        # 资产分类
    class3_id = db.Column(db.String(32))        # 资产名称
    brand_id = db.Column(db.String(32))         # 品牌
    model_id = db.Column(db.String(32))         # 型号
    user_id = db.Column(db.String(32))          # 使用人-对应雇员信息
    amount = db.Column(db.Integer, default=1)   # 申请数量-默认为1
    std_model_id = db.Column(db.String(32))     # 标准型号-对应标准型号ID
    is_bought = db.Column(db.Boolean, default=False)    # 已购买（默认否）
    is_stored = db.Column(db.Boolean, default=False)    # 已入库（默认否）
    apply_id = db.Column(db.String(32), db.ForeignKey('biz_asset_apply.id'))    # 申请单ID
    apply = db.relationship('BizAssetApply', back_populates='items')            # 申请单
    buy_bills = db.relationship('BizAssetBuy', secondary='rel_asset_buy_item', back_populates='apply_items')    # 购买订单多个
    # 使用者
    @property
    def user(self):
        return BizEmployee.query.get(self.user_id) if self.user_id else None
    # 标准型号
    @property
    def standard_model(self):
        return BizStandardModel.query.get(self.std_model_id) if self.std_model_id else None
    # 资产分类
    @property
    def class2(self):
        return BizAssetClass.query.get(self.class2_id) if self.class2_id else None
    # 资产名称
    @property
    def class3(self):
        return BizAssetClass.query.get(self.class3_id) if self.class3_id else None
    # 品牌
    @property
    def brand(self):
        return BizBrandMaster.query.get(self.brand_id) if self.brand_id else None
    # 型号
    @property
    def model(self):
        return BizBrandModel.query.get(self.model_id) if self.model_id else None
'''
资产购买登记(和资产申请登记1:1)
'''
class BizAssetBuy(BaseModel, db.Model):
    buy_no = db.Column(db.String(32))           # 购买号:系统自动生成(规则:BY20220616+随机四位整数)
    draft_no = db.Column(db.String(32))         # 执行起案号(DooDream)
    bill_date = db.Column(db.Date())            # 订单日期
    total_price = db.Column(db.String(24))      # 购买总价
    receive_due_date = db.Column(db.Date())     # 预计到货日期
    application_no = db.Column(db.String(32))   # 申请单号
    application_id = db.Column(db.String(32), db.ForeignKey('biz_asset_apply.id'))  # 资产申请单ID
    application = db.relationship('BizAssetApply', back_populates='buy_bill')       # 资产申请单
    assets = db.relationship('BizAssetMaster', back_populates='buy_bill')           # 购买资产明细
    bg_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))               # 所属法人ID
    bg = db.relationship('BizCompany', back_populates='buy_bills')                  # 所属法人
    apply_items = db.relationship('BizAssetItem', secondary='rel_asset_buy_item', back_populates='buy_bills')  # 申请明细

'''
入库登记表--资产审批
'''
class BizStockIn(BaseModel, db.Model):
    in_no = db.Column(db.String(32))                                        # 入库登记号:系统自动生成(规则:IN20220616+随机四位整数)
    in_date = db.Column(db.Date())                                          # 入库日期
    charger_id = db.Column(db.String(32), db.ForeignKey('sys_user.id'))     # 入库人员(用户ID)
    state_id = db.Column(db.String(32), db.ForeignKey('sys_enum.id'))       # 单据审批状态(字典代码:D004已提交/审批中/审批完成)
    audit_line_id = db.Column(db.String(32), db.ForeignKey('audit_line.id'))  # 审批线ID
    charger = db.relationship('SysUser', back_populates='in_charger')       # 入库人员
    state = db.relationship('SysEnum', back_populates='in_state', lazy=True, foreign_keys=[state_id])  # 审批状态
    assets = db.relationship('BizAssetMaster', back_populates='in_bill')    # 入库资产明细
    audit_line = db.relationship('AuditLine', back_populates='stock_in_bills')  # 审批线
    bg_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))       # 所属法人ID
    bg = db.relationship('BizCompany', back_populates='in_bills')           # 所属法人
'''
出库明细清单表
'''
class RelAssetOutItem(BaseModel, db.Model):
    out_bill_id = db.Column(db.String(32), db.ForeignKey('biz_stock_out.id'))       # 出库单ID
    asset_id = db.Column(db.String(32), db.ForeignKey('biz_asset_master.id'))       # 资产ID
    amount = db.Column(db.Integer)                                                  # 出库数量
    give_by_id = db.Column(db.String(32), db.ForeignKey('biz_employee.id'))         # 发放人ID
    take_by_id = db.Column(db.String(32), db.ForeignKey('biz_employee.id'))         # 领用人ID
    return_by_id = db.Column(db.String(32), db.ForeignKey('biz_employee.id'))       # 返回人ID
    give_by = db.relationship('BizEmployee', back_populates='asset_give_by', lazy=True, foreign_keys=[give_by_id])          # 发放人
    take_by = db.relationship('BizEmployee', back_populates='asset_take_by', lazy=True, foreign_keys=[take_by_id])          # 领用人
    return_by = db.relationship('BizEmployee', back_populates='asset_return_by', lazy=True, foreign_keys=[return_by_id])    # 返还人
    back_date = db.Column(db.Date())                                                # 返还日期
    back_reason = db.Column(db.Text())                                              # 返还原因
'''
出库登记表
'''
class BizStockOut(BaseModel, db.Model):
    out_no = db.Column(db.String(32))                                       # 出库登记号:系统自动生成(规则:OUT20220616+随机四位整数)
    out_date = db.Column(db.Date())                                         # 出库日期
    back_date = db.Column(db.Date())                                        # 借用预计归还日期(仅限类型为借用发放时填写,用于借用到期提醒任务)
    out_type_id = db.Column(db.String(32), db.ForeignKey('sys_enum.id'))    # 出库类型(字典:D005 领用发放/借用发放)
    charger_id = db.Column(db.String(32), db.ForeignKey('sys_user.id'))     # 出库人员(用户ID)
    state_id = db.Column(db.String(32), db.ForeignKey('sys_enum.id'))       # 单据审批状态(字典代码:D004已提交/审批中/审批完成)
    audit_line_id = db.Column(db.String(32), db.ForeignKey('audit_line.id'))# 审批线ID
    summary = db.Column(db.Text)                                            # 出库概要
    charger = db.relationship('SysUser', back_populates='out_charger')      # 出库人员
    out_type = db.relationship('SysEnum', back_populates='out_type', lazy=True, foreign_keys=[out_type_id])   # 出库类型
    state = db.relationship('SysEnum', back_populates='out_state', lazy=True, foreign_keys=[state_id])        # 审批状态
    audit_line = db.relationship('AuditLine', back_populates='stock_out_bills') # 审批线
    assets = db.relationship('BizAssetMaster', secondary='rel_asset_out_item', back_populates='out_bills')
    bg_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))       # 所属法人ID
    bg = db.relationship('BizCompany', back_populates='out_bills')          # 所属法人
'''
资产类型层级关系(仅限三级)
'''
class RelAssetClass(BaseModel, db.Model):
    parent_class_id = db.Column(db.String(32), db.ForeignKey('biz_asset_class.id'))
    parent_class = db.relationship('BizAssetClass', foreign_keys=[parent_class_id], back_populates='parent_class', lazy='joined')     # 父类型
    child_class_id = db.Column(db.String(32), db.ForeignKey('biz_asset_class.id'))
    child_class = db.relationship('BizAssetClass', foreign_keys=[child_class_id], back_populates='child_class', lazy='joined')        # 子类型
'''
资产类型
'''
class BizAssetClass(BaseModel, db.Model):
    code = db.Column(db.String(32))                                         # 资产类型代码
    name = db.Column(db.Text)                                               # 资产类型名称
    grade = db.Column(db.Integer)                                           # 级别(仅限三级)
    unit = db.Column(db.String(12))                                         # 计量单位:只有第三级维护该栏位信息
    bg_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))       # 所属法人ID
    bg = db.relationship('BizCompany', back_populates='asset_classes')      # 所属法人
    class1_assets = db.relationship('BizAssetMaster', back_populates='class1', lazy=True, primaryjoin='BizAssetMaster.class1_id == BizAssetClass.id')       # 一级分类资产
    class2_assets = db.relationship('BizAssetMaster', back_populates='class2', lazy=True, primaryjoin='BizAssetMaster.class2_id == BizAssetClass.id')       # 二级分类资产
    class3_assets = db.relationship('BizAssetMaster', back_populates='class3', lazy=True, primaryjoin='BizAssetMaster.class3_id == BizAssetClass.id')       # 三级分类资产
    class1_history = db.relationship('BizStockHistory', back_populates='class1', lazy=True, primaryjoin='BizStockHistory.class1_id == BizAssetClass.id')    # 一级分类资产出入库履历
    class2_history = db.relationship('BizStockHistory', back_populates='class2', lazy=True, primaryjoin='BizStockHistory.class2_id == BizAssetClass.id')    # 二级分类资产出入库履历
    class3_history = db.relationship('BizStockHistory', back_populates='class3', lazy=True, primaryjoin='BizStockHistory.class3_id == BizAssetClass.id')    # 三级分类资产出入库履历
    class1_amount = db.relationship('BizStockAmount', back_populates='class1', lazy=True, primaryjoin='BizStockAmount.class1_id == BizAssetClass.id')       # 一级分类资产库存
    class2_amount = db.relationship('BizStockAmount', back_populates='class2', lazy=True, primaryjoin='BizStockAmount.class2_id == BizAssetClass.id')       # 二级分类资产库存
    class3_amount = db.relationship('BizStockAmount', back_populates='class3', lazy=True, primaryjoin='BizStockAmount.class3_id == BizAssetClass.id')       # 三级分类资产库存
    parent_class = db.relationship('RelAssetClass', foreign_keys=[RelAssetClass.parent_class_id], back_populates='parent_class', lazy='dynamic', cascade='all')  # 父类型
    child_class = db.relationship('RelAssetClass', foreign_keys=[RelAssetClass.child_class_id], back_populates='child_class', lazy='dynamic', cascade='all')     # 子类型
    # 设置父类型
    def set_parent_class(self, clazz):
        '''
        逻辑：首先判断是否已经维护父类型，如果存在则执行删除后新增
        :param clazz:
        :return:
        '''
        ref = RelAssetClass.query.filter_by(child_class_id=self.id).first()
        if ref:
            db.session.delete(ref)
            db.session.commit()
        parent = RelAssetClass(id=uuid.uuid4().hex, child_class=self, parent_class=clazz)
        db.session.add(parent)
        db.session.commit()
    @property
    def get_parent_class(self):
        clazz = RelAssetClass.query.filter_by(child_class_id=self.id).first()
        return clazz.parent_class if clazz else None
    # 设置子类型
    def set_child_class(self, clazz):
        '''
        逻辑：首先解除子类型原有的类型关系，然后再添加到当前类型下
        :param clazz:
        :return:
        '''
        ref = RelAssetClass.query.filter_by(child_class_id=clazz.id).first()
        if ref:
            db.session.delete(ref)
            db.session.commit()
        child = RelAssetClass(id=uuid.uuid4().hex, child_class=clazz, parent_class=self)
        db.session.add(child)
        db.session.commit()
    @property
    def get_child_class(self):
        return RelAssetClass.query.filter_by(parent_class_id=self.id).order_by(RelAssetClass.createtime_loc.desc()).all()
'''
标准型号
'''
class BizStandardModel(BaseModel, db.Model):
    name = db.Column(db.String(128))            # 标准型号名称
    code = db.Column(db.String(32))             # 标准型号代码
    class2_id = db.Column(db.String(32))        # 资产分类
    class3_id = db.Column(db.String(32))        # 资产名称
    brand_id = db.Column(db.String(32))         # 品牌
    model_id = db.Column(db.String(32))         # 型号
    amount = db.Column(db.Float)                # 金额
    cpu = db.Column(db.String(32))              # CPU
    memory = db.Column(db.String(32))           # 内存
    disk = db.Column(db.String(32))             # 硬盘
    screen_ratio = db.Column(db.String(32))     # 显示器分辨率
    screen_size = db.Column(db.String(32))      # 显示器尺寸
    inf = db.Column(db.String(32))              # 接口
    system_os = db.Column(db.String(32))        # 操作系统
    battery = db.Column(db.String(32))          # 电池
    power = db.Column(db.String(32))            # 功率
    remark = db.Column(db.String(32))           # 备注
    vendor_id = db.Column(db.String(32))        # 供应商
    warranty = db.Column(db.Integer)            # 保修期（天）
    # 资产分类
    @property
    def class2(self):
        return BizAssetClass.query.get(self.class2_id) if self.class2_id else None
    # 资产名称
    @property
    def class3(self):
        return BizAssetClass.query.get(self.class3_id) if self.class3_id else None
    # 品牌
    @property
    def brand(self):
        return BizBrandMaster.query.get(self.brand_id) if self.brand_id else None
    # 型号
    @property
    def model(self):
        return BizBrandModel.query.get(self.model_id) if self.model_id else None
    @property
    def vendor(self):
        return BizVendorMaster.query.get(self.vendor_id) if self.vendor_id else None

'''
资产附属关系:某个资产附属于另一个资产;应用场景->为了某个资产而购买的资产/耗材,比如笔记本电脑购买内存条
'''
class RelAssetMaster(BaseModel, db.Model):
    parent_asset_id = db.Column(db.String(32), db.ForeignKey('biz_asset_master.id'))
    parent_asset = db.relationship('BizAssetMaster', foreign_keys=[parent_asset_id], back_populates='parent_asset', lazy='joined') # 主资产
    child_asset_id = db.Column(db.String(32), db.ForeignKey('biz_asset_master.id'))
    child_asset = db.relationship('BizAssetMaster', foreign_keys=[child_asset_id], back_populates='child_asset', lazy='joined')    # 附资产
'''
资产主数据表
'''
class BizAssetMaster(BaseModel, db.Model):
    is_asset = db.Column(db.Integer)                                            # 资产耗材区分(1:资产 0:耗材)
    buy_bill_id = db.Column(db.String(32), db.ForeignKey('biz_asset_buy.id'))   # 购买订单
    buy_date = db.Column(db.Date())                                             # 购买日期
    buy_fee = db.Column(db.String(32))                                          # 购买金额
    in_bill_id = db.Column(db.String(32), db.ForeignKey('biz_stock_in.id'))     # 入库订单
    code = db.Column(db.String(32))                 # 资产编码(编码规则:AS20220617+随机四位整数)
    sap_code = db.Column(db.String(32))             # SAP资产编码(只有资产有,耗材无)
    name = db.Column(db.String(128))                # 资产名称-该栏位暂不使用
    is_new = db.Column(db.Boolean, default=True)    # 是否新的(一手or二手);资产返还/变更资产使用者时置为False
    reg_date = db.Column(db.Date())                 # 登记日期
    reg_amount = db.Column(db.Integer)              # 登记数量(登记资产只能是1;耗材>=1)
    status_id = db.Column(db.String(32), db.ForeignKey('sys_enum.id'))          # 资产状态(字典代码:D003枚举维护:在库/接收待确认/已发放/借用中/待维修/维修中/维修完成/待报废/已报废/盘亏)
    is_out = db.Column(db.Boolean, default=False)                               # 是否出库:默认未出库
    bar_path = db.Column(db.String(500))                                        # 条形码路径
    qr_path = db.Column(db.String(500))                                         # 二维码路径
    class1_id = db.Column(db.String(32), db.ForeignKey('biz_asset_class.id'))   # 一级分类(资产/耗材?)
    class2_id = db.Column(db.String(32), db.ForeignKey('biz_asset_class.id'))   # 二级分类
    class3_id = db.Column(db.String(32), db.ForeignKey('biz_asset_class.id'))   # 三级分类
    brand_id = db.Column(db.String(32), db.ForeignKey('biz_brand_master.id'))   # 品牌ID
    model_id = db.Column(db.String(32), db.ForeignKey('biz_brand_model.id'))    # 型号ID
    manager_id = db.Column(db.String(32), db.ForeignKey('biz_employee.id'))     # 管理担当ID
    user_id = db.Column(db.String(32), db.ForeignKey('biz_employee.id'))        # 使用者ID
    department_id = db.Column(db.String(32), db.ForeignKey('biz_department.id'))# 使用者部门ID
    company_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))      # 使用者法人ID
    vendor_id = db.Column(db.String(32), db.ForeignKey('biz_vendor_master.id')) # 供应商ID
    store_id = db.Column(db.String(32), db.ForeignKey('biz_store_master.id'))   # 存放仓库ID
    maintain_expired = db.Column(db.Boolean, default=False)                     # 是否出保:默认未出保，开发一定时任务根据维保信息更新该栏位，一天凌晨执行一次
    buy_bill = db.relationship('BizAssetBuy', back_populates='assets')          # 资产购买单
    in_bill = db.relationship('BizStockIn', back_populates='assets')            # 资产入库单
    class1 = db.relationship('BizAssetClass', back_populates='class1_assets', lazy=True, foreign_keys=[class1_id])  # 一级分类
    class2 = db.relationship('BizAssetClass', back_populates='class2_assets', lazy=True, foreign_keys=[class2_id])  # 二级分类
    class3 = db.relationship('BizAssetClass', back_populates='class3_assets', lazy=True, foreign_keys=[class3_id])  # 三级分类
    brand = db.relationship('BizBrandMaster', back_populates='assets')          # 品牌
    model = db.relationship('BizBrandModel', back_populates='assets')           # 型号
    manager = db.relationship('BizEmployee', back_populates='managed_assets', lazy=True, foreign_keys=[manager_id]) # 管理担当
    user = db.relationship('BizEmployee', back_populates='used_assets', lazy=True, foreign_keys=[user_id])          # 使用者
    department = db.relationship('BizDepartment', back_populates='assets')                                          # 使用者所属部门
    company = db.relationship('BizCompany', back_populates='biz_assets', lazy=True, foreign_keys=[company_id])      # 使用者所属法人
    vendor = db.relationship('BizVendorMaster', back_populates='assets')                                            # 供应商
    store = db.relationship('BizStoreMaster', back_populates='assets')                                              # 存放仓库
    properties = db.relationship('BizAssetProperty', uselist=False, back_populates='asset_master')                  # 资产属性(耗材无)
    procedures = db.relationship('BizAssetProcedure', uselist=False, back_populates='asset_master')                  # 资产属性(耗材无)
    maintains = db.relationship('BizAssetMaint', back_populates='master')                                           # 资产保修信息
    status = db.relationship('SysEnum', back_populates='asset_status', lazy=True, foreign_keys=[status_id])         # 资产状态
    out_bills = db.relationship('BizStockOut', secondary='rel_asset_out_item', back_populates='assets')             # 出库单
    repair_history = db.relationship('BizAssetRepair', back_populates='asset')                                      # 维修履历
    change_history = db.relationship('BizAssetChange', back_populates='asset')                                      # 变更履历
    scrap = db.relationship('BizAssetScrap', uselist=False, back_populates='asset')                                 # 报废记录
    check_bills = db.relationship('BizAssetCheck', secondary='rel_asset_check_item', back_populates='assets')       # 资产盘点单
    stock_history = db.relationship('BizStockHistory', back_populates='asset')                                      # 资产出入库履历
    bg_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))                                               # 所属法人ID
    bg = db.relationship('BizCompany', back_populates='sys_assets', lazy=True, foreign_keys=[bg_id])                # 所属法人
    parent_asset = db.relationship('RelAssetMaster', foreign_keys=[RelAssetMaster.parent_asset_id], back_populates='parent_asset', lazy='dynamic', cascade='all')   # 主资产
    child_asset = db.relationship('RelAssetMaster', foreign_keys=[RelAssetMaster.child_asset_id], back_populates='child_asset', lazy='dynamic', cascade='all')      # 附资产
    # 设置主资产
    def set_parent_asset(self, asset):
        '''
        逻辑：首先判断是否已经维护主资产，如果存在则执行删除后新增
        :param asset:
        :return:
        '''
        ref = RelAssetMaster.query.filter_by(child_asset_id=self.id).first()
        if ref:
            db.session.delete(ref)
            db.session.commit()
        parent = RelAssetMaster(id=uuid.uuid4().hex, child_asset=self, parent_asset=asset)
        db.session.add(parent)
        db.session.commit()

    @property
    def get_parent_asset(self):
        rel = RelAssetMaster.query.filter_by(child_asset_id=self.id).first()
        return rel.parent_asset if rel else None

    # 设置附资产
    def set_child_asset(self, asset):
        '''
        逻辑：首先解除附资产原有的资产关系，然后再添加到当前资产下
        :param asset:
        :return:
        '''
        ref = RelAssetMaster.query.filter_by(child_asset_id=asset.id).first()
        if ref:
            db.session.delete(ref)
            db.session.commit()
        child = RelAssetMaster(id=uuid.uuid4().hex, child_asset=asset, parent_asset=self)
        db.session.add(child)
        db.session.commit()

    @property
    def get_child_asset(self):
        return RelAssetMaster.query.filter_by(parent_asset_id=self.id).order_by(RelAssetMaster.createtime_loc.desc()).all()
'''
资产属性表(资产主数据1:1)
'''
class BizAssetProperty(BaseModel, db.Model):
    cpu = db.Column(db.String(32))              # CPU
    memory = db.Column(db.String(32))           # 内存
    disk = db.Column(db.String(32))             # 硬盘
    screen_ratio = db.Column(db.String(32))     # 显示器分辨率
    screen_size = db.Column(db.String(32))      # 显示器尺寸
    inf = db.Column(db.String(32))              # 接口
    system_os = db.Column(db.String(32))        # 操作系统
    serial_no = db.Column(db.String(32))        # 序列号
    mac = db.Column(db.String(32))              # MAC地址
    battery = db.Column(db.String(32))          # 电池
    power = db.Column(db.String(32))            # 功率
    remark = db.Column(db.String(32))           # 备注
    asset_master_id = db.Column(db.String(32), db.ForeignKey('biz_asset_master.id'))   # 资产主数据ID
    asset_master = db.relationship('BizAssetMaster', back_populates='properties')      # 资产主数据
'''
结算BG基础信息
'''
class BizPaymentBgMaster(BaseModel, db.Model):
    bg_code = db.Column(db.String(12))      # 结算BG代码
    bg_order = db.Column(db.String(24))     # 结算BG Order号
    bg_year = db.Column(db.String(4))       # 结算BG年份
    company_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))
    company = db.relationship('BizCompany', back_populates='payment_bgs')
'''
资产结算信息表
'''
class BizAssetProcedure(BaseModel, db.Model):
    payment_dt = db.Column(db.Date())                       # 结算日期
    payment_bg_id = db.Column(db.String(32))                # 结算BG
    payment_invoice = db.Column(db.Boolean, default=False)  # 结算发票
    payment_check = db.Column(db.Boolean, default=False)    # 结算验收证表
    payment_signet = db.Column(db.Boolean, default=False)   # 结算验收单章
    asset_master_id = db.Column(db.String(32), db.ForeignKey('biz_asset_master.id'))    # 资产主数据ID
    asset_master = db.relationship('BizAssetMaster', back_populates='procedures')       # 资产主数据
    @property
    def payment_bg(self):
        return BizPaymentBgMaster.query.get(self.payment_bg_id) if self.payment_bg_id else None
'''
维保信息
'''
class BizAssetMaint(BaseModel, db.Model):
    start_date = db.Column(db.Date())               # 维保开始日期
    expire_date = db.Column(db.Date())              # 维保结束日期
    content = db.Column(db.Text)                    # 维保内容:只在续保时维护，新增时为空
    free = db.Column(db.Boolean, default=False)     # 是否免费维保:新增时为True，其他为False
    draft_no = db.Column(db.String(32))             # 续保draft号:只在续保时维护，新增时为空
    price = db.Column(db.String(24))                # 续保费:只在续保时维护，新增时为0
    check = db.Column(db.Boolean, default=True)     # 是否check维保是否到期
    vendor_id = db.Column(db.String(32), db.ForeignKey('biz_vendor_master.id'))         # 供应商ID
    vendor = db.relationship('BizVendorMaster', back_populates='maintains')             # 供应商
    master_id = db.Column(db.String(32), db.ForeignKey('biz_asset_master.id'))          # 资产主数据ID
    master = db.relationship('BizAssetMaster', back_populates='maintains')              # 主资产
'''
资产变更履历表
'''
class BizAssetChange(BaseModel, db.Model):
    change_date = db.Column(db.Date())                                              # 变更日期
    asset_id = db.Column(db.String(32), db.ForeignKey('biz_asset_master.id'))       # 资产ID
    asset = db.relationship('BizAssetMaster', back_populates='change_history')      # 资产
    old_holder_id = db.Column(db.String(32), db.ForeignKey('biz_employee.id'))      # 上一持有者ID
    new_holder_id = db.Column(db.String(32), db.ForeignKey('biz_employee.id'))      # 最新持有者ID
    old_holder = db.relationship('BizEmployee', back_populates='asset_old_holder', lazy=True, foreign_keys=[old_holder_id])  # 上一持有者
    new_holder = db.relationship('BizEmployee', back_populates='asset_new_holder', lazy=True, foreign_keys=[new_holder_id])  # 最新持有者
'''
出入库履历
'''
class BizStockHistory(BaseModel, db.Model):
    bill_no = db.Column(db.String(32))                                          # 出入库单号
    asset_id = db.Column(db.String(32), db.ForeignKey('biz_asset_master.id'))   # 资产ID
    code = db.Column(db.String(32))                                             # 资产编码
    sap_code = db.Column(db.String(32))                                         # SAP资产编码
    class1_id = db.Column(db.String(32), db.ForeignKey('biz_asset_class.id'))   # 一级分类
    class2_id = db.Column(db.String(32), db.ForeignKey('biz_asset_class.id'))   # 二级分类
    class3_id = db.Column(db.String(32), db.ForeignKey('biz_asset_class.id'))   # 三级分类
    brand_id = db.Column(db.String(32), db.ForeignKey('biz_brand_master.id'))   # 品牌ID
    model_id = db.Column(db.String(32), db.ForeignKey('biz_brand_model.id'))    # 型号ID
    io_type = db.Column(db.Integer)                                             # 出入库区分(1:入库; 0:出库)
    io_class_id = db.Column(db.String(32), db.ForeignKey('sys_enum.id'))        # 出入库类型ID
    amount = db.Column(db.Integer)                                              # 出/入库数量
    remark = db.Column(db.String(500))                                          # 备注
    asset = db.relationship('BizAssetMaster', back_populates='stock_history')   # 资产
    class1 = db.relationship('BizAssetClass', back_populates='class1_history', lazy=True, foreign_keys=[class1_id])  # 一级分类
    class2 = db.relationship('BizAssetClass', back_populates='class2_history', lazy=True, foreign_keys=[class2_id])  # 二级分类
    class3 = db.relationship('BizAssetClass', back_populates='class3_history', lazy=True, foreign_keys=[class3_id])  # 三级分类
    brand = db.relationship('BizBrandMaster', back_populates='brand_io')        # 品牌
    model = db.relationship('BizBrandModel', back_populates='model_io')         # 型号
    io_class = db.relationship('SysEnum', back_populates='stock_io_class')      # 出入库类型
    bg_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))           # 所属法人ID
    bg = db.relationship('BizCompany', back_populates='stock_history')          # 所属法人
'''
库存余额
'''
class BizStockAmount(BaseModel, db.Model):
    class1_id = db.Column(db.String(32), db.ForeignKey('biz_asset_class.id'))   # 一级分类ID
    class2_id = db.Column(db.String(32), db.ForeignKey('biz_asset_class.id'))   # 二级分类ID
    class3_id = db.Column(db.String(32), db.ForeignKey('biz_asset_class.id'))   # 三级分类ID
    brand_id = db.Column(db.String(32), db.ForeignKey('biz_brand_master.id'))   # 品牌ID
    model_id = db.Column(db.String(32), db.ForeignKey('biz_brand_model.id'))    # 型号ID
    amount = db.Column(db.Integer)                                              # 库存数量
    class1 = db.relationship('BizAssetClass', back_populates='class1_amount', lazy=True, foreign_keys=[class1_id])  # 一级分类
    class2 = db.relationship('BizAssetClass', back_populates='class2_amount', lazy=True, foreign_keys=[class2_id])  # 二级分类
    class3 = db.relationship('BizAssetClass', back_populates='class3_amount', lazy=True, foreign_keys=[class3_id])  # 三级分类
    brand = db.relationship('BizBrandMaster', back_populates='brand_amount')    # 品牌
    model = db.relationship('BizBrandModel', back_populates='model_amount')     # 型号
    bg_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))  # 所属法人ID
    bg = db.relationship('BizCompany', back_populates='stock_amount')  # 所属法人
'''
维修履历表 - 只有资产有维修履历，耗材无
'''
class BizAssetRepair(BaseModel, db.Model):
    repair_no = db.Column(db.String(32))                                        # 维修单号(编码规则:AR20220617+随机四位整数)
    request_draft = db.Column(db.String(32))                                    # 维修申请Draft
    request_accept_dt = db.Column(db.Date())                                    # 维修申请接收日期
    requested_by_id = db.Column(db.String(32), db.ForeignKey('biz_employee.id'))# 维修申请人ID
    repair_draft = db.Column(db.String(32))                                     # 维修Draft
    repair_handler_id = db.Column(db.String(32), db.ForeignKey('biz_employee.id')) # IT维修处理担当ID
    repair_type_id = db.Column(db.String(32), db.ForeignKey('sys_enum.id'))     # 故障维修类型(字典:D006)
    repair_state_id = db.Column(db.String(32), db.ForeignKey('sys_enum.id'))    # 故障维修状态(字典:D007)
    repair_part_id = db.Column(db.String(32), db.ForeignKey('sys_enum.id'))     # 故障部位(字典:D011)
    repair_content = db.Column(db.String(256))                                  # 维修项目内容
    pre_finish_date = db.Column(db.Date())                                      # 预计维修完成日期
    rel_finish_date = db.Column(db.Date())                                      # 实际维修完成日期
    fee = db.Column(db.String(24))                                              # 维修费用
    out_date = db.Column(db.Date())                                             # 搬出日期
    pre_in_date = db.Column(db.Date())                                          # 预计搬入日期
    real_in_date = db.Column(db.Date())                                         # 实际搬入日期
    asset_id = db.Column(db.String(32), db.ForeignKey('biz_asset_master.id'))   # 资产ID
    asset = db.relationship('BizAssetMaster', back_populates='repair_history')  # 资产
    requested_by = db.relationship('BizEmployee', back_populates='repair_request_list', lazy=True, foreign_keys=[requested_by_id])    # 维修申请人
    repair_handler = db.relationship('BizEmployee', back_populates='repair_handle_list', lazy=True, foreign_keys=[repair_handler_id]) # 维修处理担当
    repair_type = db.relationship('SysEnum', back_populates='repair_type', lazy=True, foreign_keys=[repair_type_id])    # 故障维修类型
    repair_state = db.relationship('SysEnum', back_populates='repair_state', lazy=True, foreign_keys=[repair_state_id]) # 故障维修状态
    bg_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))           # 所属法人ID
    bg = db.relationship('BizCompany', back_populates='asset_repair')           # 所属法人

    @property
    def repair_part(self):
        if self.repair_part_id:
            return SysEnum.query.get(self.repair_part_id)
        return None
'''
资产报废表-资产报废，耗材无法报废，和master -> 1:1
'''
class BizAssetScrap(BaseModel, db.Model):
    scrap_no = db.Column(db.String(32))                                         # 报废单号(编码规则:AS20220617+随机四位整数)
    scrap_date = db.Column(db.Date())                                           # 报废判定日期
    scraper_id = db.Column(db.String(32), db.ForeignKey('sys_user.id'))         # 报废判定人ID
    scrap_reason_id = db.Column(db.String(32), db.ForeignKey('sys_enum.id'))    # 报废原因(字典:D008)
    scrap_state_id = db.Column(db.String(32), db.ForeignKey('sys_enum.id'))     # 报废状态(字典:D009)
    scrap_draft = db.Column(db.String(40))                                      # 报废Draft号
    finish_date = db.Column(db.Date())                                          # 报废完成日期
    sap_scrap = db.Column(db.Boolean, default=False)                            # SAP是否报废,默认否
    scraper = db.relationship('SysUser', back_populates='asset_scraper')        # 报废判定人
    scrap_reason = db.relationship('SysEnum', back_populates='scrap_reason', lazy=True, foreign_keys=[scrap_reason_id]) # 报废原因
    scrap_state = db.relationship('SysEnum', back_populates='scrap_state', lazy=True, foreign_keys=[scrap_state_id])    # 报废状态
    asset_id = db.Column(db.String(32), db.ForeignKey('biz_asset_master.id'))   # 资产ID
    asset = db.relationship('BizAssetMaster', back_populates='scrap')           # 资产
    bg_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))           # 所属法人ID
    bg = db.relationship('BizCompany', back_populates='asset_scrap')            # 所属法人
'''
资产盘点明细表-盘点单&资产Master(N:N)
'''
class RelAssetCheckItem(BaseModel, db.Model):
    check_id = db.Column(db.String(32), db.ForeignKey('biz_asset_check.id'))    # 盘点单ID
    asset_id = db.Column(db.String(32), db.ForeignKey('biz_asset_master.id'))   # 资产ID
    passed_biz = db.Column(db.Boolean, default=False)                           # 自盘点是否通过
    passed_it = db.Column(db.Boolean, default=False)                            # IT盘点是否通过
    more_or_less = db.Column(db.String(4))                                      # 盘点盈(Y)亏(K)
    remark = db.Column(db.Text)                                                 # 盘点结果备注
'''
资产盘点单
'''
class BizAssetCheck(BaseModel, db.Model):
    check_no = db.Column(db.String(32))                                     # 盘点单号(CK20220621+随机四位整数)
    check_year = db.Column(db.String(8))                                    # 盘点年度
    check_batch = db.Column(db.String(24))                                  # 盘点批次
    plan_start_date = db.Column(db.Date())                                  # 计划开始时间
    plan_finish_date = db.Column(db.Date())                                 # 计划完成时间
    checker_id = db.Column(db.String(32), db.ForeignKey('biz_employee.id')) # 盘点担当ID
    checker = db.relationship('BizEmployee', back_populates='asset_checker')# 盘点担当
    bg_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))       # 所属法人ID
    bg = db.relationship('BizCompany', back_populates='asset_check')        # 所属法人
    assets = db.relationship('BizAssetMaster', secondary='rel_asset_check_item', back_populates='check_bills')  # 盘点资产明细
'''
审批业务代码
'''
class AuditBizCode(BaseModel, db.Model):
    code = db.Column(db.String(24))  # 业务代码
    name = db.Column(db.String(40))  # 业务名称
    audit_lines = db.relationship('AuditLine', back_populates='biz_code')  # 业务审批线
    bg_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))   # 所属法人ID
    bg = db.relationship('BizCompany', back_populates='audit_codes')    # 所属法人
'''
审批线&审批角色关联表(N:N)
'''
class RelAuditLineRole(BaseModel, db.Model):
    audit_line_id = db.Column(db.String(32), db.ForeignKey('audit_line.id'))       # 审批线ID
    audit_role_id = db.Column(db.String(32), db.ForeignKey('audit_role.id'))       # 审批角色ID
    audit_grade = db.Column(db.Integer)                                            # 审批等级
'''
审批线
'''
class AuditLine(BaseModel, db.Model):
    code = db.Column(db.String(24))             # 审批线代码
    name = db.Column(db.String(40))             # 审批线名称
    remark = db.Column(db.Text)                 # 备注
    biz_code_id = db.Column(db.String(32), db.ForeignKey('audit_biz_code.id'))  # 审批业务代码ID
    biz_code = db.relationship('AuditBizCode', back_populates='audit_lines')    # 审批业务代码
    audit_roles = db.relationship('AuditRole', secondary='rel_audit_line_role', back_populates='audit_lines')  # 审批人
    audit_items = db.relationship('AuditItem', back_populates='audit_line')     # 审批单据
    stock_in_bills = db.relationship('BizStockIn', back_populates='audit_line')    # 入库单
    stock_out_bills = db.relationship('BizStockOut', back_populates='audit_line')   # 出库单
    bg_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))           # 所属法人ID
    bg = db.relationship('BizCompany', back_populates='audit_lines')            # 所属法人
'''
审批角色用户关联表(N:N)
'''
rel_audit_role_user = db.Table('rel_audit_role_user',
    db.Column('audit_role_id', db.String(32), db.ForeignKey('audit_role.id')),
    db.Column('user_id', db.String(32), db.ForeignKey('sys_user.id'))
)
'''
审批角色
'''
class AuditRole(BaseModel, db.Model):
    code = db.Column(db.String(24))  # 审批角色代码
    name = db.Column(db.String(40))  # 审批角色名称
    audit_lines = db.relationship('AuditLine', secondary='rel_audit_line_role', back_populates='audit_roles')   # 审批线
    auditors = db.relationship('SysUser', secondary='rel_audit_role_user', back_populates='audit_roles')        # 审批人
    bg_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))  # 所属法人ID
    bg = db.relationship('BizCompany', back_populates='audit_roles')   # 所属法人
'''
审批表:写入待审批时，同时写入审批履历表一条记录供审批WorkToDo画面查询即可
'''
class AuditItem(BaseModel, db.Model):
    audit_line_id = db.Column(db.String(32), db.ForeignKey('audit_line.id'))        # 审批线ID
    bill_no = db.Column(db.String(32))                                              # 审批单号
    bill_type = db.Column(db.String(12))                                            # 审批单据类型('SI':入库单BizStockIn, 'SO':出库单BizStockOut)
    audit_level = db.Column(db.Integer)                                             # 审批等级
    audit_finish = db.Column(db.Boolean, default=False)                             # 审批完成(默认False)
    resubmit = db.Column(db.Boolean, default=False)                                 # 重新提交(默认False),审批过程任意几点Reject后,置为True,相应单据修改后重新修改提交后置为False
    audit_line = db.relationship('AuditLine', back_populates='audit_items')         # 审批线
    audit_instances = db.relationship('AuditInstance', back_populates='audit_item')  # 审批履历=待办事项
    bg_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))               # 所属法人ID
    bg = db.relationship('BizCompany', back_populates='audit_items')                # 所属法人
'''
审批履历
'''
class AuditInstance(BaseModel, db.Model):
    audit_item_id = db.Column(db.String(32), db.ForeignKey('audit_item.id'))    # 审批单据ID
    finished = db.Column(db.Boolean, default=False)                             # 审批完成(默认False)-只要审批了就置为True
    approved = db.Column(db.Boolean, default=True)                              # 审批通过(默认True)
    remark = db.Column(db.Text)                                                 # 审批意见
    audit_item = db.relationship('AuditItem', back_populates='audit_instances') # 审批单据
    user_id = db.Column(db.String(32), db.ForeignKey('sys_user.id'))            # 审批人ID(多个用户任一审批完成即完成)
    user = db.relationship('SysUser', back_populates='audit_list')              # 审批人