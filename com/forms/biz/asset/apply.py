from flask_wtf import FlaskForm
from wtforms import FileField, StringField, HiddenField, ValidationError, SelectField, validators, TextAreaField
from wtforms.validators import DataRequired
from com.models import BizAssetItem

class ApplySearchForm(FlaskForm):
    apply_no = StringField('资产申请号', [validators.optional()])
    draft_no = StringField('申请起案号', [validators.optional()])
    company = SelectField('法人', [validators.optional()], choices=[])
    department = SelectField('部门', [validators.optional()], choices=[])
class ApplyForm(FlaskForm):
    id = HiddenField()
    items_tmp_id = HiddenField()
    apply_no = StringField('申请号', [validators.optional()])
    draft_no = StringField('申请起案号', validators=[DataRequired('请输入申请起案号！')])
    receive_date = StringField('接收日期', validators=[DataRequired('请输入接收日期！')])
    summary = TextAreaField('申请概要', validators=[DataRequired('请输入申请概要！')])
    amount = StringField('申请数量', [validators.optional()])
    company = SelectField('申请法人', [validators.optional()], choices=[])
    department_slt = SelectField('申请部门', [validators.optional()], choices=[])
    applicant_slt = SelectField('申请人', [validators.optional()], choices=[])
    applicant_pos = StringField('职位', [validators.optional()])
    class2_slt = SelectField('资产分类', [validators.optional()], choices=[])
    brand_slt = SelectField('品牌', [validators.optional()], choices=[])
    file = FileField('附件', [validators.optional()])
    class2_id = HiddenField()
    class3_id = HiddenField()
    brand_id = HiddenField()
    model_id = HiddenField()
    department = HiddenField()
    applicant = HiddenField()
    company_id = HiddenField()

    def validate_applicant(self, field):
        if not field.data or field.data == '00000000':
            raise ValidationError('请选择申请人!')
    def validate_items_tmp_id(self, field):
        items = BizAssetItem.query.filter_by(tmp_id=field.data).all()
        print('Items length is : ', len(items))
        if not items:
            raise ValidationError('请添加申请明细！')