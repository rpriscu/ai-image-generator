"""
Application entry point for the AI Image Generator.
Configures logging and runs the Flask application.
"""
from app import create_app
from app.models.models import db, User, MonthlyUsage, Admin
import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    """Configure application logging with rotating file handler"""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.mkdir('logs')
        
    # Configure file handler
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    
    # Add handlers to app logger
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('AI Image Generator startup')

# Create the application instance
app = create_app()

# Set up logging
setup_logging(app)

@app.shell_context_processor
def make_shell_context():
    """Add database and models to shell context for Flask shell"""
    return {
        'db': db,
        'User': User,
        'MonthlyUsage': MonthlyUsage,
        'Admin': Admin
    }

if __name__ == '__main__':
    # Get configuration from environment or use defaults
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    # Run the application
    app.run(host=host, port=port, debug=debug) 