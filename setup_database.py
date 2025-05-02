"""
Database setup script that properly creates tables before querying them.
This avoids the 'relation does not exist' error.
"""
from app import create_app
from app.models.models import db, Admin
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_database():
    """Initialize the database and create the admin user"""
    print("Setting up the database...")
    
    # Create the application with the correct config
    app = create_app()
    
    # Modify app to avoid creating admin during initialization
    app.config['SKIP_ADMIN_CREATION'] = True
    
    # Display the current configuration
    print(f"Using database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # Initialize the database within the application context
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")
        
        # Now create admin user if configured
        if app.config.get('ADMIN_USERNAME') and app.config.get('ADMIN_PASSWORD'):
            try:
                Admin.create_admin(
                    username=app.config.get('ADMIN_USERNAME'),
                    password=app.config.get('ADMIN_PASSWORD')
                )
                print(f"Admin user '{app.config.get('ADMIN_USERNAME')}' created successfully!")
            except Exception as e:
                print(f"Error creating admin user: {str(e)}")

if __name__ == '__main__':
    setup_database() 