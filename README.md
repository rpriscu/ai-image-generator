# Zemingo AI Image Generator

A Flask-based web application that generates AI images using fal.ai's API. The application features a modern dark-themed UI, Google Sign-In authentication for Zemingo employees, and an admin panel for user management and usage tracking.

## Features

- **User Authentication**:
  - Google Sign-In restricted to @zemingo.com domain
  - Secure authentication with OAuth 2.0
  - Separate admin authentication system

- **Image Generation**:
  - Text-to-image generation with 4 outputs per prompt
  - Support for multiple fal.ai models
  - Modern, intuitive interface

- **Usage Tracking**:
  - Track API requests per user per month
  - Monthly usage statistics
  - Admin reporting dashboard

- **Administration**:
  - User management (enable/disable/remove)
  - Usage statistics and reports
  - Admin user management

- **Security**:
  - Domain-restricted access
  - Encrypted passwords
  - Session management

## Prerequisites

- Python 3.11+
- PostgreSQL database
- fal.ai API key
- Google OAuth 2.0 credentials

## Setup

1. Clone the repository:
```bash
git clone git@github.com:rpriscu/ai-image-generator.git
cd ai-image-generator
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with the following variables:
```
# Flask configuration
SECRET_KEY=your_secret_key_here
FLASK_ENV=development  # Change to 'production' for production

# Database configuration
DATABASE_URL=postgresql://username:password@localhost/dbname

# fal.ai API configuration
FAL_API_KEY=your_fal_api_key_here

# Google OAuth configuration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Initial admin user (will be created on first run)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure_password_here
```

5. Initialize the database:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

6. Run the application:
```bash
python run.py
```

The application will be available at `http://localhost:8080`

## Deploying to PythonAnywhere

1. Create a PythonAnywhere account and a new web app

2. Clone this repository to your PythonAnywhere account

3. Set up a PostgreSQL database on PythonAnywhere or use an external database service

4. Create a virtual environment and install the dependencies:
```bash
mkvirtualenv --python=/usr/bin/python3.11 ai-image-generator
pip install -r requirements.txt
pip install gunicorn
```

5. Create a `.env` file in the project root with your configuration (similar to the local setup)

6. Set up the WSGI configuration file to point to your application, using `app` from `run.py`

7. Update the static files URL configuration in PythonAnywhere web app settings

8. Initialize the database:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

9. Reload the web app

For more detailed instructions on deploying to PythonAnywhere, refer to the [pythonanywhere_setup.md](pythonanywhere_setup.md) file.

## Project Structure

```
ai-image-generator/
├── app/                      # Main application package
│   ├── __init__.py           # Application factory
│   ├── models/               # Database models
│   ├── routes/               # Route blueprints
│   │   ├── auth_routes.py    # Authentication routes
│   │   ├── admin_routes.py   # Admin panel routes
│   │   └── user_routes.py    # User-facing routes
│   ├── services/             # Service modules
│   │   ├── fal_api.py        # fal.ai API service
│   │   ├── google_auth.py    # Google OAuth service
│   │   └── usage_tracker.py  # Usage tracking service
│   ├── templates/            # Jinja2 templates
│   │   ├── admin/            # Admin panel templates
│   │   ├── auth/             # Authentication templates
│   │   └── user/             # User-facing templates
│   ├── static/               # Static assets
│   └── utils/                # Utility modules
│       └── security.py       # Security utilities
├── migrations/               # Database migrations
├── config.py                 # Application configuration
├── requirements.txt          # Project dependencies
├── run.py                    # Application entry point
└── README.md                 # Project documentation
```

## License

MIT 