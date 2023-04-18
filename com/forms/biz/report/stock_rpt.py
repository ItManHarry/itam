from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, validators
class Stock_rptSearchForm(FlaskForm):
    class1 = SelectField('一级分类', [validators.optional()], choices=[])
    class2 = SelectField('二级分类', [validators.optional()], choices=[])
    class3 = SelectField('三级级分类', [validators.optional()], choices=[])
    brands = SelectField('品牌', [validators.optional()], choices=[])
    models = SelectField('型号', [validators.optional()], choices=[])