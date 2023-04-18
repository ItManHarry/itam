from flask import request
from functools import wraps
from flask_login import current_user
from com.models import SysLog
from com.plugins import db
import uuid
'''
    写入日志
'''
def log_record(content):
    def decorator(function):
        @wraps(function)
        def decorated_function(*args, **kwargs):
            log = SysLog(id=uuid.uuid4().hex, url=request.path, operation=content, user=current_user, create_id=current_user.id)
            db.session.add(log)
            db.session.commit()
            return function(*args, **kwargs)
        return decorated_function
    return decorator