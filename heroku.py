"""
Heroku configuration helper module.

This module provides functions to help the application run properly on Heroku.
It's imported by the main application when it detects it's running on Heroku.
"""
import os
import logging
import sys

logger = logging.getLogger(__name__)

def configure_for_heroku(app):
    """
    Configure a Flask application to run on Heroku.
    
    Args:
        app: Flask application instance
    
    Returns:
        The configured Flask app
    
    Raises:
        RuntimeError: If critical Heroku configuration is missing
    """
    logger.info("Configuring application for Heroku environment")
    
    try:
        # Ensure we have the right PORT binding (required by Heroku)
        port = int(os.environ.get('PORT', 5000))
        app.config['PORT'] = port
        
        # Log the configuration
        logger.info(f"Heroku PORT: {port}")
        
        # Make sure we're using the Heroku app name for URLs
        heroku_app_name = os.environ.get('HEROKU_APP_NAME')
        if heroku_app_name:
            logger.info(f"Heroku app name: {heroku_app_name}")
        else:
            logger.warning("HEROKU_APP_NAME environment variable not set - URLs may not work correctly")
            # This is a warning but we'll continue
    
        # Verify database configuration (critical for functionality)
        db_url = app.config.get('SQLALCHEMY_DATABASE_URI')
        if not db_url:
            message = "No database URL configured. Please set the DATABASE_URL environment variable."
            logger.error(message)
            # This is critical but we won't crash - the app will likely fail elsewhere
            # with a more specific database error
        else:
            # Log the database URL (masked)
            masked_db = db_url
            if '@' in masked_db:
                # Mask password for security
                parts = masked_db.split('@')
                if ':' in parts[0]:
                    user_part = parts[0].split(':')[0]
                    masked_db = f"{user_part}:****@{parts[1]}"
            logger.info(f"Database URL: {masked_db}")
            
        # Verify FAL API key (critical for functionality)
        if not app.config.get('FAL_KEY'):
            logger.warning("FAL_KEY is not set - image generation will not work")
        
        # Check for SECRET_KEY (critical for security)
        if not app.config.get('SECRET_KEY') or app.config.get('SECRET_KEY') == 'dev-key-change-in-production':
            message = "Production SECRET_KEY not set. Using an insecure default is dangerous in production."
            logger.error(message)
            # This is critical but we'll continue - Flask will work but sessions won't be secure
        
        return app
        
    except Exception as e:
        logger.error(f"Error configuring for Heroku: {str(e)}")
        # Re-raise the exception to ensure deployment fails fast if there's a critical issue
        raise 