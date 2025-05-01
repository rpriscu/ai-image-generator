from app import create_app
from app.models.models import Admin, db

def create_admin_user(username, password):
    """Create an admin user with the specified username and password"""
    app = create_app()
    
    with app.app_context():
        # Check if admin with this username already exists
        existing_admin = Admin.query.filter_by(username=username).first()
        if existing_admin:
            print(f"Admin with username '{username}' already exists.")
            return
        
        # Create a new admin user
        try:
            admin = Admin.create_admin(
                username=username,
                password=password
            )
            print(f"Admin user '{username}' created successfully!")
        except Exception as e:
            print(f"Error creating admin user: {str(e)}")

if __name__ == "__main__":
    import sys
    
    # Default admin credentials if not provided as arguments
    default_username = "admin"
    default_password = "admin123"
    
    if len(sys.argv) > 2:
        username = sys.argv[1]
        password = sys.argv[2]
    else:
        username = default_username
        password = default_password
        print(f"Using default credentials: username='{username}', password='{password}'")
    
    create_admin_user(username, password)
    print("You can now log in at: http://localhost:8080/auth/admin/login") 