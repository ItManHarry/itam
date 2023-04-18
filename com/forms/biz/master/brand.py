from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField
from wtforms.validators import DataRequired
from wtforms import ValidationError, validators
from com.models import BizBrandMaster
class BrandSearchForm(FlaskForm):
    code = StringField('品牌代码', [validators.optional()])
    name = StringField('品牌名称', [validators.optional()])
class BrandForm(FlaskForm):
    id = HiddenField()
    code = StringField('品牌代码', validators=[DataRequired('请输入品牌代码！')])
    name = StringField('品牌名称', validators=[DataRequired('请输入品牌名称！')])

    def validate_code(self, field):
        if self.id.data is None or self.id.data == '':
            if BizBrandMaster.query.filter_by(code=field.data.upper()).first():
                raise ValidationError('品牌代码已存在!')
        else:
            old_code = BizBrandMaster.query.get(self.id.data).code
            codes = []
            all_brands = BizBrandMaster.query.all()
            for brand in all_brands:
                codes.append(brand.code)
            # 剔除未更新前的品牌代码
            codes.remove(old_code)
            # Check新的品牌代码是否已经存在
            if field.data.upper() in codes:
                raise ValidationError('品牌代码已存在!')
    def validate_name(self, field):
        if self.id.data is None or self.id.data == '':
            if BizBrandMaster.query.filter_by(name=field.data).first():
                raise ValidationError('品牌名称已存在!')
        else:
            old_name = BizBrandMaster.query.get(self.id.data).name
            names = []
            for brand in BizBrandMaster.query.all():
                names.append(brand.name)
            # 剔除未更新前的品牌名称
            names.remove(old_name)
            # Check新的品牌名称是否已经存在
            if field.data in names:
                raise ValidationError('品牌名称已存在!')