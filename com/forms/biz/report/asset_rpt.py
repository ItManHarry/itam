from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, validators
class SearchForm(FlaskForm):
    class1 = SelectField('资产大类', [validators.optional()], choices=[])
    class2 = SelectField('资产分类', [validators.optional()], choices=[])
    class3 = SelectField('资产名称', [validators.optional()], choices=[])
    brands = SelectField('品牌', [validators.optional()], choices=[])
    models = SelectField('型号', [validators.optional()], choices=[])
    code = StringField('资产编号', [validators.optional()])
    sap_code = StringField('SAP资产编号', [validators.optional()])
    log_s = StringField('登记日期(FROM)', [validators.optional()])
    log_e = StringField('登记日期(TO)', [validators.optional()])
    store_status = SelectField('库存状态', [validators.optional()], choices=[('0', '库存-All'), ('1', '在库'), ('2', '已出库')])
    asset_status = SelectField('资产状态', [validators.optional()], choices=[])