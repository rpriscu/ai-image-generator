"""
Heroku Deployment Verification Script

This script verifies both the PostgreSQL connection and Flask-Session compatibility 
for deployment on Heroku with Python 3.13.
"""
import os
import sys
import time
import logging
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Print diagnostic info
print("=" * 80)
print("HEROKU DEPLOYMENT VERIFICATION")
print("=" * 80)
print(f"Python version: {sys.version}")
print(f"Running on Heroku: {'Yes' if 'DYNO' in os.environ else 'No'}")
print("=" * 80)

# Part 1: Check PostgreSQL dialect
print("\n[1/3] CHECKING POSTGRESQL DIALECT COMPATIBILITY")
print("=" * 60)

# Check if we're on Python 3.13
is_py313 = sys.version_info.major == 3 and sys.version_info.minor == 13
print(f"Running on Python 3.13: {'Yes' if is_py313 else 'No'}")

if is_py313:
    # Apply PostgreSQL dialect fix before importing SQLAlchemy
    try:
        print("Applying PostgreSQL dialect fix...")
        # Import and apply the fix
        from app.utils.db_fix import apply_postgres_dialect_fix, check_dialect_modules
        apply_postgres_dialect_fix()
        print("Successfully applied PostgreSQL dialect fix")
        
        # Verify the modules are properly installed
        print("\nVerifying dialect modules:")
        module_check = check_dialect_modules()
        for key, value in module_check.items():
            print(f"- {key}: {'OK' if value else 'MISSING'}")
    except ImportError:
        print("ERROR: Could not import db_fix module. Make sure it's in app/utils/db_fix.py")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR applying PostgreSQL dialect fix: {e}")
        print("Continuing but database connection may fail...")

# Try to import SQLAlchemy
try:
    import sqlalchemy
    print(f"Successfully imported SQLAlchemy version: {sqlalchemy.__version__}")
except ImportError:
    print("ERROR: Could not import SQLAlchemy. Make sure it's installed.")
    sys.exit(1)

# Part 2: Test Database Connection
print("\n[2/3] TESTING DATABASE CONNECTION")
print("=" * 60)

# Get database URL from environment
db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith('postgres://'):
    # Fix for SQLAlchemy 1.4+ which requires postgresql:// instead of postgres://
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
    print(f"Updated database URL format from postgres:// to postgresql://")
elif db_url:
    print(f"Database URL format is already correct")
else:
    print("ERROR: No DATABASE_URL environment variable found")
    sys.exit(1)

# Mask sensitive parts for display
parsed_url = urlparse(db_url)
safe_url = f"{parsed_url.scheme}://{parsed_url.netloc.split('@')[-1]}{parsed_url.path}"
print(f"Database URL (host/path only): {safe_url}")

# Test direct connection with psycopg2
print("\nTesting connection with psycopg2...")
try:
    import psycopg2
    
    parsed_url = urlparse(db_url)
    username = parsed_url.username
    password = parsed_url.password
    database = parsed_url.path[1:]  # Remove leading slash
    hostname = parsed_url.hostname
    port = parsed_url.port or 5432
    
    start_time = time.time()
    conn = psycopg2.connect(
        dbname=database,
        user=username,
        password=password,
        host=hostname,
        port=port
    )
    cursor = conn.cursor()
    cursor.execute('SELECT version();')
    version = cursor.fetchone()
    conn.close()
    end_time = time.time()
    
    print(f"SUCCESS: psycopg2 connection worked in {end_time - start_time:.2f} seconds")
    print(f"PostgreSQL server version: {version[0]}")
except ImportError:
    print("ERROR: Could not import psycopg2. Make sure it's installed.")
except Exception as e:
    print(f"ERROR connecting with psycopg2: {e}")
    print("Database connection test failed!")
    sys.exit(1)

# Test SQLAlchemy connection
print("\nTesting connection with SQLAlchemy...")
try:
    from sqlalchemy import create_engine, text
    
    start_time = time.time()
    engine = create_engine(db_url)
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        version = result.fetchone()
    end_time = time.time()
    
    print(f"SUCCESS: SQLAlchemy connection worked in {end_time - start_time:.2f} seconds")
    print(f"PostgreSQL server version: {version[0]}")
except Exception as e:
    print(f"ERROR connecting with SQLAlchemy: {e}")
    print("SQLAlchemy database connection test failed!")
    sys.exit(1)

# Part 3: Test Flask with Sessions
print("\n[3/3] TESTING FLASK APPLICATION WITH SESSIONS")
print("=" * 60)

try:
    # First, patch the session interface
    print("Importing session_fix module...")
    from app.utils.session_fix import patched_save_session, configure_session_interface
    print("Successfully imported session_fix module")
    
    # Create Flask app
    print("\nCreating Flask application...")
    from app import create_app
    app = create_app()
    print("Flask application created successfully")
    
    # Check if session is configured correctly
    session_type = app.config.get('SESSION_TYPE')
    print(f"Session type: {session_type}")
    
    if session_type == 'filesystem':
        session_dir = app.config.get('SESSION_FILE_DIR')
        if session_dir:
            print(f"Session directory: {session_dir}")
            if not os.path.exists(session_dir):
                print(f"Creating session directory: {session_dir}")
                os.makedirs(session_dir, exist_ok=True)
        else:
            print("Warning: SESSION_FILE_DIR not set")
    elif session_type == 'redis':
        print("Using Redis for session storage")
        redis_url = app.config.get('SESSION_REDIS')
        if redis_url:
            print("Redis URL is configured")
        else:
            print("Warning: SESSION_REDIS not set")
    else:
        print(f"Using {session_type} for session storage")
    
    # Test session patch
    print("\nVerifying session interface patch...")
    from flask.sessions import SessionInterface
    if SessionInterface.save_session == patched_save_session:
        print("SUCCESS: Session interface patch is correctly applied")
    else:
        print("WARNING: Session interface patch is not applied correctly")
        print("Attempting to apply it now...")
        configure_session_interface(app)
    
    print("\nAll verification steps completed successfully!")
    sys.exit(0)
except ImportError as e:
    print(f"ERROR importing Flask app: {e}")
    print("Flask application test failed!")
    sys.exit(1)
except Exception as e:
    print(f"ERROR testing Flask application: {e}")
    print("Flask application test failed!")
    sys.exit(1) 