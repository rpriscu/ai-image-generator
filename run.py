"""
Application entry point for the AI Image Generator.
Configures logging and runs the Flask application.
"""
from app import create_app
from app.models.models import db, User, MonthlyUsage, Admin
import os
import logging
from logging.handlers import RotatingFileHandler
from app.services.fal_api import fal_api_service
import atexit
import sys

def setup_logging(app):
    """Configure application logging with rotating file handler"""
    # Create logs directory if it doesn't exist and we're not on Heroku
    is_heroku = 'DYNO' in os.environ
    
    # Configure logging differently for Heroku vs local/PythonAnywhere
    if is_heroku:
        # Heroku already logs to stdout/stderr, so we configure for that
        # We'll still set up our formatter for consistency
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        stream_handler.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('AI Image Generator startup on Heroku')
    else:
        # For local or PythonAnywhere, use file-based logging
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

# Initialize services
with app.app_context():
    fal_api_service.init_app(app)
    
    # Create temporary directory for downloads
    temp_dir = os.path.join(app.root_path, 'static', 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    # Register cleanup function for temp directory
    def cleanup_temp_dir():
        """Clean up temporary files on application exit"""
        try:
            # Clean old files using utility function
            from app.utils.cleanup import clean_temp_files
            clean_temp_files(temp_dir=temp_dir, max_age_hours=2)
            app.logger.info(f"Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            app.logger.error(f"Error cleaning up temp directory: {str(e)}")
    
    # Register cleanup function to run on application exit
    atexit.register(cleanup_temp_dir)

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
    # Determine if running on a managed platform
    is_pythonanywhere = 'PYTHONANYWHERE_SITE' in os.environ
    is_heroku = 'DYNO' in os.environ
    
    if is_pythonanywhere or is_heroku:
        # When running on a managed platform, don't start the development server
        # The WSGI server will handle the requests
        app.logger.info('Running on managed platform - no need to start development server')
    else:
        # Get configuration from environment or use defaults
        host = os.environ.get('HOST', '0.0.0.0')
        port = int(os.environ.get('PORT', 8080))
        debug = os.environ.get('FLASK_ENV', 'development') == 'development'
        
        # Run the application with the development server
        app.logger.info(f'Starting development server on {host}:{port}')
        app.run(host=host, port=port, debug=debug) 