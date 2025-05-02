"""
Consolidated database setup script.
This script handles database initialization and admin user creation.
"""
import os
import sys
import argparse
from dotenv import load_dotenv
from app import create_app
from app.models.models import db, Admin, User

# Load environment variables
load_dotenv()

def init_database(drop_all=False):
    """
    Initialize the database tables.
    
    Args:
        drop_all (bool): Whether to drop all tables before creating them
    """
    print("Setting up the database...")
    
    # Create application with initialization flag
    app = create_app()
    app.config['SKIP_ADMIN_CREATION'] = True
    
    # Display database configuration
    print(f"Using database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    with app.app_context():
        if drop_all:
            print("Dropping all tables...")
            db.drop_all()
            print("All tables dropped.")
        
        print("Creating tables...")
        db.create_all()
        print("Database tables created successfully!")

def create_admin_user(username=None, password=None, force=False):
    """
    Create an admin user.
    
    Args:
        username (str): Admin username
        password (str): Admin password
        force (bool): Whether to create a new admin even if one exists
    """
    # Create the application
    app = create_app()
    app.config['SKIP_ADMIN_CREATION'] = True
    
    # Use environment variables if not provided
    if not username:
        username = app.config.get('ADMIN_USERNAME')
    if not password:
        password = app.config.get('ADMIN_PASSWORD')
    
    if not username or not password:
        print("Error: Admin username and password are required.")
        print("Either provide them as arguments or set ADMIN_USERNAME and ADMIN_PASSWORD environment variables.")
        return
    
    with app.app_context():
        # Check if admin already exists
        admin_exists = Admin.query.filter_by(username=username).first() is not None
        
        if admin_exists and not force:
            print(f"Admin user '{username}' already exists.")
            return
        
        # Create a new admin user
        try:
            admin = Admin.create_admin(
                username=username,
                password=password
            )
            print(f"Admin user '{username}' created successfully!")
            print(f"You can log in at: {app.config['SERVER_NAME'] or 'http://localhost:8080'}/auth/admin/login")
        except Exception as e:
            print(f"Error creating admin user: {str(e)}")

def list_users():
    """List all users in the database"""
    app = create_app()
    
    with app.app_context():
        print("Users in the database:")
        print("-" * 50)
        users = User.query.all()
        if not users:
            print("No users found.")
        else:
            for user in users:
                print(f"ID: {user.id}, Email: {user.email}, Active: {user.is_active}")
        
        print("\nAdmins in the database:")
        print("-" * 50)
        admins = Admin.query.all()
        if not admins:
            print("No admin users found.")
        else:
            for admin in admins:
                print(f"ID: {admin.id}, Username: {admin.username}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Database setup and management script")
    parser.add_argument('--drop', action='store_true', help='Drop all tables before creating them')
    parser.add_argument('--init', action='store_true', help='Initialize database tables')
    parser.add_argument('--create-admin', action='store_true', help='Create admin user')
    parser.add_argument('--admin-username', help='Admin username (default: from env vars)')
    parser.add_argument('--admin-password', help='Admin password (default: from env vars)')
    parser.add_argument('--force', action='store_true', help='Force creation of admin even if one exists')
    parser.add_argument('--list-users', action='store_true', help='List all users in the database')
    
    args = parser.parse_args()
    
    # If no args provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    
    # Execute commands
    if args.init or args.drop:
        init_database(drop_all=args.drop)
    
    if args.create_admin:
        create_admin_user(args.admin_username, args.admin_password, args.force)
    
    if args.list_users:
        list_users() 