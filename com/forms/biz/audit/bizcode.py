from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, ValidationError, SelectField
from wtforms.validators import DataRequired
from com.models import AuditBizCode
class BizcodeForm(FlaskForm):
    id = HiddenField()
    code = StringField('业务代码', validators=[DataRequired('请输入业务代码！')])
    name = StringField('业务名称', validators=[DataRequired('请输入业务名称！')])


    def validate_code(self,field):
        if self.id.data is None or self.id.data == '':
            if AuditBizCode.query.filter_by(code=field.data.upper()).first():
                raise ValidationError('业务代码已存在!')
        else:
            old_code = AuditBizCode.query.get(self.id.data).code
            codes = (store.code for store in AuditBizCode.query.filter(AuditBizCode.code != old_code).all())
            if field.data.upper() in codes:
                raise ValidationError('业务代码已存在!')