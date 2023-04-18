from flask import Flask
from com.config import configurations
from com.regs.web_globals import reg_web_global_path, reg_web_global_context
from com.regs.web_plugins import reg_web_plugins
from com.regs.web_shells import reg_web_shell, reg_web_commands
from com.regs.web_views import reg_web_views
from com.regs.web_log import setup_log
def create_app(config=None):
    if config is None:
        config = 'dev_config'
    app = Flask('com')
    app.config.from_object(configurations[config])
    setup_log(configurations[config])
    reg_web_global_path(app)
    reg_web_global_context(app)
    reg_web_plugins(app)
    reg_web_shell(app)
    reg_web_commands(app)
    reg_web_views(app)
    return app