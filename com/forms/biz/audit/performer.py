from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, ValidationError, validators
from wtforms.validators import DataRequired
from com.models import AuditRole
class PerformerSearchForm(FlaskForm):
    code = StringField('角色代码', [validators.optional()])
    name = StringField('角色名称', [validators.optional()])
class PerformerForm(FlaskForm):
    id = HiddenField()
    code = StringField('角色代码', validators=[DataRequired('请输入角色代码！')])
    name = StringField('角色名称', validators=[DataRequired('请输入角色名称！')])

    def validate_code(self, field):
        if self.id.data is None or self.id.data == '':
            if AuditRole.query.filter_by(code=field.data.upper()).first():
                raise ValidationError('角色代码已存在!')
        else:
            old_code = AuditRole.query.get(self.id.data).code
            codes = []
            all_roles = AuditRole.query.all()
            for role in all_roles:
                codes.append(role.code)
            # 剔除未更新前的角色代码
            codes.remove(old_code)
            # Check新的角色代码是否已经存在
            if field.data.upper() in codes:
                raise ValidationError('角色代码已存在!')

    def validate_name(self, field):
        if self.id.data is None or self.id.data == '':
            if AuditRole.query.filter_by(name=field.data).first():
                raise ValidationError('角色名称已存在!')
        else:
            old_name = AuditRole.query.get(self.id.data).name
            names = []
            for role in AuditRole.query.all():
                names.append(role.name)
            # 剔除未更新前的角色名称
            names.remove(old_name)
            # Check新的角色名称是否已经存在
            if field.data in names:
                raise ValidationError('角色名称已存在!')