"""
WSGI configuration file for PythonAnywhere deployment.
This should be used as the WSGI configuration file in PythonAnywhere settings.
"""
import sys
import os

# Add your project directory to the path
project_home = '/home/rpriscu/ai-image-generator'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['PYTHONANYWHERE_SITE'] = 'True'

# Import the Flask application
from run import app as application

# Tell PythonAnywhere this is a WSGI application
application.secret_key = os.environ.get('SECRET_KEY', 'default-secret-key') 