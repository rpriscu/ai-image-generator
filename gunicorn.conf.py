"""
Gunicorn configuration file for AI Image Generator.
Used for production deployment.
"""
import os
import multiprocessing

# Server socket settings
bind = f"0.0.0.0:{os.environ.get('PORT', '8080')}"

# Worker settings
# For Heroku, we default to 2 workers but can be overridden by WEB_CONCURRENCY
workers = int(os.environ.get('WEB_CONCURRENCY', 2))
worker_class = 'gthread'
threads = int(os.environ.get('GUNICORN_THREADS', 2))
worker_tmp_dir = '/tmp'  # Required for Heroku

# Process naming
proc_name = 'ai-image-generator'

# Logging settings
loglevel = 'info'
accesslog = '-'  # Log to stdout
errorlog = '-'   # Log to stderr

# Security settings
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Server mechanics
timeout = 30
keepalive = 2

# Automatic reload on code changes (only for development)
reload = os.environ.get('FLASK_ENV', 'production') == 'development' 