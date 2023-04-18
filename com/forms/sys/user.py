from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, HiddenField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Email
from wtforms import ValidationError, validators
from com.models import SysUser
import re
class UserSearchForm(FlaskForm):
    code = StringField('用户代码', [validators.optional()])
    name = StringField('用户姓名', [validators.optional()])
class UserForm(FlaskForm):
    id = HiddenField()
    is_ad = BooleanField('AD用户')
    code = StringField('用户代码', validators=[DataRequired('请输入用户代码！')])
    name = StringField('用户姓名', validators=[DataRequired('请输入用户姓名！')])
    password = PasswordField('密码')
    password_confirm = PasswordField('确认密码')
    email = StringField('邮箱', validators=[DataRequired('请输入邮箱!!!'), Length(1, 64, '长度要介于1~64!!!'), Email('邮箱格式不正确!!!')])
    phone = StringField('电话', [validators.optional()])
    role = SelectField('角色', validators=[DataRequired('请选择角色！')], choices=[])
    company = SelectField('法人', validators=[DataRequired('请选择法人！')], choices=[])
    def validate_code(self, field):
        if self.id.data == '' or self.id.data is None:
            if SysUser.query.filter_by(user_id=field.data.lower()).first():
                raise ValidationError('用户代码已存在!')
        else:
            old_code = SysUser.query.get(self.id.data).user_id
            codes = [user.user_id for user in SysUser.query.filter(SysUser.user_id != old_code).all()]
            if field.data.lower() in codes:
                raise ValidationError('人员代码已存在!')
    def validate_email(self, field):
        if self.id.data == '' or self.id.data is None:
            if SysUser.query.filter_by(email=field.data.lower()).first():
                raise ValidationError('邮箱地址已存在!')
        else:
            old_email = SysUser.query.get(self.id.data).email
            emails = [user.email for user in SysUser.query.filter(SysUser.email != old_email).all()]
            if field.data in emails:
                raise ValidationError('邮箱地址已存在!')
    def validate_password(self, field):
        password = field.data.strip() if field.data else ''
        regex = re.compile('^(?:(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])).*$')
        # 新增用户
        if self.id.data == '' or self.id.data is None:
            # 非ad用户的情况下才去校验密码
            if not self.is_ad.data:
                if not password:
                    raise ValidationError('请输入密码！')
                if len(password) < 8:
                    raise ValidationError('密码长度要八位以上!')
                if not regex.match(password):
                    raise ValidationError('密码必须包含大小写字母和数字!')
                if password != self.password_confirm.data:
                    raise ValidationError('两次输入的密码不一致')
        # 编辑用户
        else:
            if not self.is_ad.data:
                if password:
                    if len(password) < 8:
                        raise ValidationError('密码长度要八位以上!')
                    if not regex.match(password):
                        raise ValidationError('密码必须包含大小写字母和数字!')
                    if password != self.password_confirm.data:
                        raise ValidationError('两次输入的密码不一致')
                else:
                    old_password = SysUser.query.get(self.id.data).user_pwd_hash
                    if not old_password:
                        raise ValidationError('请输入密码！')
    def validate_password_confirm(self, field):
        confirm_password = field.data.strip() if field.data else ''
        # 新增用户
        if self.id.data == '' or self.id.data is None:
            if not self.is_ad.data:
                if not confirm_password:
                    raise ValidationError('请输入确认密码！')
        # 编辑用户
        else:
            old_password = SysUser.query.get(self.id.data).user_pwd_hash
            if not self.is_ad.data:
                if not old_password and not confirm_password:
                    raise ValidationError('请输入确认密码！')