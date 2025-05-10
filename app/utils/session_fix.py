"""
Flask-Session compatibility module for Python 3.13.
This provides a complete replacement for the session interface to fix compatibility issues.
"""
from flask_session.sessions import FileSystemSessionInterface
from flask.sessions import SessionMixin
from werkzeug.datastructures import CallbackDict
from flask import Flask
import os
import tempfile
import pickle
from uuid import uuid4

class FixedFileSystemSessionInterface(FileSystemSessionInterface):
    """
    A completely rewritten FileSystemSessionInterface that handles all compatibility issues
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure key_prefix is a string 
        if self.key_prefix is None or isinstance(self.key_prefix, bool):
            self.key_prefix = "session:"
    
    def open_session(self, app, request):
        """
        Override to fix compatibility issues with different Python versions
        """
        sid = request.cookies.get(app.config['SESSION_COOKIE_NAME'])
        
        if not sid:
            return self.session_class({}, sid=str(uuid4()))
            
        # Handle case where sid might be bytes
        if isinstance(sid, bytes):
            sid = sid.decode('utf-8')
            
        # Ensure key_prefix is a string
        if isinstance(self.key_prefix, bool) or self.key_prefix is None:
            key_prefix = "session:"
        else:
            key_prefix = self.key_prefix
            
        # Build the full path
        path = os.path.join(self.get_session_data_dir(app), key_prefix + sid)
        
        try:
            data = {}
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    data = pickle.load(f)
            return self.session_class(data, sid=sid)
        except Exception as e:
            app.logger.error(f"Error loading session: {e}")
            return self.session_class({}, sid=str(uuid4()))
            
    def save_session(self, app, session, response):
        """
        Override to fix compatibility issues with different Python versions
        """
        path = os.path.join(self.get_session_data_dir(app), 
                            (self.key_prefix if isinstance(self.key_prefix, str) else "session:") + 
                            (session.sid if isinstance(session.sid, str) else str(session.sid)))
                            
        # Make sure the directory exists
        dir_path = os.path.dirname(path)
        os.makedirs(dir_path, exist_ok=True)
        
        # Don't save if the session is not modified and not permanent
        if not session.modified and not app.config.get('SESSION_PERMANENT', False):
            return
            
        # Don't save empty sessions
        if not session:
            if os.path.exists(path):
                os.unlink(path)
            return
            
        # Save the session
        with open(path, 'wb') as f:
            pickle.dump(dict(session), f)
            
        # Set the cookie
        self._set_cookie(app, session, response)

    def get_session_data_dir(self, app):
        """Get the session data directory, creating it if it doesn't exist"""
        data_dir = app.config.get('SESSION_FILE_DIR')
        if data_dir is None:
            data_dir = os.path.join(tempfile.gettempdir(), 'flask_session')
        if not os.path.isdir(data_dir):
            os.makedirs(data_dir, exist_ok=True)
        return data_dir
        
    def _set_cookie(self, app, session, response):
        """Set the session cookie"""
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        
        if not session.modified and not app.config.get('SESSION_REFRESH_EACH_REQUEST', False):
            return
            
        httponly = self.get_cookie_httponly(app)
        secure = self.get_cookie_secure(app)
        samesite = self.get_cookie_samesite(app)
        
        if session.permanent:
            max_age = app.permanent_session_lifetime
        else:
            max_age = None
            
        # Make sure session.sid is a string
        sid = session.sid if isinstance(session.sid, str) else str(session.sid)
        
        response.set_cookie(
            app.config['SESSION_COOKIE_NAME'], 
            sid,
            max_age=max_age,
            expires=self.get_expiration_time(app, session),
            path=path,
            domain=domain,
            secure=secure,
            httponly=httponly,
            samesite=samesite
        )

def configure_session_interface(app):
    """
    Replace the Flask-Session interface with our fixed version
    """
    # Create and apply our fixed session interface
    app.session_interface = FixedFileSystemSessionInterface(
        app.config.get('SESSION_FILE_DIR'),
        app.config.get('SESSION_FILE_THRESHOLD', 500),
        app.config.get('SESSION_FILE_MODE', 0o600),
        app.config.get('SESSION_USE_SIGNER', False),
        app.config.get('SESSION_KEY_PREFIX', 'session:')
    )
    
    app.logger.info("Configured fixed session interface for Python 3.13 compatibility")