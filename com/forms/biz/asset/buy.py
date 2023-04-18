from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, ValidationError, TextAreaField, SelectField, validators
from wtforms.validators import DataRequired
from com.models import BizAssetBuy, BizAssetApply
class BuySearchForm(FlaskForm):
    application_no = StringField('申请单号', [validators.optional()])
    buy_no = StringField('购买号', [validators.optional()])
    draft_no = StringField('草案号', [validators.optional()])
class BuyForm(FlaskForm):
    id = HiddenField()
    buy_no = StringField('购买号', [validators.optional()])
    application_no = SelectField('申请单号', choices=[])
    bill_date = StringField('订单日期', validators=[DataRequired('请选择订单日期！')])
    draft_no = StringField('执行起案号', validators=[DataRequired('请输入执行起案号！')])
    total_price = StringField('购买总价', validators=[DataRequired('请输入购买总价！')])
    receive_due_date = StringField('预计到货日期', validators=[DataRequired('请选择预计到货日期！')])
    asset_class = StringField('资产分类', [validators.optional()])
    asset_name = StringField('资产名称', [validators.optional()])
    brand = StringField('品牌', [validators.optional()])
    model = StringField('型号', [validators.optional()])
    applicant = StringField('申请人', [validators.optional()])

    def validate_application_no(self, field):
        if field.data == '00000000':
            raise ValidationError('请选择申请单号!')