"""
Database setup script that uses the main application models to initialize the database.
This prevents duplication of model code and ensures consistency.
"""
from app import create_app
from app.models.models import db
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_database():
    """Initialize the database using the application models"""
    print("Setting up the database...")
    
    # Create the application with the correct config
    app = create_app()
    
    # Display the current configuration
    print(f"Using database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # Initialize the database within the application context
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")

if __name__ == '__main__':
    setup_database()