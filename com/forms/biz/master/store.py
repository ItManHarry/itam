from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, ValidationError, SelectField
from wtforms.validators import DataRequired
from com.models import BizStoreMaster
class StoreForm(FlaskForm):
    id = HiddenField()
    code = StringField('仓库代码', validators=[DataRequired('请输入仓库代码！')])
    name = StringField('仓库名称', validators=[DataRequired('请输入仓库名称！')])
    place = StringField('仓库地点', validators=[DataRequired('请输入仓库地点！')])

    def validate_code(self,field):
        if self.id.data is None or self.id.data == '':
            if BizStoreMaster.query.filter_by(code=field.data.upper()).first():
                raise ValidationError('仓库代码已存在!')
        else:
            old_code = BizStoreMaster.query.get(self.id.data).code
            codes = (store.code for store in BizStoreMaster.query.filter(BizStoreMaster.code != old_code).all())
            if field.data.upper() in codes:
                raise ValidationError('仓库代码已存在!')