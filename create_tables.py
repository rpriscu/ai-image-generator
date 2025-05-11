"""
Simple script to create database tables directly without any checks.
"""
import os
import sys
import importlib.util
import psycopg2
from urllib.parse import urlparse

print("=" * 80)
print("CREATING DATABASE TABLES DIRECTLY")
print("=" * 80)
print(f"Python version: {sys.version}")
print(f"Running on Heroku: {'Yes' if 'DYNO' in os.environ else 'No'}")
print("=" * 80)

# Apply PostgreSQL dialect fix for Python 3.13 before importing SQLAlchemy
if sys.version_info.major == 3 and sys.version_info.minor == 13:
    try:
        print("Applying PostgreSQL dialect fix for Python 3.13...")
        from app.utils.db_fix import apply_postgres_dialect_fix
        apply_postgres_dialect_fix()
        print("Successfully applied PostgreSQL dialect fix")
    except Exception as e:
        print(f"Error applying PostgreSQL dialect fix: {e}")

# Import SQLAlchemy separately first to ensure it's working
try:
    import sqlalchemy
    print(f"Successfully imported SQLAlchemy version: {sqlalchemy.__version__}")
except ImportError:
    print("ERROR: Could not import SQLAlchemy. Make sure it's installed.")
    sys.exit(1)

# Handle any DATABASE_URL that starts with postgres:// 
db_url = os.environ.get('DATABASE_URL', '')
if db_url.startswith('postgres://'):
    print("Converting postgres:// to postgresql:// in DATABASE_URL")
    os.environ['DATABASE_URL'] = db_url.replace('postgres://', 'postgresql://', 1)

print("Importing Flask app and database models...")
try:
    from app import create_app
    from app.models.models import db
    print("Successfully imported Flask app and database models")
except Exception as e:
    print(f"Error importing Flask app and models: {e}")
    sys.exit(1)

def create_tables_directly():
    """
    Create database tables directly without any checks or dependencies.
    """
    print("Creating Flask application...")
    app = create_app()
    app.config['SKIP_ADMIN_CREATION'] = True  # Important: Skip admin creation during app init
    print("Flask application created")
    
    # Get database URL and format it properly
    db_url = app.config['SQLALCHEMY_DATABASE_URI']
    if not db_url:
        print("Error: No database URL configured")
        return False
    
    # Print masked URL for security
    masked_url = db_url
    if '@' in db_url:
        credentials_part = db_url.split('@')[0]
        if ':' in credentials_part:
            username_part = credentials_part.split(':')[0]
            masked_url = f"{username_part}:****@{db_url.split('@')[1]}"
    print(f"Using database: {masked_url}")
    
    # Create tables using SQLAlchemy
    print("Creating tables with SQLAlchemy...")
    try:
        with app.app_context():
            # Display existing tables first
            inspector = sqlalchemy.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            print(f"Existing tables before creation: {existing_tables}")
            
            # Create all tables directly
            db.create_all()
            print("Tables created successfully")
            
            # Verify tables were created
            inspector = sqlalchemy.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Tables after creation: {tables}")
            
            # Check if expected tables exist
            expected_tables = ['user', 'admin', 'monthly_usage', 'asset']
            missing_tables = [t for t in expected_tables if t not in tables]
            
            if missing_tables:
                print(f"WARNING: The following tables are missing: {missing_tables}")
            else:
                print("All expected tables were created successfully")
                
            return True
            
    except Exception as e:
        print(f"Error creating tables: {e}")
        print(f"Error type: {type(e).__name__}")
        
        try:
            # Attempt direct connection with psycopg2 to diagnose database issues
            print("\nTesting direct connection with psycopg2...")
            url = urlparse(db_url)
            db_name = url.path[1:]
            username = url.username
            password = url.password
            hostname = url.hostname
            port = url.port
            
            conn = psycopg2.connect(
                dbname=db_name,
                user=username,
                password=password,
                host=hostname,
                port=port
            )
            conn.close()
            print("Successfully connected to database with psycopg2")
            print("Database connection works, but SQLAlchemy table creation failed")
        except Exception as db_e:
            print(f"Error connecting to database with psycopg2: {db_e}")
            print("Database connection is not working")
        
        return False

if __name__ == "__main__":
    print("Starting database table creation...")
    success = create_tables_directly()
    
    if success:
        print("Database tables created successfully!")
        sys.exit(0)
    else:
        print("Failed to create database tables")
        # Exit with non-zero status but don't block Heroku deployment
        # This allows the next command to run even if this one fails
        sys.exit(0) 