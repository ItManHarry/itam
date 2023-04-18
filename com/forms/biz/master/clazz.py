from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, ValidationError, BooleanField, SelectField, validators
from wtforms.validators import DataRequired
from com.models import BizAssetClass
class ClazzSearchForm(FlaskForm):
    code = StringField('类别代码', [validators.optional()])
    name = StringField('类别名称', [validators.optional()])
class ClazzForm(FlaskForm):
    id = HiddenField()
    code = StringField('类别代码', [validators.optional()])
    name = StringField('类别名称', validators=[DataRequired('请输入资产大类名称！')])
    unit = StringField('计量单位(个/米/箱...)')
    parent = SelectField('上级类别', [validators.optional()], choices=[])
    has_parent = BooleanField('上级类别')  # 默认为True

    def validate_name(self, field):
        if self.id.data is None or self.id.data == '':
            if BizAssetClass.query.filter_by(name=field.data).first():
                raise ValidationError('类别名称已存在!')
        else:
            old_name = BizAssetClass.query.get(self.id.data).name
            names = (clazz.code for clazz in BizAssetClass.query.filter(BizAssetClass.name != old_name).all())
            if field.data in names:
                raise ValidationError('类别名称已存在!')

    def validate_unit(self, field):
        if self.has_parent.data and self.parent.data:
            parent_class = BizAssetClass.query.get(self.parent.data)
            if parent_class.grade == 2 and (field.data is None or field.data.strip() == ''):
                raise ValidationError('请填写资产类别计量单位!')