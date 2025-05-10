"""
Python Anywhere Compatibility Helper

This script helps prepare the codebase for deployment to PythonAnywhere
with Python 3.9. It creates versions of files that are compatible with
Python 3.9 when needed.
"""
import os
import shutil
import subprocess
import sys

# Packages that need specific versions for PythonAnywhere
PA_PACKAGES = {
    'Flask': '2.0.3',
    'Werkzeug': '2.0.3',
    'Flask-Session': '0.4.0',
    'itsdangerous': '2.0.1',
    'jinja2': '3.0.3',
    'Flask-SQLAlchemy': '2.5.1',
    'SQLAlchemy': '1.4.46',
    'sqlalchemy-utils': '0.38.3',
}

PA_COMPATIBLE_SESSION_FIX = """
\"\"\"
Flask-Session compatibility module for Python 3.9 on PythonAnywhere.
A simpler version for Python 3.9 which doesn't need the complex patching.
\"\"\"
import os
import pickle
import datetime
from flask.sessions import SessionInterface, SessionMixin
from werkzeug.datastructures import CallbackDict

class SimpleSession(CallbackDict, SessionMixin):
    \"\"\"Simple dictionary session implementation.\"\"\"
    def __init__(self, initial=None, sid=None):
        def on_update(self):
            self.modified = True
        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        self.permanent = True
        self.modified = False

class SimpleFileSystemSession:
    \"\"\"Simple filesystem session implementation.\"\"\"

    def __init__(self, path):
        self.path = path
        try:
            os.makedirs(self.path)
        except OSError:
            pass

    def open_session(self, sid):
        filename = os.path.join(self.path, sid)
        if not os.path.exists(filename):
            return None
        try:
            with open(filename, 'rb') as f:
                return pickle.load(f)
        except:
            return None

    def save_session(self, sid, session_data):
        filename = os.path.join(self.path, sid)
        with open(filename, 'wb') as f:
            pickle.dump(session_data, f)

class SimpleSessionInterface(SessionInterface):
    \"\"\"Simple session interface implementation.\"\"\"

    def __init__(self, session_file_dir):
        self.session_file_dir = session_file_dir or os.path.join(os.getcwd(), 'flask_session')
        self.session_store = SimpleFileSystemSession(self.session_file_dir)

    def open_session(self, app, request):
        sid = request.cookies.get(app.config.get('SESSION_COOKIE_NAME', 'session'))
        if not sid:
            import uuid
            sid = str(uuid.uuid4())
            return SimpleSession(sid=sid)
        session_data = self.session_store.open_session(sid)
        if session_data is None:
            return SimpleSession(sid=sid)
        return SimpleSession(session_data, sid=sid)

    def save_session(self, app, session, response):
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        
        if not session:
            if session.modified:
                # Remove session file if empty
                try:
                    filename = os.path.join(self.session_file_dir, session.sid)
                    os.unlink(filename)
                except OSError:
                    pass
                response.delete_cookie(
                    app.config.get('SESSION_COOKIE_NAME', 'session'),
                    domain=domain,
                    path=path
                )
            return
        
        # Save session data
        if session.modified:
            self.session_store.save_session(session.sid, dict(session))
        
        # Set cookie
        httponly = self.get_cookie_httponly(app)
        secure = self.get_cookie_secure(app)
        expires = self.get_expiration_time(app, session)
        
        response.set_cookie(
            app.config.get('SESSION_COOKIE_NAME', 'session'),
            session.sid,
            expires=expires,
            httponly=httponly,
            domain=domain,
            path=path,
            secure=secure
        )

def configure_session_interface(app):
    \"\"\"
    Apply a simpler session interface for PythonAnywhere
    \"\"\"
    app.session_cookie_name = app.config.get('SESSION_COOKIE_NAME', 'session')
    
    # Use our simple session interface instead
    app.session_interface = SimpleSessionInterface(
        app.config.get('SESSION_FILE_DIR')
    )
    
    app.logger.info("Simple session compatibility module initialized for PythonAnywhere")
"""

def reset_environment():
    """Clean up the environment by uninstalling problematic packages"""
    print("Cleaning up environment before installing compatible versions...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "uninstall", "-y", 
            "Flask", "Flask-SQLAlchemy", "SQLAlchemy", "Flask-Session", 
            "Werkzeug", "itsdangerous", "jinja2"
        ])
        print("Successfully removed existing packages")
    except subprocess.CalledProcessError as e:
        print(f"Error removing packages: {e}")

def downgrade_packages():
    """Uninstall current packages and install specific versions that work well together"""
    print("Setting up compatible packages for PythonAnywhere...")
    
    # Clean up environment first
    reset_environment()
    
    # Create requirements file with specific versions
    with open("pa_requirements.txt", "w") as f:
        for package, version in PA_PACKAGES.items():
            f.write(f"{package}=={version}\n")
    
    # Install from the specific requirements file
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "pa_requirements.txt"
        ])
        print("Successfully installed compatible packages for PythonAnywhere")
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
        
    # Update the main requirements.txt file
    update_requirements()

def update_requirements():
    """Update requirements.txt with the compatible package versions"""
    if os.path.exists("requirements.txt"):
        with open("requirements.txt", "r") as f:
            requirements = f.readlines()
        
        new_requirements = []
        for line in requirements:
            if "==" in line:
                package = line.split("==")[0].strip()
                if package in PA_PACKAGES:
                    new_requirements.append(f"{package}=={PA_PACKAGES[package]}\n")
                else:
                    new_requirements.append(line)
            else:
                new_requirements.append(line)
        
        with open("requirements.txt", "w") as f:
            f.writelines(new_requirements)
        
        print("Updated requirements.txt with compatible package versions")

def create_pa_compatible_files():
    """Create Python 3.9 compatible versions of critical files"""
    # Create a Python 3.9 compatible version of session_fix.py
    utils_dir = os.path.join("app", "utils")
    if not os.path.exists(utils_dir):
        print(f"Creating directory: {utils_dir}")
        os.makedirs(utils_dir, exist_ok=True)
    
    session_fix_path = os.path.join(utils_dir, "session_fix.py")
    with open(session_fix_path, "w") as f:
        f.write(PA_COMPATIBLE_SESSION_FIX)
    
    print(f"Created Python 3.9 compatible session_fix.py at {session_fix_path}")
    print("Your application is now ready for deployment to PythonAnywhere with Python 3.9!")

if __name__ == "__main__":
    create_pa_compatible_files()
    downgrade_packages() 