# Environment Configuration

This directory contains environment configuration templates for different deployment scenarios. These templates help you set up the proper environment variables for the AI Image Generator application.

## Available Templates

- `example.env`: The base template with all available configuration options
- `development.env`: Template for local development environments 
- `testing.env`: Template for testing environments
- `production.env`: Template for production deployments

## Setting Up Your Environment

1. Choose the template that best matches your deployment scenario
2. Copy the template to the project root directory and rename it to `.env`
3. Modify the values in the `.env` file to match your specific requirements
4. The application will automatically load these environment variables when it starts

Example:
```bash
cp docs/development.env .env
# Edit .env with your specific values
```

## Environment Variables

### Flask Configuration
- `FLASK_ENV`: The environment mode (development, testing, production)
- `SECRET_KEY`: Secret key for session encryption and security tokens

### Server Configuration
- `HOST`: Host address to bind the server to
- `PORT`: Port number to listen on

### Database Configuration
- `DATABASE_URL`: Database connection string

### FAL AI API Configuration
- `FAL_KEY`: Your API key from fal.ai
- `FAL_API_BASE_URL`: Base URL for FAL API requests

### Google OAuth Configuration
- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret
- `ALLOWED_EMAIL_DOMAIN`: Email domain to restrict user access to

### Admin Configuration
- `ADMIN_USERNAME`: Username for the initial admin user
- `ADMIN_PASSWORD`: Password for the initial admin user 