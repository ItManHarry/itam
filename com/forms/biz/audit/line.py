from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, ValidationError, TextAreaField, SelectField, validators
from wtforms.validators import DataRequired
from com.models import AuditLine
class LineSearchForm(FlaskForm):
    code = StringField('模板代码', [validators.optional()])
    name = StringField('模板名称', [validators.optional()])
class LineForm(FlaskForm):
    id = HiddenField()
    code = StringField('模板代码', validators=[DataRequired('请输入模板代码！')])
    name = StringField('模板名称', validators=[DataRequired('请输入模板名称！')])
    biz_code = SelectField('审批业务', validators=[DataRequired('请选择审批业务！')], choices=[])
    remark = TextAreaField('模板说明', [validators.optional()])

    def validate_code(self, field):
        if self.id.data is None or self.id.data == '':
            if AuditLine.query.filter_by(code=field.data.upper()).first():
                raise ValidationError('模板代码已存在!')
        else:
            old_code = AuditLine.query.get(self.id.data).code
            codes = []
            all_roles = AuditLine.query.all()
            for role in all_roles:
                codes.append(role.code)
            # 剔除未更新前的角色代码
            codes.remove(old_code)
            # Check新的角色代码是否已经存在
            if field.data.upper() in codes:
                raise ValidationError('模板代码已存在!')

    def validate_name(self, field):
        if self.id.data is None or self.id.data == '':
            if AuditLine.query.filter_by(name=field.data).first():
                raise ValidationError('模板名称已存在!')
        else:
            old_name = AuditLine.query.get(self.id.data).name
            names = []
            for role in AuditLine.query.all():
                names.append(role.name)
            # 剔除未更新前的模板名称
            names.remove(old_name)
            # Check新的模板名称是否已经存在
            if field.data in names:
                raise ValidationError('模板名称已存在!')