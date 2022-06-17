'''
    系统工具函数
'''
from flask import request, redirect, url_for
from urllib.parse import urlparse, urljoin
from com.plugins import db
from com.models import SysUser, SysModule, SysMenu
import time, datetime, os, uuid
def utc_to_locale(utc_date):
    '''
    utc时间转本地
    :param utc_date:
    :return:
    '''
    now_stamp = time.time()
    locale_time = datetime.datetime.fromtimestamp(now_stamp)
    utc_time = datetime.datetime.utcfromtimestamp(now_stamp)
    offset = locale_time - utc_time
    locale_date = utc_date + offset
    return locale_date
def get_time():
    '''
    获取当前时间
    :return:
    '''
    return 'Now is : %s' %time.strftime('%Y年%m月%d日')
def get_date():
    '''
    获取日期
    :return:
    '''
    return time.strftime('%Y%m%d')
def format_time(timestamp):
    '''
    格式化日期
    :param timestamp:
    :return:
    '''
    return utc_to_locale(timestamp).strftime('%Y-%m-%d %H:%M:%S')
def is_safe_url(target):
    '''
    判断地址是否安全
    :param target:
    :return:
    '''
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http','https') and ref_url.netloc == test_url.netloc
def redirect_back(default='main.index', **kwargs):
    '''
    通用返回方法(默认返回博客首页)
    :param default:
    :param kwargs:
    :return:
    '''
    target = request.args.get('next')
    if target and is_safe_url(target):
        return redirect(target)
    return redirect(url_for(default, **kwargs))
def random_filename(filename):
    '''
    重命名文件
    :param filename:
    :return:
    '''
    ext = os.path.splitext(filename)[1]
    new_file_name = uuid.uuid4().hex + ext
    return new_file_name
def get_options(code):
    '''
    根据字典代码获取枚举下拉值
    :param code:
    :return:
    '''
    from com.models import SysDict
    dictionary = SysDict.query.filter_by(code=code).first()
    enums = dictionary.enums
    options = []
    for enum in enums:
        options.append((enum.id, enum.display))
    return options
def get_current_user(id):
    '''
    获取当前用户
    :param id:
    :return:
    '''
    return SysUser.query.get(id)
def get_current_module(id):
    '''
    获取当前模块
    :param id:
    :return:
    '''
    return SysModule.query.get(id)
def get_current_menu(id):
    '''
    获取当前菜单
    :param id:
    :return:
    '''
    return SysMenu.query.get(id)
def change_entity_order(new_order, action, entity):
    '''
    自动调整排序
    注：实体表的排序字段名必须为order_by,且为整型
    :param new_order:新的排序号
    :param action:执行操作：0:新增 1:更新
    :param entity:要编辑的表实例
    :return:
    '''
    if action == 0:
        '''
        如果是新增，则将大于等于当前排序号的加一保存
        '''
        if isinstance(entity, SysModule):
            entities = SysModule.query.filter(SysModule.order_by >= new_order).all()
        if isinstance(entity, SysMenu):
            # entities = SysMenu.query.with_parent(entity.module).filter(SysMenu.order_by >= new_order).all()
            entities = None
        if entities:
            for item in entities:
                item.order_by = item.order_by + 1
                db.session.commit()
    if action == 1:
        '''
            如果是更新，首先判断是由小变大还是由大变小
            由小变大：将大于当前要修改的module排序号同时小于等于新排序号的模块排序号减一保存
            由大变小：将小于当前要修改的module排序号同时大于等于新排序号的模块排序号加一保存
        '''
        if entity.order_by < new_order:
            if isinstance(entity, SysModule):
                entities = SysModule.query.filter(SysModule.order_by > entity.order_by, SysModule.order_by <= new_order).all()
            if isinstance(entity, SysMenu):
                entities = SysMenu.query.with_parent(entity.module).filter(SysMenu.order_by > entity.order_by, SysMenu.order_by <= new_order).all()
            if entities:
                for item in entities:
                    item.order_by = item.order_by - 1
                    db.session.commit()
        else:
            if isinstance(entity, SysModule):
                entities = SysModule.query.filter(SysModule.order_by < entity.order_by, SysModule.order_by >= new_order).all()
            if isinstance(entity, SysMenu):
                entities = SysMenu.query.with_parent(entity.module).filter(SysMenu.order_by < entity.order_by, SysMenu.order_by >= new_order).all()
            if entities:
                for item in entities:
                    item.order_by = item.order_by + 1
                    db.session.commit()
def gen_barcode(path, code):
    '''
    生成条形码
    :param path:
    :param code:
    :return:
    '''
    import barcode
    from barcode.writer import ImageWriter
    print('Provided codes : ', barcode.PROVIDED_BARCODES)
    BARCODE_EAN = barcode.get_barcode_class('code39')
    ean = BARCODE_EAN(code, writer=ImageWriter())
    full_name = ean.save(path + '\\' + code, options=dict(font_size=14, text_distance=2))
    return full_name
def gen_qrcode(file, data):
    '''
    生成二维码
    :param file:
    :param data:
    :return:
    '''
    import qrcode
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(file)