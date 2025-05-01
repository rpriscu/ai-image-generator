from flask import session, redirect, url_for, request, abort
from functools import wraps
import logging

logger = logging.getLogger(__name__)

def is_user_authenticated():
    """Check if the user is authenticated"""
    return 'user_id' in session

def require_login(f):
    """Decorator to require user login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_user_authenticated():
            logger.info(f"Unauthenticated access attempt to {request.path}")
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def is_admin_authenticated():
    """Check if the admin is authenticated"""
    return 'admin_id' in session

def require_admin(f):
    """Decorator to require admin login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin_authenticated():
            logger.warning(f"Unauthorized admin access attempt to {request.path} from {request.remote_addr}")
            return redirect(url_for('admin.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def get_user_info():
    """Get the current user's information from the session"""
    if not is_user_authenticated():
        return None

    return {
        'id': session.get('user_id'),
        'email': session.get('user_email'),
        'name': session.get('user_name'),
        'picture': session.get('user_picture')
    }

def get_admin_info():
    """Get the current admin's information from the session"""
    if not is_admin_authenticated():
        return None

    return {
        'id': session.get('admin_id'),
        'username': session.get('admin_username')
    } 