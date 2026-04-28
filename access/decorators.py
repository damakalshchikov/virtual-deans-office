from functools import wraps
from flask import abort
from flask_login import current_user
from models import db, RolePermission, Permission


def requires_role(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator


def has_permission(role: str, code: str) -> bool:
    """Проверяет, есть ли у роли право с указанным кодом."""
    if role == "admin":
        # Администратор всегда имеет все права
        return True
    return db.session.query(RolePermission).join(Permission).filter(
        RolePermission.role == role,
        Permission.code == code
    ).first() is not None
