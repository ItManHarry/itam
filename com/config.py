import os
from com.jobs.tasks import jobs
import logging
dev_db = os.getenv('DEV_DB', 'mysql+pymysql://itam:Itam2022@10.41.128.217:3306/itam')
uat_db = os.getenv('UAT_DB', 'mysql+pymysql://itam:Itam2022@10.41.128.217:3306/uitam')
pro_db = os.getenv('PRO_DB', 'mysql+pymysql://itam:Itam2022@10.41.128.177:3306/itam')
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
class GlobalConfig():
    SECRET_KEY = os.getenv('SECRET_KEY', '85a9168800d5b7ee452b82ba0467fa9586e49fc95a2cdbc09417f0ae7cf92b41')
    # SEND_FILE_MAX_AGE_DEFAULT = timedelta(seconds=1)
    LOG_LEVEL = logging.DEBUG                                       # 默认log等级
    LOG_PATH = os.path.join(basedir, 'logs\\log')                   # log文件路径
    BOOTSTRAP_SERVE_LOCAL = True                                    # Bootstrap本地化
    ITEM_COUNT_PER_PAGE = 20                                        # 分页每页条数
    AD_SERVER = os.getenv('AD_SERVER')                              # AD服务器地址
    AD_DOMAIN = os.getenv('AD_DOMAIN')                              # AD域名称
    BAR_CODE_PATH = os.path.join(basedir, 'codes\\bars')            # 条形码保存路径
    QR_CODE_PATH = os.path.join(basedir, 'codes\\qrs')              # 二维码保存路径
    PRINTER_TEMPLATE = os.path.join(basedir, 'printer\\PrinterTemplate.xlsx')   # 打印模板
    ASSET_APPLY_FILE_PATH = os.path.join(basedir, 'attachments\\biz\\apply')    # 资产申请附件路径
    FILE_UPLOAD_PATH = os.path.join(basedir, 'attachments')         # 附件存放路径
    MAIL_SERVER = os.getenv('MAIL_SERVER')                          # 邮箱服务器
    MAIL_DEFAULT_SENDER = ('系统通知提醒-IT资产管理', os.getenv('MAIL_SENDER'))  # 默认发件人
    MAIL_SUBJECT_PREFIX = '[Notice]'                                # 邮件主题前缀
    DROPZONE_MAX_FILE_SIZE = 30                                     # Dropzone上传文件大小(3M)
    DROPZONE_MAX_FILES = 20                                         # Dropzone上传文件最大数量
    MAX_CONTENT_LENGTH = 30 * 1024 * 1024                           # Flask内置文件上传大小设置
    DROPZONE_ALLOWED_FILE_TYPE = 'image'                            # Dropzone允许上传的文件类型
    DROPZONE_ENABLE_CSRF = True                                     # Dropzone上传启用CSRF令牌验证
    DROPZONE_IN_FORM = True                                         # 嵌入表单
    DROPZONE_UPLOAD_ON_CLICK = True                                 # 点击选择文件
    # 以下为Dropzone错误消息提示
    DROPZONE_INVALID_FILE_TYPE = '上传文件类型错误！'
    DROPZONE_FILE_TOO_BIG = '上传文件超过最大限制！'
    DROPZONE_SERVER_ERROR = '服务端错误!'
    DROPZONE_BROWSER_UNSUPPORTED = '浏览器不支持！'
    DROPZONE_MAX_FILE_EXCEED = '超出最大文件上传数量！'
    # 配置定时任务
    JOBS = jobs
    SCHEDULER_API_ENABLED = True
    SCHEDULER_JOB_DEFAULTS = {
        'coalesce': True,               # 积攒的任务只跑一次
        'max_instances': 1000,          # 支持1000个实例并发
        'misfire_grace_time': 600       # 600秒的任务超时容错
    }
    # SQLALCHEMY_ECHO = True              # 打印SQL
    # SQLALCHEMY_ECHO_POOL = True         # 连接池信息打印
    # 配置韩国HR数据库连接信息
    HR_SERVER = os.getenv('HR_SERVER', '')
    HR_USER = os.getenv('HR_USER', '')
    HR_PASSWORD = os.getenv('HR_PASSWORD', '')
    HR_DATABASE = os.getenv('HR_DATABASE', '')
class DevelopConfig(GlobalConfig):
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DEVELOP_DATABASE_URL', dev_db)
class UserTestConfig(GlobalConfig):
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv('UAT_DATABASE_URL', uat_db)
    WTF_CSRF_ENABLED = False
    TESTING = True
    LOG_LEVEL = logging.ERROR
class ProductConfig(GlobalConfig):
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv('PRODUCT_DATABASE_URL', pro_db)
    LOG_LEVEL = logging.ERROR
configurations = {
    'dev_config': DevelopConfig,
    'uat_config': UserTestConfig,
    'pro_config': ProductConfig
}