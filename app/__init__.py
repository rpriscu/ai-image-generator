"""
Main application factory module.
Creates and configures the Flask application.
"""
from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_session import Session
import os
import sys
from datetime import datetime

# Apply PostgreSQL dialect fix for Python 3.13 before importing SQLAlchemy
if sys.version_info.major == 3 and sys.version_info.minor == 13:
    # Apply PostgreSQL dialect fix before importing SQLAlchemy-based models
    try:
        from app.utils.db_fix import apply_postgres_dialect_fix
        apply_postgres_dialect_fix()
    except Exception as e:
        print(f"Error applying PostgreSQL dialect fix: {e}")

from app.models.models import db, User, Admin
from config import get_config

# Initialize extensions
login_manager = LoginManager()
migrate = Migrate()

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))

def register_blueprints(app):
    """Register Flask blueprints"""
    from app.routes.auth_routes import auth_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.user_routes import user_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)

def register_context_processors(app):
    """Register Jinja2 context processors"""
    @app.context_processor
    def inject_datetime():
        return {'current_year': datetime.utcnow().year}
    
    @app.context_processor
    def inject_is_production():
        is_pythonanywhere = 'PYTHONANYWHERE_SITE' in os.environ
        is_heroku = 'DYNO' in os.environ
        return {
            'is_production': is_pythonanywhere or is_heroku,
            'is_pythonanywhere': is_pythonanywhere,
            'is_heroku': is_heroku
        }

def configure_database(app):
    """Configure database connection based on environment"""
    # Fix PostgreSQL database URL if needed
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI')
    if db_url and db_url.startswith('postgres://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace('postgres://', 'postgresql://', 1)
        app.logger.info("Fixed PostgreSQL database URL format")
    
    # Handle PythonAnywhere specific configuration
    if 'PYTHONANYWHERE_SITE' in os.environ:
        from app.utils.db_config import get_engine_url
        
        # Get engine configuration
        engine_config = get_engine_url(app)
        
        # Update database URI if provided
        if engine_config.get('url'):
            app.config['SQLALCHEMY_DATABASE_URI'] = engine_config.get('url')
        
        # Set engine options for PostgreSQL on PythonAnywhere
        if isinstance(engine_config, dict) and 'connect_args' in engine_config:
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'connect_args': engine_config['connect_args']}
            app.logger.info("Configured special database settings for PythonAnywhere")
    
    # Handle Heroku specific configuration
    elif 'DYNO' in os.environ:
        app.logger.info("Detected Heroku environment")
        
        # Ensure we're using the correct dialect
        if sys.version_info.major == 3 and sys.version_info.minor == 13:
            from app.utils.db_fix import apply_postgres_dialect_fix
            apply_postgres_dialect_fix()
            app.logger.info("Applied PostgreSQL dialect fix for Python 3.13")
        
        # Heroku PostgreSQL configuration is handled in config.py
        # This is just for additional settings that might be needed
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_size': 10,
            'max_overflow': 2,
            'pool_recycle': 300,
            'pool_pre_ping': True
        }
        app.logger.info("Configured database pool settings for Heroku")

def create_default_admin(app):
    """Create default admin user if none exists"""
    # Skip admin creation if flag is set (for database setup)
    if app.config.get('SKIP_ADMIN_CREATION'):
        return
        
    with app.app_context():
        if Admin.query.count() == 0 and app.config.get('ADMIN_USERNAME') and app.config.get('ADMIN_PASSWORD'):
            Admin.create_admin(
                username=app.config.get('ADMIN_USERNAME'),
                password=app.config.get('ADMIN_PASSWORD')
            )

def create_app(config_class=None):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config_class if config_class else get_config())
    
    # Configure session settings based on environment
    # Default to filesystem sessions
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    
    # Check for Redis URL (Heroku add-on)
    redis_url = os.environ.get('REDIS_URL')
    if redis_url and 'DYNO' in os.environ:
        # Use Redis if available (better for Heroku)
        app.config['SESSION_TYPE'] = 'redis'
        app.config['SESSION_REDIS'] = redis_url
        app.logger.info("Using Redis for session storage")
    else:
        # Use filesystem sessions, setting the path based on environment
        if 'DYNO' in os.environ:
            app.config['SESSION_FILE_DIR'] = '/tmp/flask_session'
        else:
            app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session')
        
        # Create session directory if it doesn't exist
        if not os.path.exists(app.config['SESSION_FILE_DIR']):
            os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
            app.logger.info(f"Created session directory: {app.config['SESSION_FILE_DIR']}")
    
    # Configure database for the environment
    configure_database(app)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # Import our session interface fix first
    from app.utils.session_fix import configure_session_interface
    
    # Then initialize Flask-Session
    from flask_session import Session
    Session(app)
    
    # Now apply our custom session interface
    configure_session_interface(app)
    
    # Configure static files for PythonAnywhere
    from app.utils.static_files import configure_static_files
    configure_static_files(app)
    
    # Configure for Heroku if running on Heroku
    if 'DYNO' in os.environ:
        from heroku import configure_for_heroku
        configure_for_heroku(app)
    
    # Register context processors
    register_context_processors(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Create default admin user
    create_default_admin(app)
    
    return app 