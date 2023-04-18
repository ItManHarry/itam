from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, ValidationError, SelectField,validators
from wtforms.validators import DataRequired
from com.models import BizVendorMaster

class VendorSearchForm(FlaskForm):
    code = StringField('供应商代码', [validators.optional()])
    name = StringField('供应商名称', [validators.optional()])
class VendorForm(FlaskForm):
    id = HiddenField()
    code = StringField('供应商代码', validators=[DataRequired('请输入供应商代码！')])
    name = StringField('供应商名称', validators=[DataRequired('请输入供应商名称！')])
    contact_person = StringField('联系人', validators=[DataRequired('请输入供应商联系人！')])
    contact_phone = StringField('联系电话', validators=[DataRequired('请输入供应商联系电话！')])

    def validate_code(self, field):
        if self.id.data is None or self.id.data == '':
            if BizVendorMaster.query.filter_by(code=field.data.upper()).first():
                raise ValidationError('供应商代码已存在!')
        else:
            old_code = BizVendorMaster.query.get(self.id.data).code
            codes = (vendor.code for vendor in BizVendorMaster.query.filter(BizVendorMaster.code != old_code).all())
            if field.data.upper() in codes:
                raise ValidationError('供应商代码已存在!')
