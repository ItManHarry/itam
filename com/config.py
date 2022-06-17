import os
from com.jobs.tasks import jobs
dev_db = os.getenv('DEV_DB')
uat_db = os.getenv('UAT_DB')
pro_db = os.getenv('PRO_DB')
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
class GlobalConfig():
    SECRET_KEY = os.getenv('SECRET_KEY', '123456789qazxswedcvfr!@#@452631')
    BOOTSTRAP_SERVE_LOCAL = True                                    # Bootstrap本地化
    ITEM_COUNT_PER_PAGE = 10
    AD_JAR_PATH = os.path.join(basedir, 'ad')                       # AD验证jar包路径
    BAR_CODE_PATH = os.path.join(basedir, 'codes\\bars')            # 条形码保存路径
    QR_CODE_PATH = os.path.join(basedir, 'codes\\qrs')              # 二维码保存路径
    FILE_UPLOAD_PATH = os.path.join(basedir, 'attachments')         # 附件存放路径
    MAIL_SERVER = os.getenv('MAIL_SERVER')                          # 邮箱服务器
    MAIL_DEFAULT_SENDER = ('IT Service', os.getenv('MAIL_SENDER'))  # 默认发件人
    MAIL_SUBJECT_PREFIX = '[Notice]'                                # 邮件主题前缀
    DROPZONE_MAX_FILE_SIZE = 3                                      # Dropzone上传文件大小(3M)
    DROPZONE_MAX_FILES = 5                                          # Dropzone上传文件最大数量
    MAX_CONTENT_LENGTH = 3 * 1024 * 1024                            # Flask内置文件上传大小设置
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
    # 配置韩国HR数据库连接信息
    HR_SERVER = os.getenv('HR_SERVER')
    HR_USER = os.getenv('HR_USER')
    HR_PASSWORD = os.getenv('HR_PASSWORD')
    HR_DATABASE = os.getenv('HR_DATABASE')
class DevelopConfig(GlobalConfig):
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DEVELOP_DATABASE_URL', dev_db)
    JVM_PATH = os.getenv('DEV_JVM_PATH', '')
class UserTestConfig(GlobalConfig):
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv('UAT_DATABASE_URL', uat_db)
    JVM_PATH = os.getenv('UAT_JVM_PATH', '')
    WTF_CSRF_ENABLED = False
    TESTING = True
class ProductConfig(GlobalConfig):
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv('PRODUCT_DATABASE_URL', pro_db)
    JVM_PATH = os.getenv('PRO_JVM_PATH', '')
configurations = {
    'dev_config': DevelopConfig,
    'uat_config': UserTestConfig,
    'pro_config': ProductConfig
}