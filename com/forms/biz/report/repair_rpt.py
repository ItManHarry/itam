from flask_wtf import FlaskForm
from wtforms import StringField,   validators

class Repair_rptSearchForm(FlaskForm):
    asset_no = StringField('资产编号', [validators.optional()])
    repair_no = StringField('维修单号', [validators.optional()])
    check_year = StringField('盘点年份', [validators.optional()])