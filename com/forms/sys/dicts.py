from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField
from wtforms.validators import DataRequired
from wtforms import ValidationError, validators
from com.models import SysDict
class DictSearchForm(FlaskForm):
    code = StringField('字典代码', [validators.optional()])
    name = StringField('字典名称', [validators.optional()])
class DictForm(FlaskForm):
    id = HiddenField()
    code = StringField('字典代码', validators=[DataRequired('请输入字典代码！')])
    name = StringField('字典名称', validators=[DataRequired('请输入字典名称！')])

    def validate_code(self, field):
        if self.id.data is None or self.id.data == '':
            if SysDict.query.filter_by(code=field.data.upper()).first():
                raise ValidationError('字典代码已存在!')
        else:
            old_code = SysDict.query.get(self.id.data).code
            codes = []
            all_dicts = SysDict.query.all()
            for dictionary in all_dicts:
                codes.append(dictionary.code)
            # 剔除未更新前的字典代码
            codes.remove(old_code)
            # Check新的字典代码是否已经存在
            if field.data.upper() in codes:
                raise ValidationError('字典代码已存在!')
    def validate_name(self, field):
        if self.id.data is None or self.id.data == '':
            if SysDict.query.filter_by(name=field.data).first():
                raise ValidationError('字典名称已存在!')
        else:
            old_name = SysDict.query.get(self.id.data).name
            names = []
            for dictionary in SysDict.query.all():
                names.append(dictionary.name)
            # 剔除未更新前的字典名称
            names.remove(old_name)
            # Check新的字典名称是否已经存在
            if field.data in names:
                raise ValidationError('字典名称已存在!')