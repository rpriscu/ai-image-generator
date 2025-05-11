"""
Simple script to create database tables directly without any checks.
"""
import os
import sys
import importlib.util
import psycopg2
from urllib.parse import urlparse

# Apply PostgreSQL dialect fix for Python 3.13 before importing SQLAlchemy
if sys.version_info.major == 3 and sys.version_info.minor == 13:
    try:
        print("Applying PostgreSQL dialect fix for Python 3.13...")
        from app.utils.db_fix import apply_postgres_dialect_fix
        apply_postgres_dialect_fix()
        print("Successfully applied PostgreSQL dialect fix")
    except Exception as e:
        print(f"Error applying PostgreSQL dialect fix: {e}")

print("Importing Flask app and database models...")
try:
    from sqlalchemy import create_engine, text, inspect
    from app import create_app
    from app.models.models import db
    print("Successfully imported Flask app and database models")
except Exception as e:
    print(f"Error importing Flask app and models: {e}")
    sys.exit(1)

def create_tables():
    """
    Create database tables directly without any checks.
    """
    print("Creating Flask application...")
    app = create_app()
    print("Flask application created")
    
    # Get database URL and format it properly
    db_url = app.config['SQLALCHEMY_DATABASE_URI']
    if not db_url:
        print("Error: No database URL configured")
        return False
    
    # Print masked URL for log
    masked_url = db_url
    if '@' in db_url:
        credentials_part = db_url.split('@')[0]
        if ':' in credentials_part:
            username_part = credentials_part.split(':')[0]
            masked_url = f"{username_part}:****@{db_url.split('@')[1]}"
    print(f"Using database: {masked_url}")
    
    # Create database connection
    print("Creating database connection...")
    try:
        # Get database connection details from URL
        url = urlparse(db_url)
        db_name = url.path[1:]
        username = url.username
        password = url.password
        hostname = url.hostname
        port = url.port
        
        # Connect directly with psycopg2 to verify connection
        conn = psycopg2.connect(
            dbname=db_name,
            user=username,
            password=password,
            host=hostname,
            port=port
        )
        conn.close()
        print("Successfully connected to database with psycopg2")
    except Exception as e:
        print(f"Error connecting to database with psycopg2: {e}")
        return False
    
    # Create tables with SQLAlchemy
    print("Creating tables with SQLAlchemy...")
    with app.app_context():
        try:
            # Display existing tables
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            print(f"Existing tables before creation: {existing_tables}")
            
            # Create all tables
            db.create_all()
            print("Tables created successfully")
            
            # Verify tables were created
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Tables after creation: {tables}")
            
            # Check if specific tables exist
            print("Verifying specific tables:")
            for table in ['user', 'admin', 'monthly_usage', 'image']:
                exists = table in tables
                print(f"  - {table}: {'EXISTS' if exists else 'MISSING'}")
            
            return True
        except Exception as e:
            print(f"Error creating tables: {e}")
            return False

if __name__ == "__main__":
    print("=" * 80)
    print("DIRECT TABLE CREATION")
    print("=" * 80)
    
    success = create_tables()
    if success:
        print("Database tables created successfully!")
    else:
        print("Failed to create database tables")
    
    print("=" * 80)
    print("Script execution complete")
    print("=" * 80) 