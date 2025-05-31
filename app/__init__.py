"""
Main application factory module.
Creates and configures the Flask application.
"""
from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
import os
import sys
from datetime import datetime

# Print diagnostic info
print(f"Python version: {sys.version}")
print(f"Initializing Flask application with Python {sys.version_info.major}.{sys.version_info.minor}")

# Apply fixes for Python 3.13
if sys.version_info.major == 3 and sys.version_info.minor == 13:
    # Apply PostgreSQL dialect fix before importing SQLAlchemy-based models
    try:
        print("Applying PostgreSQL dialect fix from app/__init__.py...")
        from app.utils.db_fix import apply_postgres_dialect_fix
        apply_postgres_dialect_fix()
        print("Successfully applied PostgreSQL dialect fix from app/__init__.py")
    except Exception as e:
        print(f"Error applying PostgreSQL dialect fix: {e}")
    
    # Apply Werkzeug cookie handling fix
    try:
        print("Applying Werkzeug cookie handling fix from app/__init__.py...")
        from app.utils.werkzeug_fix import patch_werkzeug_cookie_functions
        patch_werkzeug_cookie_functions()
        print("Successfully applied Werkzeug cookie handling fix from app/__init__.py")
    except Exception as e:
        print(f"Error applying Werkzeug cookie fix: {e}")

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
    if app.config.get('SKIP_ADMIN_CREATION') or os.environ.get('SKIP_ADMIN_CREATION') == '1':
        print("Skipping admin creation as requested by config or environment variable")
        return
        
    try:
        with app.app_context():
            # Try to check if admin table exists first
            try:
                # Import inspect here to avoid circular imports
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                if 'admin' not in inspector.get_table_names():
                    print("Admin table does not exist yet - skipping admin check")
                    return
            except Exception as e:
                print(f"Could not check for admin table: {e}")
                return
                
            # Now it's safe to query the admin table
            try:
                admin_count = Admin.query.count()
                if admin_count == 0 and app.config.get('ADMIN_USERNAME') and app.config.get('ADMIN_PASSWORD'):
                    print(f"Creating default admin user: {app.config.get('ADMIN_USERNAME')}")
                    Admin.create_admin(
                        username=app.config.get('ADMIN_USERNAME'),
                        password=app.config.get('ADMIN_PASSWORD')
                    )
                    print("Default admin user created successfully")
                else:
                    print(f"Admin user already exists or credentials not provided")
            except Exception as e:
                print(f"Error checking or creating admin user: {e}")
    except Exception as e:
        print(f"Error in create_default_admin: {e}")
        # Don't raise the exception to allow the app to continue starting up

def create_app(config_name=None):
    """Create and configure the Flask application"""
    print("Creating Flask application...")
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config_name if config_name else get_config())
    
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
        print("Using Redis for session storage")
    else:
        # Use filesystem sessions, setting the path based on environment
        if 'DYNO' in os.environ:
            app.config['SESSION_FILE_DIR'] = '/tmp/flask_session'
            print(f"Using filesystem sessions with path: /tmp/flask_session")
        else:
            app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session')
            print(f"Using filesystem sessions with path: {os.path.join(os.getcwd(), 'flask_session')}")
        
        # Create session directory if it doesn't exist
        if not os.path.exists(app.config['SESSION_FILE_DIR']):
            os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
            print(f"Created session directory: {app.config['SESSION_FILE_DIR']}")
    
    # Configure database for the environment
    print("Configuring database...")
    configure_database(app)
    
    # Initialize extensions
    print("Initializing extensions...")
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # Import our session interface fix first
    print("Importing session interface fix...")
    from app.utils.session_fix import configure_session_interface
    
    # Initialize Flask-Session with our patched version
    # Important: Do not import Session directly here, use configure_session_interface
    print("Configuring session interface...")
    configure_session_interface(app)
    print("Session interface configured")
    
    # Configure static files for PythonAnywhere
    from app.utils.static_files import configure_static_files
    configure_static_files(app)
    
    # Configure for Heroku if running on Heroku
    if 'DYNO' in os.environ:
        print("Configuring for Heroku...")
        from scripts.deployment.heroku import configure_for_heroku
        configure_for_heroku(app)
    
    # Register context processors
    register_context_processors(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Create default admin user
    create_default_admin(app)
    
    # Check database schema on startup
    with app.app_context():
        from app.models.models import Asset
        from sqlalchemy import inspect, text
        
        # Only in production (Heroku)
        if os.environ.get('DYNO'):
            try:
                # Check if we need to update the file_url column
                inspector = inspect(db.engine)
                columns = {col['name']: col for col in inspector.get_columns('asset')}
                
                if 'file_url' in columns and columns['file_url']['type'].length != 2048:
                    app.logger.warning("Detected Asset.file_url column with wrong size, updating to 2048 characters")
                    
                    # Execute SQL to alter the column size
                    db.session.execute(text("ALTER TABLE asset ALTER COLUMN file_url TYPE VARCHAR(2048)"))
                    db.session.commit()
                    app.logger.info("Successfully updated asset.file_url column size to 2048")
            except Exception as e:
                app.logger.error(f"Error checking/updating database schema: {str(e)}")
    
    print("Flask application created successfully")
    return app 