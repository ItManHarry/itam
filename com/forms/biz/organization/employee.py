from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, HiddenField, ValidationError, validators
from wtforms.validators import DataRequired, Length, Email
from com.models import BizEmployee, BizCompany
class EmployeeSearchForm(FlaskForm):
    code = StringField('职号', [validators.optional()])
    name = StringField('姓名', [validators.optional()])
class EmployeeForm(FlaskForm):
    id = HiddenField()
    code = StringField('职号', validators=[DataRequired('请输入职号!')])
    name = StringField('姓名', validators=[DataRequired('请输入姓名!')])
    email = StringField('邮箱', validators=[DataRequired('请输入邮箱!!!'), Length(1, 64, '长度要介于1~64!!!'), Email('邮箱格式不正确!!!')])
    phone = StringField('电话', [validators.optional()])
    company = HiddenField()
    department = SelectField('部门', validators=[DataRequired('请选择部门！')], choices=[])
    
    def validate_code(self, field):
        company = BizCompany.query.get(self.company.data)
        if self.id.data is None or self.id.data == '':
            if BizEmployee.query.with_parent(company).filter_by(code=field.data.lower()).first():
                raise ValidationError('职号已存在!')
        else:
            old_code = BizEmployee.query.get(self.id.data).code
            codes = []
            all_departments = BizEmployee.query.with_parent(company).all()
            for department in all_departments:
                codes.append(department.code)
            # 剔除未更新前的职号
            codes.remove(old_code)
            # Check新的职号是否已经存在
            if field.data.lower() in codes:
                raise ValidationError('职号已存在!')