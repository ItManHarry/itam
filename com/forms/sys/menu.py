from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired
from wtforms import ValidationError, validators
from com.models import SysMenu
class MenuSearchForm(FlaskForm):
    name = StringField('菜单名称', [validators.optional()])
class MenuForm(FlaskForm):
    id = HiddenField()
    code = StringField('菜单代码', validators=[DataRequired('请输入菜单代码！')])
    name = StringField('菜单名称', validators=[DataRequired('请输入菜单名称！')])
    url = StringField('菜单URL', validators=[DataRequired('请输入菜单URL地址！')])
    remark = TextAreaField('菜单说明', validators=[DataRequired('请输入菜单说明！')])
    module = SelectField('所属模块', validators=[DataRequired('请选择所属模块！')], choices=[])
    icon = StringField('菜单图标', [validators.optional()])
    order_by = IntegerField('排序号(整数)', validators=[DataRequired('菜单序号必须是整数！')])

    def validate_name(self, field):
        if self.id.data is None or self.id.data == '':
            if SysMenu.query.filter_by(name=field.data).first():
                raise ValidationError('菜单名称已存在!')
        else:
            old_name = SysMenu.query.get(self.id.data).name
            names = []
            for menu in SysMenu.query.all():
                names.append(menu.name)
            # 剔除未更新前的菜单名称
            names.remove(old_name)
            # Check新的菜单名称是否已经存在
            if field.data in names:
                raise ValidationError('菜单名称已存在!')