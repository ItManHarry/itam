from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, ValidationError, SelectField,validators
from wtforms.validators import DataRequired
from com.models import BizAssetApply

class ApplySearchForm(FlaskForm):
    apply_no = StringField('资产申请号代码', [validators.optional()])
    draft_no = StringField('资产草案号代码', [validators.optional()])
    company_id = StringField('法人代码', [validators.optional()])
    department_id = StringField('部门代码', [validators.optional()])
class ApplyForm(FlaskForm):
    apply_no = HiddenField()
    draft_no = StringField('资产草案号', validators=[DataRequired('请输入资产草案号！')])
    receive_date = StringField('接收日期', validators=[DataRequired('请输入接收日期！')])
    company_id = StringField('申请法人ID', validators=[DataRequired('请输入申请法人ID！')])
    company = StringField('申请法人', validators=[DataRequired('请输入申请法人！')])
    department_id = StringField('申请部门ID', validators=[DataRequired('请输入申请部门ID！')])
    department = StringField('申请部门', validators=[DataRequired('请输入申请部门！')])
    applicant_id = StringField('申请人ID', validators=[DataRequired('请输入申请人ID！')])
    applicant = StringField('申请人', validators=[DataRequired('请输入申请人！')])
    summary = StringField('申请概要', validators=[DataRequired('请输入申请概要！')])
    amount = StringField('申请数量', validators=[DataRequired('请输入申请数量！')])
    bg_id = StringField('单据所属法人ID', validators=[DataRequired('请输入单据所属法人ID！')])
    bg = StringField('单据所属法人', validators=[DataRequired('请输入单据所属法人！')])
    buy_bill = StringField('购买订单', validators=[DataRequired('请输入购买订单！')])

    def validate_code(self, field):
        if self.id.data is None or self.id.data == '':
            if BizAssetApply.query.filter_by(draft_no=field.data.upper()).first():
                raise ValidationError('草案号已存在!')
        else:
            old_code = BizAssetApply.query.get(self.id.data).code
            codes = (asset_apply.draft_no for asset_apply in BizAssetApply.query.filter(BizAssetApply.draft_no != old_code).all())
            if field.data.upper() in codes:
                raise ValidationError('草案号已存在!')
