from flask_wtf import FlaskForm
from wtforms import StringField,   validators

class ScrapSearchForm(FlaskForm):
    asset_no = StringField('资产编号', [validators.optional()])
    scrap_no = StringField('报废单号', [validators.optional()])