import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class with shared settings"""
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    
    # Database settings - Fix for Heroku postgres:// URLs
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        # Heroku provides postgres:// URLs, but SQLAlchemy needs postgresql://
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        # Ensure we always have a valid URL format
        if not (db_url.startswith('postgresql://') or db_url.startswith('sqlite:///')):
            print("Warning: DATABASE_URL does not start with postgresql:// or sqlite:///")
    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # SQLAlchemy engine options - explicit for Python 3.13 compatibility
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'max_overflow': 2,
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'connect_args': {},
        'drivername': 'postgresql',  # Force dialect to be 'postgresql' not 'postgres'
    }
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # FAL AI settings
    FAL_KEY = os.environ.get('FAL_KEY')
    FAL_API_BASE_URL = os.environ.get('FAL_API_BASE_URL', 'https://fal.run')
    
    # Google OAuth settings
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GOOGLE_DISCOVERY_URL = 'https://accounts.google.com/.well-known/openid-configuration'
    ALLOWED_EMAIL_DOMAIN = os.environ.get('ALLOWED_EMAIL_DOMAIN', 'zemingo.com')
    
    # Admin credentials - used for initial setup only
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    
    # Deployment settings
    IS_PYTHONANYWHERE = 'PYTHONANYWHERE_SITE' in os.environ
    IS_HEROKU = 'DYNO' in os.environ
    SERVER_NAME = os.environ.get('SERVER_NAME')
    
    @staticmethod
    def get_host_url():
        """Get the host URL based on environment"""
        if Config.IS_PYTHONANYWHERE:
            return f"https://{os.environ.get('PYTHONANYWHERE_DOMAIN', 'rpriscu.pythonanywhere.com')}"
        elif Config.IS_HEROKU:
            return f"https://{os.environ.get('HEROKU_APP_NAME', '')}.herokuapp.com"
        else:
            return "http://localhost:8080"

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    # Use SQLite as fallback in development if no DATABASE_URL is provided
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///dev.db'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    # Use in-memory SQLite for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    # Disable CSRF protection in testing
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # Enforce having a proper SECRET_KEY in production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    # Enforce having a database URL in production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    # Set higher security headers for production
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get the current configuration based on FLASK_ENV environment variable"""
    # Check if running on a production platform
    if Config.IS_PYTHONANYWHERE or Config.IS_HEROKU:
        config_name = 'production'
    else:
        config_name = os.environ.get('FLASK_ENV', 'default')
    return config[config_name] 