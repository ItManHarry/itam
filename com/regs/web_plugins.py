from com.plugins import *
def reg_web_plugins(app):
    '''
    注册系统插件
    :param app:
    :return:
    '''
    db.init_app(app)
    bootstrap.init_app(app)
    # moment.init_app(app)
    mail.init_app(app)
    ckeditor.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    dropzone.init_app(app)
    login_manager.init_app(app)
    # babel.init_app(app)
    scheduler.init_app(app)
    scheduler.start()