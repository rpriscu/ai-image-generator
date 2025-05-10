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

# Packages that need to be downgraded for Python 3.9 on PythonAnywhere
PA_PACKAGES = {
    'Flask': '2.2.3',
    'Werkzeug': '2.2.3',
    'Flask-Session': '0.4.0',
    'itsdangerous': '2.1.2',
    'jinja2': '3.1.2'
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
    def open_session(self, app, request):
        # Fix for Flask-Session on PythonAnywhere
        if not hasattr(app, 'session_cookie_name'):
            app.session_cookie_name = app.config.get('SESSION_COOKIE_NAME', 'session')
        
        return super().open_session(app, request)

def configure_session_interface(app):
    \"\"\"
    Apply the session interface fix for PythonAnywhere
    \"\"\"
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

def downgrade_packages():
    """Downgrade packages to versions that work with Python 3.9 on PythonAnywhere"""
    print("Downgrading packages for PythonAnywhere compatibility...")
    
    for package, version in PA_PACKAGES.items():
        print(f"Downgrading {package} to version {version}...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                f"{package}=={version}", "--force-reinstall"
            ])
            print(f"Successfully downgraded {package} to version {version}")
        except subprocess.CalledProcessError as e:
            print(f"Error downgrading {package}: {e}")
    
    # Update the requirements.txt file
    try:
        update_requirements()
    except Exception as e:
        print(f"Error updating requirements.txt: {e}")
    
    print("\nAll packages have been downgraded for PythonAnywhere compatibility.")

def update_requirements():
    """Update requirements.txt with the downgraded package versions"""
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