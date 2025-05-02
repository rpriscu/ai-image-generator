"""
Database configuration utilities.
Provides functions for configuring database connections.
"""
import os


def get_engine_url(app=None):
    """
    Get the SQLAlchemy database URL and engine options.
    
    Args:
        app: Flask application instance (optional)
        
    Returns:
        dict: Dictionary containing database URL and connection arguments
    """
    # If app is provided, try to get DATABASE_URL from app config
    if app and app.config.get('SQLALCHEMY_DATABASE_URI'):
        database_url = app.config.get('SQLALCHEMY_DATABASE_URI')
    else:
        database_url = os.environ.get('DATABASE_URL')
    
    # Handle special case for PostgreSQL URLs (heroku-style)
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://')
    
    # Set the URL in app config if provided
    if app:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    
    # Configure connection parameters based on database type
    connect_args = {
        'connect_timeout': 15,  # Default connection timeout in seconds
        'application_name': 'AI Image Generator'  # Application name for database logs
    }
    
    # For PostgreSQL on PythonAnywhere, we need to disable SSL
    if database_url and ('postgresql://' in database_url or 'postgres://' in database_url):
        connect_args.update({
            'sslmode': 'disable',  # Completely disable SSL
        })
    
    # Create configuration dictionary with database URL and connection arguments
    # This matches the expected structure in the server-side __init__.py
    return {
        'url': database_url,
        'connect_args': connect_args
    } 