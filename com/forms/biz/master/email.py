from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, ValidationError, SelectField
from wtforms.validators import DataRequired
from com.models import BizEmailConfig
class EmailForm(FlaskForm):
    id = HiddenField()
    code = StringField('邮件通知代码', validators=[DataRequired('请输入邮件通知代码！')])
    name = StringField('邮件通知名称', validators=[DataRequired('请输入邮件通知名称！')])
    email_to = StringField('邮件收件人(以英文逗号隔开)', validators=[DataRequired('请输入邮件收件人！')])
    email_cc = StringField('邮件参照人(以英文逗号隔开)', validators=[DataRequired('请输入邮件参照人！')])

    def validate_code(self,field):
        if self.id.data is None or self.id.data == '':
            if BizEmailConfig.query.filter_by(code=field.data.upper()).first():
                raise ValidationError('邮件通知代码已存在!')
        else:
            old_code = BizEmailConfig.query.get(self.id.data).code
            codes = (email.code for email in BizEmailConfig.query.filter(BizEmailConfig.code != old_code).all())
            if field.data.upper() in codes:
                raise ValidationError('邮件通知代码已存在!')