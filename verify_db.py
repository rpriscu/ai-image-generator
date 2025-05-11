"""
Database Connection Verification Script

This script verifies that the application can connect to the PostgreSQL database.
It's helpful for debugging connection issues on Heroku.
"""
import os
import sys
import importlib.util
from urllib.parse import urlparse
import time

# Try to import psycopg2
try:
    import psycopg2
    print(f"Successfully imported psycopg2 version: {psycopg2.__version__}")
except ImportError:
    print("ERROR: Could not import psycopg2. Make sure it's installed.")
    sys.exit(1)

# Try to import SQLAlchemy
try:
    import sqlalchemy
    print(f"Successfully imported SQLAlchemy version: {sqlalchemy.__version__}")
except ImportError:
    print("ERROR: Could not import SQLAlchemy. Make sure it's installed.")
    sys.exit(1)

# Try to import the PostgreSQL dialect
try:
    from sqlalchemy.dialects import postgresql
    print("Successfully imported PostgreSQL dialect from SQLAlchemy")
except ImportError:
    print("ERROR: Could not import PostgreSQL dialect from SQLAlchemy.")
    sys.exit(1)

def check_postgres_module_path():
    """Check the path of the PostgreSQL dialect module"""
    try:
        if importlib.util.find_spec("sqlalchemy.dialects.postgresql"):
            path = importlib.util.find_spec("sqlalchemy.dialects.postgresql").origin
            print(f"PostgreSQL dialect located at: {path}")
            return True
        else:
            print("ERROR: Could not locate sqlalchemy.dialects.postgresql module")
            return False
    except Exception as e:
        print(f"Error checking PostgreSQL module path: {e}")
        return False

def get_database_url():
    """Get the database URL from environment or use a default"""
    # Get from DATABASE_URL environment variable (Heroku sets this)
    db_url = os.environ.get('DATABASE_URL')
    
    if db_url and db_url.startswith('postgres://'):
        # Fix for SQLAlchemy 1.4+ which requires postgresql:// instead of postgres://
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
        print(f"Using PostgreSQL connection URL from environment (replaced 'postgres://' with 'postgresql://')")
    elif db_url:
        print(f"Using database connection URL from environment")
    else:
        print("ERROR: No DATABASE_URL environment variable found")
        return None
    
    # Don't print the full URL as it contains credentials
    parsed_url = urlparse(db_url)
    safe_url = f"{parsed_url.scheme}://{parsed_url.netloc.split('@')[-1]}{parsed_url.path}"
    print(f"Database URL (host/path only): {safe_url}")
    
    return db_url

def test_database_connection(db_url):
    """Test connection to the database"""
    if not db_url:
        return False
    
    print("\nTesting direct connection with psycopg2...")
    try:
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
        
        print(f"Successfully connected using psycopg2 in {end_time - start_time:.2f} seconds")
        print(f"PostgreSQL server version: {version[0]}")
        return True
    except Exception as e:
        print(f"Error connecting with psycopg2: {e}")
        return False

def test_sqlalchemy_connection(db_url):
    """Test connection using SQLAlchemy"""
    if not db_url:
        return False
        
    print("\nTesting connection with SQLAlchemy...")
    try:
        from sqlalchemy import create_engine, text
        
        start_time = time.time()
        engine = create_engine(db_url)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            version = result.fetchone()
        end_time = time.time()
        
        print(f"Successfully connected using SQLAlchemy in {end_time - start_time:.2f} seconds")
        print(f"PostgreSQL server version: {version[0]}")
        return True
    except Exception as e:
        print(f"Error connecting with SQLAlchemy: {e}")
        return False

def main():
    """Main function to run all checks"""
    print("=" * 50)
    print("DATABASE CONNECTION VERIFICATION")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print(f"Running on Heroku: {'Yes' if 'DYNO' in os.environ else 'No'}")
    print("=" * 50)
    
    # Check if PostgreSQL dialect module exists
    dialect_ok = check_postgres_module_path()
    if not dialect_ok:
        print("WARNING: PostgreSQL dialect module not found properly")
    
    # Get database URL
    db_url = get_database_url()
    if not db_url:
        print("ERROR: Could not get database URL")
        sys.exit(1)
    
    # Test connections
    psycopg2_ok = test_database_connection(db_url)
    sqlalchemy_ok = test_sqlalchemy_connection(db_url)
    
    # Summary
    print("\n" + "=" * 50)
    print("VERIFICATION SUMMARY")
    print("=" * 50)
    print(f"PostgreSQL dialect module: {'OK' if dialect_ok else 'FAILED'}")
    print(f"Direct psycopg2 connection: {'OK' if psycopg2_ok else 'FAILED'}")
    print(f"SQLAlchemy connection: {'OK' if sqlalchemy_ok else 'FAILED'}")
    print("=" * 50)
    
    if dialect_ok and psycopg2_ok and sqlalchemy_ok:
        print("All database connection checks passed!")
        sys.exit(0)
    else:
        print("Some database connection checks failed. Review the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 