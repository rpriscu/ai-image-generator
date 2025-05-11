"""
Database Verification Script

This script performs a comprehensive check of the database configuration,
connections, and table schema to verify everything is set up correctly.
"""
import os
import sys
import time
from urllib.parse import urlparse

print("=" * 80)
print("DATABASE VERIFICATION SCRIPT")
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

# Try to import SQLAlchemy and psycopg2
print("\nVerifying database libraries...")
try:
    import sqlalchemy
    print(f"✓ SQLAlchemy version: {sqlalchemy.__version__}")
except ImportError:
    print("❌ Could not import SQLAlchemy. Make sure it's installed.")
    sys.exit(1)

try:
    import psycopg2
    print(f"✓ psycopg2 version: {psycopg2.__version__}")
except ImportError:
    print("❌ Could not import psycopg2. Make sure it's installed.")
    sys.exit(1)

# Get database URL
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    print("❌ No DATABASE_URL environment variable found")
    sys.exit(1)

# Fix database URL if needed
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
    print("✓ Fixed database URL format (postgres:// -> postgresql://)")

# Mask sensitive parts for display
parsed_url = urlparse(db_url)
safe_url = f"{parsed_url.scheme}://{parsed_url.netloc.split('@')[0].split(':')[0]}:****@{parsed_url.netloc.split('@')[-1]}{parsed_url.path}"
print(f"Database URL: {safe_url}")

# Test direct connection with psycopg2
print("\nTesting connection with psycopg2...")
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
    
    print(f"✓ psycopg2 connection successful ({end_time - start_time:.2f}s)")
    print(f"PostgreSQL server version: {version[0]}")
except Exception as e:
    print(f"❌ psycopg2 connection error: {e}")
    print("Database connection test failed!")
    sys.exit(1)

# Import our app and models
print("\nImporting Flask app and models...")
try:
    from app import create_app
    from app.models.models import db, Admin, User, MonthlyUsage, Asset
    print("✓ Successfully imported Flask app and models")
except Exception as e:
    print(f"❌ Error importing app or models: {e}")
    sys.exit(1)

# Create app instance and verify tables
print("\nVerifying database tables...")
app = create_app()
app.config['SKIP_ADMIN_CREATION'] = True

with app.app_context():
    try:
        # Check connection through SQLAlchemy
        start_time = time.time()
        engine = db.engine
        connection = engine.connect()
        result = connection.execute(sqlalchemy.text("SELECT 1"))
        connection.close()
        end_time = time.time()
        print(f"✓ SQLAlchemy connection successful ({end_time - start_time:.2f}s)")
        
        # Check tables
        inspector = sqlalchemy.inspect(engine)
        tables = inspector.get_table_names()
        print(f"Found {len(tables)} tables: {', '.join(tables)}")
        
        # Check required tables
        required_tables = ['user', 'admin', 'monthly_usage', 'asset']
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            print(f"❌ Missing required tables: {', '.join(missing_tables)}")
            
            # Offer to create missing tables
            print("\nAttempting to create missing tables...")
            db.create_all()
            print("Tables created. Verifying again...")
            
            # Check again
            inspector = sqlalchemy.inspect(engine)
            tables = inspector.get_table_names()
            print(f"Found {len(tables)} tables after creation: {', '.join(tables)}")
            
            # Check required tables again
            missing_tables = [table for table in required_tables if table not in tables]
            if missing_tables:
                print(f"❌ Still missing tables: {', '.join(missing_tables)}")
            else:
                print("✓ All required tables now exist")
        else:
            print("✓ All required tables exist")
        
        # Check for admin user
        try:
            admin_count = Admin.query.count()
            print(f"Found {admin_count} admin users")
            
            if admin_count == 0:
                print("❌ No admin users found. You should create one with setup_db.py --create-admin")
            else:
                print("✓ Admin user(s) exist")
        except Exception as e:
            print(f"❌ Error checking admin users: {e}")
        
    except Exception as e:
        print(f"❌ Error verifying database: {e}")
        sys.exit(1)

print("\n" + "=" * 80)
print("DATABASE VERIFICATION COMPLETE")
print("=" * 80)
print("✓ Database connection is working")
if 'missing_tables' in locals() and not missing_tables:
    print("✓ All required tables exist")
else:
    print("❌ Some required tables are missing")
if 'admin_count' in locals() and admin_count > 0:
    print("✓ Admin user exists")
else:
    print("❌ No admin user found")
print("=" * 80) 