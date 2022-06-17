from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length
class LoginForm(FlaskForm):
    user_id = StringField('账号', validators=[DataRequired('Please Input User ID!'), Length(1, 20, '长度要介于(1~20)!')])
    user_pwd = PasswordField('密码', validators=[DataRequired('Please input password!'), Length(8, 128, '长度要介于(8~128)!')])
    submit = SubmitField('登录')