"""
Consolidated database setup script.
This script handles database initialization and admin user creation.
"""
import os
import sys
import argparse
import sqlalchemy
from dotenv import load_dotenv

# Print initial diagnostic info
print("=" * 80)
print(f"SETUP_DB.PY - Database initialization script")
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

print("Importing Flask app and database models...")
try:
    from app import create_app
    from app.models.models import db, Admin, User
    print("Successfully imported Flask app and database models")
except Exception as e:
    print(f"Error importing Flask app and models: {e}")
    sys.exit(1)

# Load environment variables
print("Loading environment variables...")
load_dotenv()
print("Environment variables loaded")

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
            # Check if tables already exist
            try:
                engine = db.engine
                inspector = sqlalchemy.inspect(engine)
                existing_tables = inspector.get_table_names()
                print(f"Existing tables: {existing_tables}")
            except Exception as e:
                print(f"Could not inspect existing tables: {e}")
                existing_tables = []
                
            if drop_all:
                print("Dropping all tables...")
                db.drop_all()
                print("All tables dropped.")
            
            print("Creating tables...")
            db.create_all()
            print("Database tables created successfully!")
            
            # List all tables that were created
            try:
                inspector = sqlalchemy.inspect(engine)
                tables_after = inspector.get_table_names()
                print(f"Tables after creation: {tables_after}")
                new_tables = set(tables_after) - set(existing_tables)
                if new_tables:
                    print(f"Newly created tables: {new_tables}")
                else:
                    print("No new tables were created")
            except Exception as e:
                print(f"Could not inspect tables after creation: {e}")
                
        except Exception as e:
            print(f"ERROR creating database tables: {e}")
            print(f"Error type: {type(e).__name__}")
            
            # Try to continue even if there was an error
            print("Attempting to continue despite errors...")
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
        username = app.config.get('ADMIN_USERNAME')
    if not password:
        password = app.config.get('ADMIN_PASSWORD')
    
    if not username or not password:
        print("Error: Admin username and password are required.")
        print("Either provide them as arguments or set ADMIN_USERNAME and ADMIN_PASSWORD environment variables.")
        return
    
    print(f"Attempting to create admin user: {username}")
    with app.app_context():
        # Check if admin table exists and admin user exists
        try:
            # First check if the table exists
            engine = db.engine
            inspector = sqlalchemy.inspect(engine)
            if 'admin' not in inspector.get_table_names():
                print("Admin table does not exist yet. Creating it...")
                db.create_all()  # Create tables if they don't exist
            
            # Now check if admin already exists
            print("Checking if admin user already exists...")
            admin_exists = Admin.query.filter_by(username=username).first() is not None
            
            if admin_exists and not force:
                print(f"Admin user '{username}' already exists.")
                return
            
            # Create a new admin user
            try:
                print("Creating admin user...")
                admin = Admin.create_admin(
                    username=username,
                    password=password
                )
                print(f"Admin user '{username}' created successfully!")
                
                # Determine login URL based on environment
                login_url = None
                is_heroku = 'DYNO' in os.environ
                is_pythonanywhere = 'PYTHONANYWHERE_SITE' in os.environ
                
                if is_heroku:
                    heroku_app_name = os.environ.get('HEROKU_APP_NAME')
                    if heroku_app_name:
                        login_url = f"https://{heroku_app_name}.herokuapp.com/auth/admin/login"
                elif is_pythonanywhere:
                    pythonanywhere_domain = os.environ.get('PYTHONANYWHERE_DOMAIN')
                    if pythonanywhere_domain:
                        login_url = f"https://{pythonanywhere_domain}/auth/admin/login"
                
                if not login_url:
                    server_name = app.config.get('SERVER_NAME')
                    login_url = f"{server_name or 'http://localhost:8080'}/auth/admin/login"
                    
                print(f"You can log in at: {login_url}")
            except Exception as e:
                print(f"Error creating admin user: {str(e)}")
                print(f"Error type: {type(e).__name__}")
        except Exception as e:
            print(f"Error checking or creating admin user: {e}")
            print(f"Error type: {type(e).__name__}")

def list_users():
    """List all users in the database"""
    print("Creating Flask application for listing users...")
    app = create_app()
    print("Flask application created")
    
    with app.app_context():
        try:
            # First check if tables exist
            inspector = sqlalchemy.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'user' not in existing_tables:
                print("User table does not exist yet.")
                return
                
            print("Users in the database:")
            print("-" * 50)
            users = User.query.all()
            if not users:
                print("No users found.")
            else:
                for user in users:
                    print(f"ID: {user.id}, Email: {user.email}, Active: {user.is_active}")
            
            if 'admin' not in existing_tables:
                print("\nAdmin table does not exist yet.")
                return
                
            print("\nAdmins in the database:")
            print("-" * 50)
            admins = Admin.query.all()
            if not admins:
                print("No admin users found.")
            else:
                for admin in admins:
                    print(f"ID: {admin.id}, Username: {admin.username}")
        except Exception as e:
            print(f"Error listing users: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Database setup and management script")
    parser.add_argument('--drop', action='store_true', help='Drop all tables before creating them')
    parser.add_argument('--init', action='store_true', help='Initialize database tables')
    parser.add_argument('--create-admin', action='store_true', help='Create admin user')
    parser.add_argument('--admin-username', help='Admin username (default: from env vars)')
    parser.add_argument('--admin-password', help='Admin password (default: from env vars)')
    parser.add_argument('--force', action='store_true', help='Force creation of admin even if one exists')
    parser.add_argument('--list-users', action='store_true', help='List all users in the database')
    
    print("Parsing command line arguments...")
    args = parser.parse_args()
    print(f"Command line arguments: {args}")
    
    # If no args provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    
    # Execute commands
    if args.init or args.drop:
        try:
            print("Initializing database...")
            success = init_database(drop_all=args.drop)
            if success:
                print("Database initialization complete")
            else:
                print("Database initialization had some issues but we'll continue")
        except Exception as e:
            print(f"Database initialization failed: {e}")
            # Don't exit with an error to allow deployment to continue
            print("Continuing with deployment despite database initialization errors")
    
    if args.create_admin:
        print("Creating admin user...")
        create_admin_user(args.admin_username, args.admin_password, args.force)
    
    if args.list_users:
        print("Listing users...")
        list_users()
    
    print("=" * 80)
    print("SETUP_DB.PY - Execution complete")
    print("=" * 80) 