from flask_wtf import FlaskForm
from wtforms import StringField, validators, HiddenField, SelectField
class SearchForm(FlaskForm):
    inventory_year = StringField('盘点年份', [validators.optional()])
    inventory_batch = StringField('盘点批次', [validators.optional()])
    inventory_by = StringField('盘点担当', [validators.optional()])
    status = SelectField('资产状态', choices=[('0', '状态All'), ('1', '在库'), ('2', '出库')])
    inventory_by_id = HiddenField()