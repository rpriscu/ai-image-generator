"""
Static files helper for PythonAnywhere deployment.
This module provides utilities to ensure static files are correctly served.
"""
from flask import Flask, url_for
import os

def configure_static_files(app: Flask):
    """
    Configure static files for PythonAnywhere deployment.
    
    This function properly configures static files handling for PythonAnywhere
    to ensure CSS and image files load correctly in production.
    
    Args:
        app: The Flask application instance
    """
    # Check if we're running on PythonAnywhere
    is_pythonanywhere = 'PYTHONANYWHERE_SITE' in os.environ
    
    if is_pythonanywhere:
        # Get PythonAnywhere domain from environment
        pa_domain = os.environ.get('PYTHONANYWHERE_DOMAIN')
        
        if pa_domain:
            # Set the SERVER_NAME for url_for to work correctly with _external=True
            app.config['SERVER_NAME'] = pa_domain
            app.config['PREFERRED_URL_SCHEME'] = 'https'
            
            # Configure application root path if running in a subdomain
            app.config['APPLICATION_ROOT'] = '/'
            
            app.logger.info(f"Configured static files for PythonAnywhere domain: {pa_domain}")
        else:
            app.logger.warning("PYTHONANYWHERE_DOMAIN not set in environment variables")
            
        # Make sure static files are properly cached to improve performance
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year in seconds
    
    # Ensure static directory exists
    static_dir = os.path.join(app.root_path, 'static')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir, exist_ok=True)
        app.logger.info(f"Created static directory: {static_dir}")
        
    # Ensure CSS directory exists
    css_dir = os.path.join(static_dir, 'css')
    if not os.path.exists(css_dir):
        os.makedirs(css_dir, exist_ok=True)
        app.logger.info(f"Created CSS directory: {css_dir}")
        
    # Ensure images directory exists
    images_dir = os.path.join(static_dir, 'images')
    if not os.path.exists(images_dir):
        os.makedirs(images_dir, exist_ok=True)
        app.logger.info(f"Created images directory: {images_dir}")
        
    # Add context processor to provide static URL helpers
    @app.context_processor
    def static_url_processor():
        """Add static URL helpers to template context"""
        def get_static_url(filename):
            """Get absolute URL for static file"""
            return url_for('static', filename=filename, _external=True)
            
        return dict(get_static_url=get_static_url) 