from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField,  HiddenField, ValidationError, TextAreaField, SelectField, validators
from wtforms.validators import DataRequired
from com.models import BizAssetMaster, BizAssetBuy

class SearchForm(FlaskForm):
    class2 = SelectField('资产分类', [validators.optional()], choices=[])
    class3 = SelectField('资产名称', [validators.optional()], choices=[])
    brands = SelectField('品牌', [validators.optional()], choices=[])
    models = SelectField('型号', [validators.optional()], choices=[])
    companies = SelectField('法人', [validators.optional()], choices=[])
    code = StringField('资产编号', [validators.optional()])
    sap_code = StringField('SAP资产编号', [validators.optional()])
    used_by = StringField('使用者', [validators.optional()])
    buy_s = StringField('购买日期(FROM)', [validators.optional()])
    buy_e = StringField('购买日期(TO)', [validators.optional()])
    store_status = SelectField('库存状态', [validators.optional()], choices=[('0', '库存状态-All'), ('1', '在库'), ('2', '已出库')])
    asset_status = SelectField('资产状态', [validators.optional()], choices=[])
    used_by_id = HiddenField()
class AssetForm(FlaskForm):
    # 资产主数据
    id = HiddenField()
    class1 = HiddenField()
    class2 = SelectField('资产分类', validators=[DataRequired('请选择二级分类！')], choices=[])
    class3_id = HiddenField()
    buy_no = StringField('购买单号', validators=[DataRequired('请输入购买单号！')])
    buy_date = StringField('购买日期', validators=[DataRequired('请输入购买日期！')])
    buy_fee = StringField('购买费用', validators=[DataRequired('请输入购买费用！')])
    code = StringField('资产编号', [validators.optional()])
    sap_code = StringField('SAP资产编号', [validators.optional()])
    brands = SelectField('品牌', validators=[DataRequired('请选择品牌！')], choices=[])
    model_id = HiddenField()
    store = SelectField('存放位置', validators=[DataRequired('请选择存放位置！')], choices=[])
    reg_amount = IntegerField('登记数量')
    used_by = StringField('使用者', [validators.optional()])
    used_by_id = HiddenField()
    parent_asset = StringField('主资产', [validators.optional()])  # 此栏位主要标识为哪个资产购买的辅材，如笔记本购买内存条！选择方式
    parent_asset_id = HiddenField()
    # 维保信息
    vendors = SelectField('供应商', validators=[DataRequired('请选择供应商！')], choices=[])
    contact_person = StringField('联系人', validators=[DataRequired('请填写联系人！')])  # 无需保存关联Vendor信息
    contact_phone = StringField('联系电话', [validators.optional()])        # 无需保存关联Vendor信息
    start_date = StringField('维保开始日期', validators=[DataRequired('请输入维保开始日期！')])
    expire_date = StringField('维保到期日期', validators=[DataRequired('请输入维保到期日期！')])
    # 属性信息(均为非必填项)
    cpu = StringField('CPU', [validators.optional()])
    memory = StringField('内存', [validators.optional()])
    disk = StringField('硬盘', [validators.optional()])
    screen_ratio = StringField('显示器分辨率', [validators.optional()])
    screen_size = StringField('显示器尺寸', [validators.optional()])
    inf = StringField('接口', [validators.optional()])
    system_os = StringField('操作系统', [validators.optional()])
    serial_no = StringField('序列号', [validators.optional()])
    mac = StringField('MAC地址', [validators.optional()])
    battery = StringField('电池', [validators.optional()])
    power = StringField('功率', [validators.optional()])
    remark = TextAreaField('备注', [validators.optional()])

    def validate_class2(self, field):
        if field.data == '0':
            raise ValidationError('请选择资产分类！')
    def validate_class3_id(self, field):
        if not field.data:
            raise ValidationError('资产名称为空！')
    def validate_buy_no(self, field):
        if not BizAssetBuy.query.filter_by(buy_no=field.data.upper()).first():
            raise ValidationError('购买单号错误！')
    def validate_brands(self, field):
        if field.data == '0':
            raise ValidationError('请选择品牌！')
    def validate_model_id(self, field):
        if not field.data:
            raise ValidationError('型号为空！')
    def validate_vendors(self, field):
        if field.data == '0':
            raise ValidationError('请选择供应商！')
    def validate_reg_amount(self, field):
        if self.class1.data == 0 and not field.data:
            raise ValidationError('请填写登记数量！')
    def validate_buy_fee(self, field):
        try:
            float(field.data)
        except:
            raise ValidationError('购买费用必须是数字!')
class AssetSignForm(FlaskForm):
    id = HiddenField()