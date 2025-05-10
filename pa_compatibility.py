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
    'SQLAlchemy': '1.4.46',  # Add specific version for SQLAlchemy
    'sqlalchemy-utils': '0.38.3',
}

PA_COMPATIBLE_SESSION_FIX = """
\"\"\"
Flask-Session compatibility module for Python 3.9 on PythonAnywhere.
A simpler version for Python 3.9 which doesn't need the complex patching.
\"\"\"
from flask.sessions import SessionInterface
from flask_session.sessions import FileSystemSessionInterface

class FixedFileSystemSessionInterface(FileSystemSessionInterface):
    \"\"\"
    Fixed version of FileSystemSessionInterface for Python 3.9 on PythonAnywhere
    \"\"\"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure key_prefix is a string
        if self.key_prefix is None or isinstance(self.key_prefix, bool):
            self.key_prefix = "session:"
    
    def open_session(self, app, request):
        # Fix for Flask-Session on PythonAnywhere
        if not hasattr(app, 'session_cookie_name'):
            app.session_cookie_name = app.config.get('SESSION_COOKIE_NAME', 'session')
        
        return super().open_session(app, request)
    
    def save_session(self, app, session, response):
        \"\"\"
        Override save_session to handle the bool + str error
        \"\"\"
        # Fix the bool + str error in save_session
        if isinstance(self.key_prefix, bool):
            self.key_prefix = "session:"
        
        return super().save_session(app, session, response)

# Original function from Flask-Session but with a bug fixed
def fixed_save_session(self, app, session, response):
    \"\"\"
    A fixed version of the save_session method to handle boolean key_prefix
    \"\"\"
    domain = self.get_cookie_domain(app)
    path = self.get_cookie_path(app)
    
    # Skip if no session changes
    if not session.modified:
        return
    
    # Delete the session from storage if it's empty
    if not session:
        if session.modified:
            # Actually remove it from backing store if it was there
            key_prefix = self.key_prefix
            if isinstance(key_prefix, bool):
                key_prefix = "session:"
            
            if hasattr(self, "cache") and hasattr(session, "sid"):
                self.cache.delete(key_prefix + session.sid)
            
            response.delete_cookie(
                app.session_cookie_name,
                domain=domain,
                path=path
            )
        return
    
    # Otherwise, save it to the store
    httponly = self.get_cookie_httponly(app)
    secure = self.get_cookie_secure(app)
    expires = self.get_expiration_time(app, session)
    
    # Serialize
    val = self.serializer.dumps(dict(session))
    
    # Store in backend
    key_prefix = self.key_prefix
    if isinstance(key_prefix, bool):
        key_prefix = "session:"
    
    if hasattr(self, "cache") and hasattr(session, "sid"):
        self.cache.set(key_prefix + session.sid, val, 
                      int(app.permanent_session_lifetime.total_seconds()))
    
    # Set cookie
    response.set_cookie(
        app.session_cookie_name, 
        session.sid,
        expires=expires,
        httponly=httponly,
        domain=domain,
        path=path,
        secure=secure
    )

def monkey_patch_flask_session():
    \"\"\"Monkey patch Flask-Session to fix bool + str issue\"\"\"
    try:
        from flask_session.sessions import FileSystemSessionInterface
        
        # Store the original function for safety
        original_save_session = FileSystemSessionInterface.save_session
        
        # Apply our fixed version
        FileSystemSessionInterface.save_session = fixed_save_session
        
        print("Successfully patched Flask-Session")
        return True
    except ImportError:
        print("Failed to patch Flask-Session - module not found")
        return False

def configure_session_interface(app):
    \"\"\"
    Apply the session interface fix for PythonAnywhere
    \"\"\"
    # Patch Flask-Session first
    monkey_patch_flask_session()
    
    # Set the session cookie name if not already set
    if not hasattr(app, 'session_cookie_name'):
        app.session_cookie_name = app.config.get('SESSION_COOKIE_NAME', 'session')
    
    # Apply our fixed session interface
    app.session_interface = FixedFileSystemSessionInterface(
        app.config.get('SESSION_FILE_DIR'),
        app.config.get('SESSION_FILE_THRESHOLD', 500),
        app.config.get('SESSION_FILE_MODE', 0o600),
        app.config.get('SESSION_USE_SIGNER', False),
        app.config.get('SESSION_KEY_PREFIX', 'session:')
    )
    
    app.logger.info("Session compatibility module initialized for PythonAnywhere")
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