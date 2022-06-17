from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, ValidationError
from wtforms.validators import DataRequired
from com.models import BizEnterprise
class EnterpriseForm(FlaskForm):
    id = HiddenField()
    code = StringField('事业处代码', validators=[DataRequired('请输入事业处代码!')])
    name = StringField('事业处名称', validators=[DataRequired('请输入事业处名称!')])
    def validate_code(self, field):
        if self.id.data is None or self.id.data == '':
            if BizEnterprise.query.filter_by(code=field.data.upper()).first():
                raise ValidationError('事业处代码已存在!')
        else:
            old_code = BizEnterprise.query.get(self.id.data).code
            codes = []
            for enterprise in BizEnterprise.query.all():
                codes.append(enterprise.code)
            # 剔除未更新前的事业处代码
            codes.remove(old_code)
            # Check新的事业处代码是否已经存在
            if field.data.upper() in codes:
                raise ValidationError('事业处代码已存在!')