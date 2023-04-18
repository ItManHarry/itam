from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, ValidationError, SelectField, validators, TextAreaField
from wtforms.validators import DataRequired
from com.models import BizStockIn


class AuditSearchForm(FlaskForm):
    in_no = StringField('审批单号', [validators.optional()])


class AuditForm(FlaskForm):
    id = HiddenField()
    in_no = StringField('审批单号', [validators.optional()])
    in_date = StringField('入库日期', validators=[DataRequired('请输入入库日期！')])
    charger_id = StringField('入库人员', validators=[DataRequired('请输入入库人员！')])
    state_id = StringField('审批状态', validators=[DataRequired('请输入入库人员！')])

    def validate_code(self, field):
        if self.id.data is None or self.id.data == '':
            if BizStockIn.query.filter_by(in_no=field.data.upper()).first():
                raise ValidationError('审批单号已存在!')
        else:
            old_code = BizStockIn.query.get(self.id.data).in_no
            codes = (audit.in_no for audit in
                     BizStockIn.query.filter(BizStockIn.code != old_code).all())
            if field.data.upper() in codes:
                raise ValidationError('审批单号已存在!')
