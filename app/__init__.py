"""
Main application factory module.
Creates and configures the Flask application.
"""
from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_session import Session
import os
from datetime import datetime

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

def configure_session(app):
    """Configure Flask-Session for server-side sessions"""
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session')
    Session(app)

def register_context_processors(app):
    """Register Jinja2 context processors"""
    @app.context_processor
    def inject_datetime():
        return {'current_year': datetime.utcnow().year}

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
    if config_class is None:
        app.config.from_object(get_config())
    else:
        app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Configure Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # Configure session
    configure_session(app)
    
    # Register context processors
    register_context_processors(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Create default admin user
    create_default_admin(app)
    
    return app 