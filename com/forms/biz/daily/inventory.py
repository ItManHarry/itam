from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField
from wtforms.validators import DataRequired
from wtforms import validators, ValidationError
from com.models import BizAssetMaster, BizAssetCheck

class CheckSearchForm(FlaskForm):
    check_no = StringField('盘点单号', [validators.optional()])
    check_year = StringField('盘点年份', [validators.optional()])

class CheckForm(FlaskForm):
    id = HiddenField()
    check_no = StringField('盘点单号', [validators.optional()])
    check_year = StringField('盘点年份', validators=[DataRequired('请选择盘点年份！')])
    check_batch = StringField('盘点批次', validators=[DataRequired('请输入盘点批次！')])
    plan_start_date = StringField('计划开始日期', validators=[DataRequired('请选择计划开始日期！')])
    plan_finish_date = StringField('计划完成日期', validators=[DataRequired('请选择计划完成日期！')])
    checker_id = HiddenField()                                                        # 盘点担当ID
    checker = StringField('盘点担当', validators=[DataRequired('请选择盘点担当！')])
    check_asset_ids = HiddenField(validators=[DataRequired('请添加要盘点的资产！')])      # 选择的判断资产ID集合

    def validate_check_asset_ids(self, field):
        if field.data:
            ids = field.data.split(',')
            selected_assets = BizAssetMaster.query.filter(BizAssetMaster.id.in_(ids)).all()
            if self.id.data is None or self.id.data == '':
                checks = BizAssetCheck.query.filter(BizAssetCheck.check_year == self.check_year.data, BizAssetCheck.check_batch == self.check_batch.data).all()
            else:
                checks = BizAssetCheck.query.filter(BizAssetCheck.check_year == self.check_year.data, BizAssetCheck.check_batch == self.check_batch.data, BizAssetCheck.id != self.id.data).all()
            if checks:
                check_list = []
                for check in checks:
                    check_list += [asset.id for asset in check.assets]
            else:
                check_list = []
            error_msg = []
            for asset in selected_assets:
                # 盘点同年度同批次盘点单中是否已存在该资产
                if check_list:
                    if asset.id in check_list:
                        error_msg.append('{}({})在{}年度{}批次其他盘点单中已存在,请剔除！!'.format(asset.class3.name, asset.code, self.check_year.data, self.check_batch.data))
                        continue
                # 资产状态为'待报废'/'已报废'的资产不进行盘点
                if asset.status.item in ['8', '9']:
                    error_msg.append('{}({})资产状态为待报废/已报废,请剔除！!'.format(asset.class3.name, asset.code))
            if error_msg:
                print(';'.join(error_msg))
                raise ValidationError(';'.join(error_msg))
class SelfCheckForm(FlaskForm):
    id = HiddenField()
    check_asset_ids = HiddenField()     # 自盘点ID
    check_asset_rls = HiddenField()     # 自盘点结果