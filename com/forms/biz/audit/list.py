from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, TextAreaField, validators
from wtforms.validators import DataRequired

class ListSearchForm(FlaskForm):
    code = StringField('模板代码', [validators.optional()])
    name = StringField('模板名称', [validators.optional()])

class ListForm(FlaskForm):
    id = HiddenField()
    class1 = HiddenField()
    bill_type = HiddenField()
    in_no = StringField('审批单号', [validators.optional()])
    in_date = StringField('入库日期', validators=[DataRequired('请输入入库日期！')])
    out_no = StringField('出库审批单号', [validators.optional()])
    out_date = StringField('出库日期', validators=[DataRequired('请输入出库日期！')])
    outcharger_id = StringField('出库人员', validators=[DataRequired('请输入出库库人员！')])
    outstate_id = StringField('出库审批状态', validators=[DataRequired('请输入出库库状态！')])
    charger_id = StringField('入库人员', validators=[DataRequired('请输入入库人员！')])
    state_id = StringField('审批状态', validators=[DataRequired('请输入入库人员！')])
    remark = TextAreaField('审批意见', validators=[DataRequired('请输入审批意见！')])
    summary = TextAreaField('出库概要', [validators.optional()])
