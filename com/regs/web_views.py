def reg_web_views(app):
    '''
    注册系统模块
    :param app:
    :return:
    '''
    from com.views.auth import bp_auth                                 # 系统登录
    from com.views.main import bp_main                                 # 系统导航
    from com.views.system.module import bp_module                      # 系统模块
    from com.views.system.menu import bp_menu                          # 系统菜单
    from com.views.system.role import bp_role                          # 系统角色
    from com.views.system.dicts import bp_dict                         # 系统字典
    from com.views.system.user import bp_user                          # 系统用户
    from com.views.biz.organization.enterprise import bp_enterprise    # 组织管理-事业处
    from com.views.biz.organization.company import bp_company          # 组织管理-法人
    from com.views.biz.organization.department import bp_department    # 组织管理-部门
    from com.views.biz.organization.employee import bp_employee        # 组织管理-雇员
    from com.views.biz.master.clazz import bp_clazz                    # 基准管理-资产分类
    from com.views.biz.master.vendor import bp_vendor                  # 基准管理-供应商信息
    from com.views.biz.master.brand import bp_brand                    # 基准管理-品牌信息
    from com.views.biz.master.store import bp_store                    # 基准管理-仓库信息
    app.register_blueprint(bp_auth, url_prefix='/auth')
    app.register_blueprint(bp_main, url_prefix='/main')
    app.register_blueprint(bp_module, url_prefix='/module')
    app.register_blueprint(bp_menu, url_prefix='/menu')
    app.register_blueprint(bp_role, url_prefix='/role')
    app.register_blueprint(bp_dict, url_prefix='/dict')
    app.register_blueprint(bp_enterprise, url_prefix='/enterprise')
    app.register_blueprint(bp_company, url_prefix='/company')
    app.register_blueprint(bp_department, url_prefix='/department')
    app.register_blueprint(bp_employee, url_prefix='/employee')
    app.register_blueprint(bp_user, url_prefix='/user')
    app.register_blueprint(bp_clazz, url_prefix='/clazz')
    app.register_blueprint(bp_vendor, url_prefix='/vendor')
    app.register_blueprint(bp_brand, url_prefix='/brand')
    app.register_blueprint(bp_store, url_prefix='/store')