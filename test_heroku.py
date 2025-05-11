#!/usr/bin/env python
"""
Heroku PostgreSQL Test Script

This script performs a series of diagnostics to verify:
1. Python environment and version
2. Availability of required modules
3. PostgreSQL connection
4. SQLAlchemy dialect registration

Run this script directly on Heroku with:
    heroku run python test_heroku.py
"""
import os
import sys
import time
import importlib.util
from urllib.parse import urlparse
import subprocess

def print_separator(title=None):
    """Print a separator line with an optional title"""
    if title:
        print("\n" + "=" * 20 + f" {title} " + "=" * 20)
    else:
        print("\n" + "=" * 60)

def check_python_environment():
    """Check Python version and environment"""
    print_separator("PYTHON ENVIRONMENT")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Running on Heroku: {'Yes' if 'DYNO' in os.environ else 'No'}")
    print(f"Environment variables: {len(os.environ)} variables set")

def check_modules():
    """Check for required modules"""
    print_separator("MODULE CHECK")
    modules = [
        'psycopg2', 'sqlalchemy', 'flask', 'flask_sqlalchemy', 
        'sqlalchemy.dialects.postgresql', 'gunicorn'
    ]
    
    for module_name in modules:
        try:
            module = importlib.import_module(module_name)
            version = getattr(module, '__version__', 'unknown')
            print(f"✓ {module_name}: Found (version: {version})")
            
            # For SQLAlchemy, check dialect registry
            if module_name == 'sqlalchemy':
                from sqlalchemy.dialects import registry
                print(f"  SQLAlchemy dialect registry contains {len(registry._registry)} entries")
                for dialect in ['postgresql', 'postgres']:
                    if dialect in registry._registry:
                        print(f"  - {dialect}: {', '.join(registry._registry[dialect].keys())}")
        except ImportError as e:
            print(f"✗ {module_name}: Not found - {e}")
            
            # Try alternate import for postgresql dialect
            if module_name == 'sqlalchemy.dialects.postgresql':
                try:
                    from sqlalchemy.dialects import postgresql
                    print(f"  ✓ Alternate import for {module_name} successful")
                except ImportError as e2:
                    print(f"  ✗ Alternate import also failed: {e2}")

def check_psycopg2():
    """Perform specific checks for psycopg2"""
    print_separator("PSYCOPG2 CHECK")
    try:
        import psycopg2
        print(f"psycopg2 version: {psycopg2.__version__}")
        print(f"psycopg2 path: {psycopg2.__file__}")
        
        # Check if it's binary or source distribution
        if 'psycopg2_binary' in psycopg2.__file__:
            print("Using psycopg2-binary package")
        else:
            print("Using standard psycopg2 package")
    except ImportError as e:
        print(f"Failed to import psycopg2: {e}")
        # Try to install it
        print("Attempting to install psycopg2-binary...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psycopg2-binary==2.9.9'])
            print("Installation successful, trying import again")
            import psycopg2
            print(f"psycopg2 version (after install): {psycopg2.__version__}")
        except Exception as e2:
            print(f"Installation failed: {e2}")

def fix_postgres_url(url):
    """Fix postgres:// URLs to be postgresql:// for SQLAlchemy 1.4+"""
    if url and url.startswith('postgres://'):
        return url.replace('postgres://', 'postgresql://', 1)
    return url

def check_database_url():
    """Check if DATABASE_URL is properly set"""
    print_separator("DATABASE URL")
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        print("❌ DATABASE_URL environment variable not found")
        print("This is required for PostgreSQL connections")
        return None
    
    # Fix URL if needed
    fixed_url = fix_postgres_url(db_url)
    if fixed_url != db_url:
        print("⚠️ Fixed DATABASE_URL format (postgres:// → postgresql://)")
    
    # Don't print full URL with credentials
    parsed = urlparse(fixed_url)
    masked_url = f"{parsed.scheme}://{parsed.netloc.split('@')[-1]}{parsed.path}"
    print(f"Database URL: {masked_url}")
    
    return fixed_url

def test_direct_connection(db_url):
    """Test direct connection with psycopg2"""
    print_separator("DIRECT CONNECTION TEST")
    if not db_url:
        print("Skipping direct connection test - no DATABASE_URL")
        return False
    
    try:
        import psycopg2
        parsed = urlparse(db_url)
        params = {
            'dbname': parsed.path[1:],
            'user': parsed.username,
            'password': parsed.password,
            'host': parsed.hostname,
            'port': parsed.port or 5432
        }
        
        print(f"Connecting to PostgreSQL at {params['host']}:{params['port']}...")
        start_time = time.time()
        conn = psycopg2.connect(**params)
        end_time = time.time()
        
        cursor = conn.cursor()
        cursor.execute('SELECT version();')
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        print(f"✓ Connected successfully in {end_time - start_time:.2f} seconds")
        print(f"PostgreSQL version: {version}")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_sqlalchemy_connection(db_url):
    """Test connection with SQLAlchemy"""
    print_separator("SQLALCHEMY CONNECTION TEST")
    if not db_url:
        print("Skipping SQLAlchemy connection test - no DATABASE_URL")
        return False
    
    try:
        from sqlalchemy import create_engine, text
        print(f"Creating SQLAlchemy engine...")
        
        # Register PostgreSQL dialects first
        try:
            from app.utils.db_fix import apply_postgres_dialect_fix
            apply_postgres_dialect_fix()
            print("Applied PostgreSQL dialect fix")
        except ImportError:
            print("Could not import db_fix module - continuing without it")
        
        start_time = time.time()
        engine = create_engine(db_url)
        print(f"Engine created with dialect: {engine.dialect.name}")
        
        with engine.connect() as connection:
            print("Connection established, executing query...")
            result = connection.execute(text("SELECT version();"))
            version = result.fetchone()[0]
        end_time = time.time()
        
        print(f"✓ Connected successfully in {end_time - start_time:.2f} seconds")
        print(f"PostgreSQL version: {version}")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

def get_flask_app_config():
    """Try to get Flask app configuration"""
    print_separator("FLASK APP CONFIG")
    try:
        from run import create_app
        app = create_app()
        print(f"SQLAlchemy database URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
        print(f"SQLAlchemy engine options: {app.config.get('SQLALCHEMY_ENGINE_OPTIONS')}")
        return True
    except Exception as e:
        print(f"Could not load Flask app config: {e}")
        return False

def main():
    """Main function to run all tests"""
    print("\n" + "=" * 60)
    print("HEROKU POSTGRESQL DIAGNOSTIC TOOL")
    print("=" * 60)
    
    # Run all diagnostic checks
    check_python_environment()
    check_modules()
    check_psycopg2()
    db_url = check_database_url()
    
    direct_ok = test_direct_connection(db_url)
    sqlalchemy_ok = test_sqlalchemy_connection(db_url)
    flask_ok = get_flask_app_config()
    
    # Print summary
    print_separator("SUMMARY")
    print(f"Python 3.13 Compatibility: {'✓' if sys.version_info.major == 3 and sys.version_info.minor == 13 else '❌'}")
    print(f"Required modules: {'✓' if check_modules else '❌'}")
    print(f"Database URL configured: {'✓' if db_url else '❌'}")
    print(f"Direct psycopg2 connection: {'✓' if direct_ok else '❌'}")
    print(f"SQLAlchemy connection: {'✓' if sqlalchemy_ok else '❌'}")
    print(f"Flask configuration: {'✓' if flask_ok else '❌'}")
    
    print("\nDiagnostic complete. Use this information to troubleshoot PostgreSQL connectivity issues.")

if __name__ == '__main__':
    main() 