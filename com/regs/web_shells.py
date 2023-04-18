import click, uuid
from com.plugins import db
def reg_web_shell(app):
    @app.shell_context_processor
    def config_shell_context():
        return dict(db=db)
def reg_web_commands(app):
    @app.cli.command()
    @click.option('--admin_code', prompt=True, help='管理员账号')
    @click.option('--admin_password', prompt=True, help='管理员密码', hide_input=True, confirmation_prompt=True)
    def init(admin_code, admin_password):
        from com.models import \
            SysUser, SysRole, SysModule, SysMenu, SysDict, SysEnum, BizEnterprise, BizCompany
        click.echo('执行数据库初始化......')
        db.create_all()
        click.echo('数据库初始化完毕')
        click.echo('创建超级管理员角色......')
        role = SysRole.query.first()
        if role:
            click.echo('管理员角色已存在，跳过创建')
        else:
            role = SysRole(id=uuid.uuid4().hex, name='Administrator')
            db.session.add(role)
            db.session.commit()
        click.echo('创建超级管理员......')
        user = SysUser.query.first()
        if user:
            click.echo('管理员已存在，跳过创建')
        else:
            user = SysUser(
                id=uuid.uuid4().hex,
                user_id=admin_code.lower(),
                user_name='Administrator',
                is_admin=True,
                role_id=role.id
            )
            user.set_password(admin_password)
            db.session.add(user)
            db.session.commit()
        click.echo('超级管理员创建成功')
        click.echo('初始化系统模块')
        modules = SysModule.query.all()
        if modules:
            click.echo('系统模块已创建，跳过')
        else:
            modules = (
                ('sys', '系统管理', 1),
                ('org', '组织管理', 2),
            )
            for module_info in modules:
                module = SysModule(
                    id=uuid.uuid4().hex,
                    code=module_info[0],
                    name=module_info[1],
                    order_by=module_info[2],
                    create_id=user.id,
                    update_id=user.id
                )
                db.session.add(module)
                db.session.commit()
        click.echo('系统模块初始化完成')
        click.echo('初始化系统菜单')
        # 菜单名称, URL地址, 菜单描述, 菜单图标, 模块所属, 对应模块下菜单显示顺序
        menus = (
            ('SY001', '用户管理', 'user.index', '管理系统用户(添加、修改、启用/停用等)', 'bi bi-person', 'sys', 1),
            ('SY002', '角色管理', 'role.index', '管理系统角色(新增/修改等)', 'bi bi-mortarboard', 'sys', 2),
            ('SY003', '模块管理', 'module.index', '管理系统模块(新增/修改等)', 'bi bi-columns-gap', 'sys', 3),
            ('SY004', '菜单管理', 'menu.index', '管理系统菜单(新增/修改/停用等)', 'bi bi-menu-button', 'sys', 4),
            ('SY005', '字典管理', 'dict.index', '管理系统下拉选项，包括新增、修改等', 'bi bi-book', 'sys', 5),
            ('HR001', '事业处管理', 'enterprise.index', '事业处信息(新增/修改/停用等)', 'bi bi-building', 'org', 1),
            ('HR002', '法人管理', 'company.index', '法人信息(新增/修改/停用等)', 'bi bi-bank', 'org', 2),
            ('HR003', '部门管理', 'department.index', '部门信息(新增/修改/停用等)', 'bi bi-diagram-3', 'org', 3),
            ('HR004', '雇员管理', 'employee.index', '雇员信息(新增/修改/停用等)', 'bi bi-people', 'org', 4),
        )
        if SysMenu.query.all():
            click.echo('系统菜单已创建，跳过')
        else:
            for menu_info in menus:
                menu = SysMenu(
                    id=uuid.uuid4().hex,
                    code=menu_info[0],
                    name=menu_info[1],
                    url=menu_info[2],
                    remark=menu_info[3],
                    icon=menu_info[4],
                    module=SysModule.query.filter_by(code=menu_info[5]).first(),
                    order_by=menu_info[6],
                    create_id=user.id,
                    update_id=user.id
                )
                db.session.add(menu)
                # 设定角色
                role.menus.append(menu)
                db.session.commit()
            click.echo('菜单初始化完成')
        click.echo('初始化系统字典')
        dicts = SysDict.query.all()
        if dicts:
            click.echo('系统字典已创建，跳过')
        else:
            dicts = (
                ('D001', '是否'),
            )
            for d in dicts:
                dictionary = SysDict(
                    id=uuid.uuid4().hex,
                    code=d[0],
                    name=d[1],
                    create_id=user.id,
                    update_id=user.id
                )
                db.session.add(dictionary)
                db.session.commit()
            click.echo('系统字典初始化完成')
        click.echo('初始化字典枚举值')
        enums = SysEnum.query.all()
        if enums:
            click.echo('字典枚举已维护，跳过')
        else:
            enums = (
                ('1', '是', 'D001', 1),
                ('2', '否', 'D001', 2),
            )
            for enum in enums:
                enumeration = SysEnum(
                    id=uuid.uuid4().hex,
                    item=enum[0],
                    display=enum[1],
                    dictionary=SysDict.query.filter_by(code=enum[2]).first(),
                    order_by=enum[3],
                    create_id=user.id,
                    update_id=user.id
                )
                db.session.add(enumeration)
                db.session.commit()
            click.echo('字典枚举初始化完成')
        click.echo('初始化事业处信息')
        BizEnterprise.init_enterprises()
        click.echo('事业处初始化完成')
        click.echo('初始化法人信息')
        BizCompany.init_companies()
        click.echo('法人初始化完成')
        click.echo('系统初始化完成')