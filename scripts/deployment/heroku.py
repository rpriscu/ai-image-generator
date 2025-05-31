"""
Heroku configuration helper module.

This module provides functions to help the application run properly on Heroku.
It's imported by the main application when it detects it's running on Heroku.
"""
import os
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Print diagnostic info
logger.info("=" * 80)
logger.info("HEROKU DEPLOYMENT STARTUP")
logger.info("=" * 80)
logger.info(f"Python version: {sys.version}")
logger.info(f"Heroku dyno: {os.environ.get('DYNO', 'Not detected')}")
logger.info(f"Startup time: {datetime.now().isoformat()}")
logger.info("=" * 80)

# Apply PostgreSQL dialect fix for Python 3.13 before importing SQLAlchemy
if sys.version_info.major == 3 and sys.version_info.minor >= 13:
    try:
        logger.info("Applying PostgreSQL dialect fix for Python 3.13...")
        from app.utils.db_fix import apply_postgres_dialect_fix
        apply_postgres_dialect_fix()
        logger.info("Successfully applied PostgreSQL dialect fix")
    except Exception as e:
        logger.error(f"Error applying PostgreSQL dialect fix: {e}")
        # Continue anyway to allow the app to attempt to start

# Apply Werkzeug cookie fixes for Python 3.13
if sys.version_info.major == 3 and sys.version_info.minor >= 13:
    try:
        logger.info("Applying Werkzeug cookie fixes for Python 3.13...")
        from app.utils.session_fix import apply_cookie_fixes
        apply_cookie_fixes()
        logger.info("Successfully applied Werkzeug cookie fixes")
    except Exception as e:
        logger.error(f"Error applying Werkzeug cookie fixes: {e}")
        # Continue anyway

# Handle any DATABASE_URL that starts with postgres:// 
db_url = os.environ.get('DATABASE_URL', '')
if db_url.startswith('postgres://'):
    logger.info("Converting postgres:// to postgresql:// in DATABASE_URL")
    os.environ['DATABASE_URL'] = db_url.replace('postgres://', 'postgresql://', 1)


def configure_for_heroku(app):
    """Configure the Flask app for Heroku deployment"""
    try:
        logger.info("Configuring Flask app for Heroku...")
        
        # Database Schema Update for Heroku
        with app.app_context():
            try:
                from app.models.models import Asset, db
                from sqlalchemy import inspect, text
                
                # Check if we need to update the file_url column
                inspector = inspect(db.engine)
                
                # Log all tables for diagnostic purposes
                tables = inspector.get_table_names()
                logger.info(f"Database tables: {', '.join(tables)}")
                
                # Check asset table
                if 'asset' in tables:
                    columns = {col['name']: col for col in inspector.get_columns('asset')}
                    
                    if 'file_url' in columns:
                        col_type = columns['file_url']['type']
                        logger.info(f"Current asset.file_url column type: {col_type}")
                        
                        # Check if we need to update the column length
                        if hasattr(col_type, 'length') and col_type.length != 2048:
                            logger.warning(f"Detected Asset.file_url column with size {col_type.length}, updating to 2048 characters")
                            
                            # Execute SQL to alter the column size
                            db.session.execute(text("ALTER TABLE asset ALTER COLUMN file_url TYPE VARCHAR(2048)"))
                            db.session.commit()
                            logger.info("Successfully updated asset.file_url column size to 2048")
                        else:
                            logger.info("asset.file_url column already has correct size")
                    else:
                        logger.warning("file_url column not found in asset table")
                else:
                    logger.warning("asset table not found in database")
            except Exception as e:
                logger.error(f"Error checking/updating database schema: {str(e)}")
                # Continue anyway to allow the app to start
        
        # Additional Heroku-specific configuration
        if 'DYNO' in os.environ:
            import logging
            
            # Configure gunicorn logging when on Heroku
            if 'gunicorn' in sys.modules:
                gunicorn_logger = logging.getLogger('gunicorn.error')
                app.logger.handlers = gunicorn_logger.handlers
                app.logger.setLevel(gunicorn_logger.level)
            
            # Special handling for web dynos to configure SSL
            if os.environ.get('DYNO', '').startswith('web.'):
                # Configure secure headers if flask-talisman is available
                try:
                    from flask_talisman import Talisman
                    Talisman(app, force_https=True)
                    logger.info("Talisman configured for HTTPS")
                except ImportError:
                    logger.info("flask-talisman not available, skipping HTTPS configuration")
                except Exception as e:
                    logger.warning(f"Could not configure Talisman: {e}")
        
        logger.info("Successfully configured Flask app for Heroku")
        
    except Exception as e:
        logger.error(f"Error configuring app for Heroku: {e}")
        # Continue anyway to allow the app to start 