from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, validators
class SearchForm(FlaskForm):
    companies = SelectField('法人', [validators.optional()], choices=[])
    departments = SelectField('部门', [validators.optional()], choices=[])
    employees = SelectField('使用人', [validators.optional()], choices=[])
    sap_code = StringField('SAP资产编号', [validators.optional()])