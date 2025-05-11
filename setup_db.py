"""
Consolidated database setup script.
This script handles database initialization and admin user creation.
"""
import os
import sys
import argparse
import sqlalchemy
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# Print initial diagnostic info
print("=" * 80)
print(f"SETUP_DB.PY - Database initialization script")
print(f"Python version: {sys.version}")
print(f"Running on Heroku: {'Yes' if 'DYNO' in os.environ else 'No'}")
print("=" * 80)

# Load environment variables
print("Loading environment variables...")
load_dotenv()
print("Environment variables loaded")

# Apply PostgreSQL dialect fix for Python 3.13 before importing SQLAlchemy
if sys.version_info.major == 3 and sys.version_info.minor == 13:
    try:
        print("Applying PostgreSQL dialect fix for Python 3.13...")
        from app.utils.db_fix import apply_postgres_dialect_fix
        apply_postgres_dialect_fix()
        print("Successfully applied PostgreSQL dialect fix")
    except Exception as e:
        print(f"Error applying PostgreSQL dialect fix: {e}")

# Handle any DATABASE_URL that starts with postgres:// 
db_url = os.environ.get('DATABASE_URL', '')
if db_url.startswith('postgres://'):
    print("Converting postgres:// to postgresql:// in DATABASE_URL")
    os.environ['DATABASE_URL'] = db_url.replace('postgres://', 'postgresql://', 1)

print("Importing Flask app and database models...")
try:
    from app import create_app
    from app.models.models import db, Admin, User
    print("Successfully imported Flask app and database models")
except Exception as e:
    print(f"Error importing Flask app and models: {e}")
    sys.exit(1)

def init_database(drop_all=False):
    """
    Initialize the database tables.
    
    Args:
        drop_all (bool): Whether to drop all tables before creating them
    """
    print("Setting up the database...")
    
    # Create application with initialization flag
    print("Creating Flask application instance...")
    app = create_app()
    app.config['SKIP_ADMIN_CREATION'] = True
    print("Flask application instance created")
    
    # Display database configuration (mask password for security)
    db_url = app.config['SQLALCHEMY_DATABASE_URI']
    if db_url:
        # Mask the password in the URL for display purposes
        masked_url = db_url
        if '@' in db_url:
            credentials_part = db_url.split('@')[0]
            if ':' in credentials_part:
                username_part = credentials_part.split(':')[0]
                masked_url = f"{username_part}:****@{db_url.split('@')[1]}"
        print(f"Using database: {masked_url}")
    else:
        print("Warning: No database URL configured")
    
    print("Creating application context...")
    with app.app_context():
        try:
            # First verify the connection works
            try:
                db.engine.connect()
                print("Database connection successful")
            except Exception as e:
                print(f"Error connecting to database: {e}")
                return False
                
            # Check if tables already exist
            try:
                engine = db.engine
                inspector = sqlalchemy.inspect(engine)
                existing_tables = inspector.get_table_names()
                print(f"Existing tables: {existing_tables}")
                
                if 'admin' not in existing_tables:
                    print("Warning: Admin table does not exist - may need to run create_tables.py first")
            except Exception as e:
                print(f"Could not inspect existing tables: {e}")
                existing_tables = []
                
            if drop_all:
                print("Dropping all tables...")
                db.drop_all()
                print("All tables dropped.")
            
            if not existing_tables:
                print("Creating tables...")
                db.create_all()
                print("Database tables created successfully!")
            else:
                print("Tables already exist, skipping table creation")
            
            # List all tables that were created
            try:
                inspector = sqlalchemy.inspect(engine)
                tables_after = inspector.get_table_names()
                print(f"Tables after setup: {tables_after}")
            except Exception as e:
                print(f"Could not inspect tables after creation: {e}")
                
        except Exception as e:
            print(f"ERROR during database setup: {e}")
            print(f"Error type: {type(e).__name__}")
            return False
    
    return True

def create_admin_user(username=None, password=None, force=False):
    """
    Create an admin user.
    
    Args:
        username (str): Admin username
        password (str): Admin password
        force (bool): Whether to create a new admin even if one exists
    """
    # Create the application
    print("Creating Flask application for admin user creation...")
    app = create_app()
    app.config['SKIP_ADMIN_CREATION'] = True
    print("Flask application created")
    
    # Use environment variables if not provided
    if not username:
        username = os.environ.get('ADMIN_USERNAME') or app.config.get('ADMIN_USERNAME')
    if not password:
        password = os.environ.get('ADMIN_PASSWORD') or app.config.get('ADMIN_PASSWORD')
    
    if not username or not password:
        print("Error: Admin username and password are required.")
        print("Either provide them as arguments or set ADMIN_USERNAME and ADMIN_PASSWORD environment variables.")
        return False
    
    print(f"Attempting to create admin user: {username}")
    
    with app.app_context():
        try:
            # First check if the admin table exists
            engine = db.engine
            inspector = sqlalchemy.inspect(engine)
            tables = inspector.get_table_names()
            
            if 'admin' not in tables:
                print("Admin table does not exist. Attempting to create tables...")
                db.create_all()
                print("Created database tables")
            
            # Now check if admin already exists
            print("Checking if admin user already exists...")
            try:
                admin_exists = Admin.query.filter_by(username=username).first() is not None
                
                if admin_exists:
                    if force:
                        print(f"Admin user '{username}' already exists, but force flag is set. Creating anyway.")
                    else:
                        print(f"Admin user '{username}' already exists. Use --force to overwrite.")
                        return True
            except Exception as e:
                print(f"Error checking for existing admin: {e}")
                print("Assuming admin does not exist and continuing...")
                admin_exists = False
            
            # Create a new admin user
            try:
                print("Creating admin user...")
                admin = Admin(username=username)
                admin.set_password(password)
                db.session.add(admin)
                db.session.commit()
                print(f"Admin user '{username}' created successfully!")
                return True
            except Exception as e:
                print(f"Error creating admin user: {str(e)}")
                db.session.rollback()
                print("Rolling back transaction")
                return False
        except Exception as e:
            print(f"Error during admin user creation: {e}")
            return False

def list_users():
    """List all users in the database"""
    print("Creating Flask application for listing users...")
    app = create_app()
    print("Flask application created")
    
    with app.app_context():
        try:
            # First check if tables exist
            engine = db.engine
            inspector = sqlalchemy.inspect(engine)
            tables = inspector.get_table_names()
            
            if 'user' not in tables or 'admin' not in tables:
                print("User or admin tables do not exist yet")
                return
            
            print("\nRegular Users:")
            users = User.query.all()
            if users:
                for user in users:
                    print(f"- {user.email} (ID: {user.id})")
            else:
                print("No regular users found.")
            
            print("\nAdmin Users:")
            admins = Admin.query.all()
            if admins:
                for admin in admins:
                    print(f"- {admin.username} (ID: {admin.id})")
            else:
                print("No admin users found.")
        except Exception as e:
            print(f"Error listing users: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Database setup script')
    parser.add_argument('--init', action='store_true', help='Initialize the database')
    parser.add_argument('--drop', action='store_true', help='Drop all tables before initialization')
    parser.add_argument('--create-admin', action='store_true', help='Create admin user')
    parser.add_argument('--force', action='store_true', help='Force creation of admin user even if one exists')
    parser.add_argument('--admin-username', help='Admin username (overrides environment variable)')
    parser.add_argument('--admin-password', help='Admin password (overrides environment variable)')
    parser.add_argument('--list-users', action='store_true', help='List all users')
    
    args = parser.parse_args()
    
    if not any([args.init, args.create_admin, args.list_users]):
        # On Heroku, create admin by default if no arguments provided
        if 'DYNO' in os.environ:
            args.create_admin = True
        else:
            parser.print_help()
            sys.exit(1)
    
    if args.init:
        init_database(drop_all=args.drop)
    
    if args.create_admin:
        success = create_admin_user(
            username=args.admin_username,
            password=args.admin_password,
            force=args.force
        )
        if not success and 'DYNO' in os.environ:
            print("Failed to create admin user on Heroku - will continue anyway")
    
    if args.list_users:
        list_users()
    
    print("=" * 80)
    print("SETUP_DB.PY - Execution complete")
    print("=" * 80) 