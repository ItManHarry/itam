'''
    系统工具函数
'''
from flask import request, redirect, url_for, current_app
from urllib.parse import urlparse, urljoin
from com.plugins import db
from com.models import SysUser, SysModule, SysMenu
import time, datetime, os, uuid, random, PIL
from ldap3 import Server, Connection, ALL, NTLM
from PIL import Image

def ad_login(server, domain, account, password):
    # 二次验证方式 ，暂不启用，只要能连接连接上即可
    ad_server = Server('ldap://{}:389'.format(server), use_ssl=True)
    try:
        Connection(server=ad_server, user='{}\\{}'.format(domain, account), password=password, auto_bind=True)
        '''        
        ad_server = Server('ldap://{}:389'.format(server), use_ssl=True, get_info=ALL)
        connection = Connection(server=ad_server, user='dsg\\{}'.format(account), password=password, auto_bind=True, authentication=NTLM)
        connection.result
        print(connection.result)
        connection.search(
            search_base='dc=corp,dc=doosan,dc=com',
            search_filter='(&(objectCategory=Person)(sAMAccountName={username}))'.format(username=account),
            # attributes: 决定输出哪些属性
            # attributes=['cn', 'mail', 'distinguishedName', 'memberOf', 'sAMAccountName']
            attributes=['memberOf', 'sAMAccountName']
        )
        entities = connection.entries
        for entity in entities:
            print('sAMAccountName is ---------->  ', entity.sAMAccountName)
            if entity.sAMAccountName == account:
                return True
        '''
    except Exception as e:
        print('Exception : ---------------------------', e)
        return False
    return True
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
def format_date(date_to_format):
    return date_to_format.strftime('%Y-%m-%d')
def format_date_year(date_to_format):
    return date_to_format.strftime('%Y')
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
    from com.models import SysDict, SysEnum
    dictionary = SysDict.query.filter_by(code=code).first()
    enums = SysEnum.query.with_parent(dictionary).order_by(SysEnum.item).all()
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
    # 重新调整尺寸,高度调整为原来的60%
    with open(full_name, 'rb') as f:
        img = Image.open(f)
        w_size = img.size[0]
        h_size = int((float(img.size[1]) * 0.6))
        img = img.resize((w_size, h_size), PIL.Image.ANTIALIAS)
        img.save(current_app.config['BAR_CODE_PATH']+'\\'+code+'.png')
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
def gen_bill_no(prefix):
    '''
    生成单号
    :param prefix:
    :return:
    '''
    date_str = time.strftime('%Y%m%d')
    random_num = random.randint(1000, 10000)
    return prefix+date_str+str(random_num)
def cal_delta_time(base_date):
    from datetime import datetime, time, date
    '''
    计算年份时长,四舍五入保留一位小数
    :param base_date:
    :return:
    '''
    # 如果类型是date, 就转换为datetime类型
    if isinstance(base_date, date):
        base_date = datetime.combine(base_date, time())
    now = datetime.now()
    date_delta = (now - base_date).days
    years = round(date_delta / 365, ndigits=1)
    # print('Delta years : ', years)
    return years