from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, SelectField, TextAreaField
from wtforms.validators import DataRequired
from wtforms import ValidationError, validators
from com.models import SysEnum, BizAssetMaster, BizStockHistory
from com.views.biz.asset.master import get_stock_amount

class StockoutSearchForm(FlaskForm):
    out_type = SelectField('出库类型', [validators.optional()], choices=[])
    out_no = StringField('出库单号', [validators.optional()])
class StockoutForm(FlaskForm):
    id = HiddenField()
    sign = HiddenField()            # action标识:0->仅保存 1->保存并提交
    take_by_id = HiddenField()      # 领用人ID
    audit_line = HiddenField()      # 审批模板
    out_assets_ids = HiddenField(validators=[DataRequired('请添加要出库的资产！')])  # 出库资产ID集合
    out_assets_amount = HiddenField()  # 出库资产数量
    take_by = StringField('领用人', validators=[DataRequired('请选择领用人！')]) # 领用人姓名
    audit_line_id = SelectField('审批模板', validators=[DataRequired('请选择审批模板！')], choices=[])         # 审批线
    out_no = StringField('出库单号', [validators.optional()])
    out_date = StringField('出库日期', validators=[DataRequired('请输入出库日期！')])
    back_date = StringField('归还日期')
    out_type_id = SelectField('出库类型', validators=[DataRequired('请选择出库类型！')], choices=[])
    summary = TextAreaField('出库概要', [validators.optional()])

    def validate_back_date(self, field):
        type_code = SysEnum.query.get(self.out_type_id.data).item
        # 借用发放时判断归还日期是否为空
        if type_code == 'T002' and not field.data:
            raise ValidationError('请选择归还日期！')

    def validate_out_assets_ids(self, field):
        stock_type = SysEnum.query.get(self.out_type_id.data)
        asset_ids = []  # 用以判断是否校验资产出库状态(只在编辑时可用)
        if self.out_no.data is not None and self.out_no.data != '':
            items = BizStockHistory.query.filter_by(bill_no=self.out_no.data).all()
            for item in items:
                asset_ids.append(item.asset_id)
        if field.data:
            ids = field.data.split(',')
            amounts = self.out_assets_amount.data.split(',')
            amount_dict = dict(zip(ids, amounts))
            selected_assets = BizAssetMaster.query.filter(BizAssetMaster.id.in_(ids)).all()
            error_msg = []
            for asset in selected_assets:
                try:
                    amount = int(amount_dict[asset.id])
                except:
                    error_msg.append('{}({})出库数量不是数字(整数)!'.format(asset.class3.name, asset.code))
                    continue
                if asset.is_asset:
                    '''
                        如果是资产,新增的情况下判断是否已出库，否则只出库数量是否为1
                    '''
                    if asset.is_out and asset.id not in asset_ids:
                        error_msg.append('{}({})已出库!'.format(asset.class3.name, asset.code))
                    elif amount != 1:
                        error_msg.append('{}({})出库数量只能是1!'.format(asset.class3.name, asset.code))
                    if stock_type.item == '1' and not asset.user:
                        error_msg.append('请维护{}({})使用者信息!'.format(asset.class3.name, asset.code))
                else:
                    '''
                        耗材只判断库存即可
                    '''
                    stock_amount = get_stock_amount(asset)
                    if stock_amount and stock_amount.amount:
                        if amount > stock_amount.amount:
                            error_msg.append('{}({})库存不足(当前库存{})!'.format(asset.class3.name, asset.code, stock_amount.amount))
                    else:
                        error_msg.append(
                            '{}({})库存余额异常,请联系管理员!'.format(asset.class3.name, asset.code))
            if error_msg:
                print(';'.join(error_msg))
                raise ValidationError(';'.join(error_msg))