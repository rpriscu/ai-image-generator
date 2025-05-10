"""
Python Anywhere Compatibility Helper

This script helps prepare the codebase for deployment to PythonAnywhere
with Python 3.9. It creates versions of files that are compatible with
Python 3.9 when needed.
"""
import os
import shutil

PA_COMPATIBLE_SESSION_FIX = """
\"\"\"
Flask-Session compatibility module for Python 3.9 on PythonAnywhere.
A simpler version for Python 3.9 which doesn't need the complex patching.
\"\"\"
from flask.sessions import SessionInterface

def configure_session_interface(app):
    \"\"\"
    Simple compatibility function for Python 3.9
    No patches needed for Python 3.9 on PythonAnywhere
    \"\"\"
    app.logger.info("Session compatibility module initialized (Python 3.9 compatible mode)")
"""

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