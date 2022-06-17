from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, HiddenField, BooleanField
from wtforms.validators import DataRequired
from wtforms import ValidationError, validators
from com.models import BizDepartment, BizCompany
class DepartmentSearchForm(FlaskForm):
    code = StringField('部门代码', [validators.optional()])
    name = StringField('部门名称', [validators.optional()])
class DepartmentForm(FlaskForm):
    '''
    以下使用会报错：
    RuntimeError: No application found. Either work inside a view function or push an application context. See http://flask-sqlalchemy.pocoo.org/contexts/.
    原因：当前未装入Flask应用上下文，故数据库操作不可用
    '''
    '''
    departments = BizDepartment.query.order_by(BizDepartment.code.desc()).all()
    for department in departments:
        department_list.append((department.id, department.name))
    print('Dept list is >>>>>>>>>> ', department_list)
    '''
    id = HiddenField()
    code = StringField('部门代码', validators=[DataRequired('请输入部门代码!')])
    name = StringField('部门名称', validators=[DataRequired('请输入部门名称!')])
    enterprise = SelectField('事业处', [validators.optional()], choices=[])
    company = StringField('法人')
    company_id = HiddenField()
    parent = StringField('上级部门')
    parent_id = HiddenField()
    has_parent = BooleanField('上级部门')
    def validate_company(self, field):
        if field.data is None or field.data.strip() == '':
            raise ValidationError('请选择法人所属!')
    def validate_parent(self, field):
        if self.has_parent.data and field.data.strip() == '':
            raise ValidationError('请选择上级部门!')
    def validate_code(self, field):
        company = BizCompany.query.get(self.company_id.data)
        if company:
            if self.id.data is None or self.id.data == '':
                if BizDepartment.query.with_parent(company).filter_by(code=field.data.lower()).first():
                    raise ValidationError('部门代码已存在!')
            else:
                old_code = BizDepartment.query.get(self.id.data).code
                codes = [department.code.lower() for department in BizDepartment.query.with_parent(company).all() if department.code != old_code]
                # Check新的部门代码是否已经存在
                if field.data.lower() in codes:
                    raise ValidationError('部门代码已存在!')

    def validate_name(self, field):
        company = BizCompany.query.get(self.company_id.data)
        if company:
            if self.id.data is None or self.id.data == '':
                if BizDepartment.query.with_parent(company).filter_by(name=field.data).first():
                    raise ValidationError('部门名称已存在!')
            else:
                old_name = BizDepartment.query.get(self.id.data).name
                names = [department.name for department in BizDepartment.query.with_parent(company).all() if department.name != old_name]
                # Check新的部门名称是否已经存在
                if field.data in names:
                    raise ValidationError('部门名称已存在!')