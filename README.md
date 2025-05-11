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

## Local Setup

1. Clone the repository:
```bash
git clone https://github.com/rpriscu/ai-image-generator.git
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
FAL_KEY=your_fal_api_key_here

# Google OAuth configuration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Initial admin user (will be created on first run)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure_password_here
```

5. Initialize the database:
```bash
# Create database tables
python setup_db.py --init

# Create admin user
python setup_db.py --create-admin
```

6. Run the application:
```bash
python run.py
```

The application will be available at `http://localhost:8080`

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Flask secret key for session encryption | Yes (in production) | dev-key-change-in-production |
| `FLASK_ENV` | Environment (development/production) | No | development |
| `DATABASE_URL` | Database connection URL | Yes | sqlite:///dev.db (in development) |
| `FAL_KEY` | fal.ai API key | Yes | None |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | Yes | None |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | Yes | None |
| `ALLOWED_EMAIL_DOMAIN` | Email domain for Google login | No | zemingo.com |
| `ADMIN_USERNAME` | Initial admin username | Yes | None |
| `ADMIN_PASSWORD` | Initial admin password | Yes | None |
| `HOST` | Host to run development server on | No | 0.0.0.0 |
| `PORT` | Port to run development server on | No | 8080 |
| `PYTHONANYWHERE_DOMAIN` | Domain for PythonAnywhere | No | rpriscu.pythonanywhere.com |

## Deploying to PythonAnywhere

For detailed deployment instructions, please see the [Deployment Guide](deployment_guide.md).

Quick steps:

1. Clone the repository on PythonAnywhere
2. Set up a virtual environment and install dependencies
3. Configure the web app settings in PythonAnywhere
4. Set up the database
5. Update the WSGI file
6. Reload the web app

## Database Management

The application comes with a database management utility (`setup_db.py`) that can perform the following operations:

- Initialize database tables: `python setup_db.py --init`
- Create admin user: `python setup_db.py --create-admin`
- List all users: `python setup_db.py --list-users`
- Reset database (drop all tables and recreate): `python setup_db.py --drop --init`

For help on available commands, run: `python setup_db.py`

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
│   ├── static/               # Static assets
│   └── utils/                # Utility modules
│       ├── db_config.py      # Database configuration utilities
│       └── cleanup.py        # Cleanup utilities
├── migrations/               # Database migrations
├── config.py                 # Application configuration
├── deployment_guide.md       # PythonAnywhere deployment guide
├── requirements.txt          # Project dependencies
├── run.py                    # Application entry point
├── setup_db.py               # Database setup script
└── README.md                 # Project documentation
```

## License

MIT 