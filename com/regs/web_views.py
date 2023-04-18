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
    from com.views.biz.master.email import bp_email                    # 基准管理-邮件通知配置
    from com.views.biz.audit.bizcode import bp_bizcode                 # 业务审批-审批业务代码管理
    from com.views.biz.audit.performer import bp_performer             # 业务审批-审批角色管理
    from com.views.biz.audit.line import bp_line                       # 业务审批-审批模板(审批线)
    from com.views.biz.audit.list import bp_list                       # 业务审批-My to do
    from com.views.biz.asset.apply import bp_apply                     # 资产登记-资产申请
    from com.views.biz.asset.buy import bp_buy                         # 资产登记-资产购买
    from com.views.biz.asset.master import bp_master                   # 资产登记-主数据
    from com.views.biz.asset.audit import bp_audit                     # 资产登记-资产审批
    from com.views.biz.daily.repair import bp_repair                   # 日常管理-资产维修
    from com.views.biz.daily.stockout import bp_stockout               # 日常管理-资产出库
    from com.views.biz.daily.scrap import bp_scrap                     # 日常管理-资产报废
    from com.views.biz.daily.inventory import bp_inventory             # 日常管理-资产盘点
    from com.views.biz.report.asset_rpt import bp_asset_rpt            # 系统报表-资产汇总报表
    from com.views.biz.report.asset_sap_rpt import bp_asset_sap_rpt    # 系统报表-SAP资产汇总报表
    from com.views.biz.report.repair_rpt import bp_repair_rpt          # 系统报表-维修履历报表
    from com.views.biz.report.scrap_rpt import bp_scrap_rpt            # 系统报表-报废履历报表
    from com.views.biz.report.stock_rpt import bp_stock_rpt            # 系统报表-库存查询报表
    from com.views.biz.report.asset_io_rpt import bp_asset_io_rpt      # 系统报表-资产出入库履历报表
    from com.views.biz.report.inventory_rpt import bp_inventory_rpt    # 系统报表-资产盘点报表

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
    app.register_blueprint(bp_email, url_prefix='/email')
    app.register_blueprint(bp_bizcode, url_prefix='/bizcode')
    app.register_blueprint(bp_performer, url_prefix='/performer')
    app.register_blueprint(bp_line, url_prefix='/line')
    app.register_blueprint(bp_list, url_prefix='/list')
    app.register_blueprint(bp_apply, url_prefix='/apply')
    app.register_blueprint(bp_buy, url_prefix='/buy')
    app.register_blueprint(bp_master, url_prefix='/master')
    app.register_blueprint(bp_audit,  url_prefix='/audit')
    app.register_blueprint(bp_repair,  url_prefix='/repair')
    app.register_blueprint(bp_stockout, url_prefix='/stockout')
    app.register_blueprint(bp_scrap, url_prefix='/scrap')
    app.register_blueprint(bp_inventory, url_prefix='/inventory')
    app.register_blueprint(bp_asset_rpt, url_prefix='/asset_rpt')
    app.register_blueprint(bp_asset_sap_rpt, url_prefix='/asset_sap_rpt')
    app.register_blueprint(bp_repair_rpt, url_prefix='/repair_rpt')
    app.register_blueprint(bp_scrap_rpt, url_prefix='/scrap_rpt')
    app.register_blueprint(bp_stock_rpt, url_prefix='/stock_rpt')
    app.register_blueprint(bp_asset_io_rpt, url_prefix='/asset_io_rpt')
    app.register_blueprint(bp_inventory_rpt, url_prefix='/inventory_rpt')