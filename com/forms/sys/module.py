from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, IntegerField
from wtforms.validators import DataRequired
from wtforms import ValidationError, validators
from com.models import SysModule
class ModuleSearchForm(FlaskForm):
    name = StringField('模块名称', [validators.optional()])
class ModuleForm(FlaskForm):
    id = HiddenField()
    code = StringField('模块代码', validators=[DataRequired('请输入模块代码！')])
    name = StringField('模块名称', validators=[DataRequired('请输入模块名称！')])
    order_by = IntegerField('排序号(整数)', validators=[DataRequired('模块序号必须是整数！')])

    def validate_code(self, field):
        if self.id.data is None or self.id.data == '':
            if SysModule.query.filter_by(code=field.data.lower()).first():
                raise ValidationError('模块代码已存在!')
        else:
            old_code = SysModule.query.get(self.id.data).code
            codes = []
            for module in SysModule.query.all():
                codes.append(module.code)
            # 剔除未更新前的模块代码
            codes.remove(old_code)
            # Check新的模块代码是否已经存在
            if field.data in codes:
                raise ValidationError('模块代码已存在!')

    def validate_name(self, field):
        if self.id.data is None or self.id.data == '':
            if SysModule.query.filter_by(name=field.data).first():
                raise ValidationError('模块名称已存在!')
        else:
            old_name = SysModule.query.get(self.id.data).name
            names = []
            for module in SysModule.query.all():
                names.append(module.name)
            # 剔除未更新前的模块名称
            names.remove(old_name)
            # Check新的模块名称是否已经存在
            if field.data in names:
                raise ValidationError('模块名称已存在!')