from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, ValidationError, SelectField
from wtforms.validators import DataRequired
from com.models import BizCompany, BizEnterprise
class CompanySearchForm(FlaskForm):
    enterprise = SelectField('所属事业处', validators=[DataRequired('请选择所属事业处！')], choices=[])
class CompanyForm(CompanySearchForm):
    id = HiddenField()
    code = StringField('法人代码', validators=[DataRequired('请输入法人代码!')])
    name = StringField('法人名称', validators=[DataRequired('请输入法人名称!')])

    def validate_code(self, field):
        selected_enterprise = BizEnterprise.query.get(self.enterprise.data)
        if self.id.data is None or self.id.data == '':
            if BizCompany.query.with_parent(selected_enterprise).filter_by(code=field.data.upper()).first():
                raise ValidationError('法人代码已存在!')
        else:
            current_company = BizCompany.query.get(self.id.data)
            old_code = current_company.code
            codes = []
            for enterprise in BizCompany.query.with_parent(selected_enterprise).all():
                codes.append(enterprise.code)
            # 剔除未更新前的法人代码(法人未变更的情况下做移除)
            if current_company.enterprise_id == self.enterprise.data:
                codes.remove(old_code)
            # Check新的法人处代码是否已经存在
            if field.data.upper() in codes:
                raise ValidationError('法人代码已存在!')