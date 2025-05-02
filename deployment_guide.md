# Deployment Guide for PythonAnywhere

This guide provides step-by-step instructions for deploying the AI Image Generator application to PythonAnywhere.

## 1. Create a PythonAnywhere Account

If you don't already have one, create a PythonAnywhere account at [https://www.pythonanywhere.com/](https://www.pythonanywhere.com/).

## 2. Clone the Repository

Open a PythonAnywhere bash console and clone the repository:

```bash
git clone https://github.com/rpriscu/ai-image-generator.git
cd ai-image-generator
```

## 3. Create a Virtual Environment

Create and activate a virtual environment:

```bash
mkvirtualenv --python=python3.11 ai-image-generator
```

## 4. Install Dependencies

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## 5. Configure Environment Variables

Create a `.env` file in the project directory:

```bash
# In PythonAnywhere bash console
touch .env
```

Then edit the `.env` file using the PythonAnywhere editor and add your configuration:

```
# Flask configuration
SECRET_KEY=your_secure_random_key
FLASK_ENV=production

# Database configuration
DATABASE_URL=mysql://username:password@username.mysql.pythonanywhere-services.com/username$dbname

# PythonAnywhere configuration
PYTHONANYWHERE_DOMAIN=yourusername.pythonanywhere.com

# FAL.ai API configuration
FAL_KEY=your_fal_api_key

# Google OAuth configuration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
ALLOWED_EMAIL_DOMAIN=zemingo.com

# Admin user credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure_admin_password
```

## 6. Configure the Web App

1. Go to the PythonAnywhere dashboard and click on the "Web" tab
2. Click "Add a new web app"
3. Select "Manual configuration" and Python 3.11
4. Set the following settings:
   - **Source code**: `/home/yourusername/ai-image-generator`
   - **Working directory**: `/home/yourusername/ai-image-generator`
   - **Virtual environment**: `/home/yourusername/.virtualenvs/ai-image-generator`

## 7. Configure the WSGI File

Edit the WSGI configuration file (`/var/www/yourusername_pythonanywhere_com_wsgi.py`) with the following content:

```python
import sys
import os

# Add your project directory to the path
project_home = '/home/yourusername/ai-image-generator'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['PYTHONANYWHERE_SITE'] = 'True'

# Import your app from run.py
from run import app as application
```

## 8. Configure Static Files

In the PythonAnywhere web app configuration, add the following static files mapping:

- **URL**: `/static/`
- **Directory**: `/home/yourusername/ai-image-generator/app/static`

## 9. Set Up the Database

Create a MySQL database from the PythonAnywhere dashboard (Databases tab), then initialize it:

```bash
cd ai-image-generator
python setup_db.py --init
python setup_db.py --create-admin
```

## 10. Reload the Web App

Click the "Reload" button on your web app's configuration page.

## 11. Set Up Scheduled Tasks

To ensure your application runs smoothly, set up some scheduled tasks:

1. Go to the "Tasks" tab in PythonAnywhere
2. Add a task to clean up temporary files daily:
   - **Command**: `cd /home/yourusername/ai-image-generator && /home/yourusername/.virtualenvs/ai-image-generator/bin/python -c "from app.utils.cleanup import clean_temp_files; clean_temp_files()"`
   - **Schedule**: Daily

## 12. Updating the Application

When you need to update the application, run these commands in a PythonAnywhere bash console:

```bash
cd ai-image-generator
git pull
workon ai-image-generator
pip install -r requirements.txt
# If there are database migrations
flask db upgrade
# Reload the web app from the Web tab
```

## Troubleshooting

### Database Connection Issues

If you experience database connection issues, check if your `DATABASE_URL` is correct and if your database exists. You can also try using the PythonAnywhere database without SSL:

```
DATABASE_URL=mysql://username:password@username.mysql.pythonanywhere-services.com/username$dbname?ssl=0
```

### Static Files Not Loading

Make sure your static files mapping is correct. Also check that the permissions on the static directory allow the web app to read the files.

### Error Logs

Check the error logs in the PythonAnywhere web app configuration page for detailed error messages. 