from flask_wtf import FlaskForm
from wtforms import StringField,   validators

class Scrap_rptSearchForm(FlaskForm):
    asset_no = StringField('资产编号', [validators.optional()])
    scrap_no = StringField('报废单号', [validators.optional()])
    check_year = StringField('盘点年份', [validators.optional()])