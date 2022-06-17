from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, SelectField
from wtforms.validators import DataRequired
from wtforms import ValidationError, validators
from com.models import SysRole
class RoleSearchForm(FlaskForm):
    name = StringField('角色名称', [validators.optional()])
class RoleForm(FlaskForm):
    id = HiddenField()
    name = StringField('角色名称', validators=[DataRequired('请输入角色名称！')])
    company = SelectField('法人', [validators.optional()], choices=[])

    def validate_name(self, field):
        if self.id.data is None or self.id.data == '':
            if SysRole.query.filter_by(name=field.data).first():
                raise ValidationError('角色名称已存在!')
        else:
            old_name = SysRole.query.get(self.id.data).name
            names = []
            for role in SysRole.query.all():
                names.append(role.name)
            # 剔除未更新前的角色名称
            names.remove(old_name)
            # Check新的角色名称是否已经存在
            if field.data in names:
                raise ValidationError('角色名称已存在!')