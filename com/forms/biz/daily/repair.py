from flask_wtf import FlaskForm
from wtforms import StringField,   validators, HiddenField

class RepairSearchForm(FlaskForm):
    asset_no = StringField('资产编号', [validators.optional()])
    repair_no = StringField('维修单号', [validators.optional()])
    request_by = StringField('维修申请人', [validators.optional()])
    request_by_id = HiddenField()