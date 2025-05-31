# AI Image Generator

A Flask-based web application for generating AI images using various models through the Fal.ai API.

## Features

- **Multiple AI Models**: Support for FLUX, Recraft V3, Stable Video, and FLUX Pro (Fill)
- **User Authentication**: Google OAuth integration
- **Usage Tracking**: Monthly usage limits and tracking
- **Asset Management**: Save and manage generated images/videos
- **Admin Panel**: User management and usage monitoring
- **Responsive Design**: Works on desktop and mobile devices

## Project Structure

```
ai-image-generator/
├── app/
│   ├── models/         # Database models
│   ├── routes/         # Route handlers
│   ├── services/       # Business logic services
│   ├── static/         # CSS, JS, images
│   ├── templates/      # HTML templates
│   └── utils/          # Utility functions
├── scripts/
│   ├── deployment/     # Deployment scripts
│   └── utils/          # Utility scripts
├── docs/               # Documentation
├── migrations/         # Database migrations
├── config.py           # Configuration
├── run.py              # Application entry point
└── requirements.txt    # Python dependencies
```

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ai-image-generator
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note for Python 3.13 users**: Run the compatibility script:
```bash
python scripts/utils/downgrade_for_python_3_13.py
```

### 4. Set Environment Variables

Create a `.env` file in the root directory:

```env
# Required
SECRET_KEY=your-secret-key
FAL_KEY=your-fal-api-key
DATABASE_URL=postgresql://username:password@localhost/dbname

# Google OAuth (optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### 5. Initialize Database

```bash
# Create database
python scripts/utils/setup_db.py

# Run migrations
flask db upgrade
```

### 6. Run the Application

```bash
python run.py
```

The application will be available at `http://localhost:8080`

## Available Models

1. **FLUX [dev]** - High-quality text-to-image generation
2. **Recraft V3** - Style-consistent image generation
3. **Stable Video** - Image-to-video conversion
4. **FLUX [pro] Fill** - Advanced inpainting/outpainting

## API Endpoints

### User Routes
- `GET /` - Landing page
- `GET /register` - Registration page
- `GET /login` - Login page
- `GET /dashboard` - Main generator interface
- `GET /gallery` - User's generated assets

### API Routes
- `POST /api/generate` - Generate new assets
- `GET /api/assets` - List user's assets
- `DELETE /api/assets/<id>` - Delete an asset
- `GET /api/model-info/<model_id>` - Get model information

### Admin Routes
- `GET /admin` - Admin dashboard
- `POST /admin/users/<id>/toggle-status` - Enable/disable user
- `POST /admin/users/<id>/reset-usage` - Reset user's monthly usage

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Code Style

The project uses Black for code formatting:

```bash
black .
```

### Database Migrations

Create a new migration:
```bash
flask db migrate -m "Description of changes"
flask db upgrade
```

## Deployment

### Heroku Deployment

1. Create a Heroku app:
```bash
heroku create your-app-name
```

2. Set environment variables:
```bash
heroku config:set SECRET_KEY=your-secret-key
heroku config:set FAL_KEY=your-fal-api-key
```

3. Deploy:
```bash
git push heroku main
```

4. Initialize database:
```bash
heroku run python scripts/utils/create_tables.py
```

## Architecture

The application follows a modular architecture:

- **Models**: SQLAlchemy database models
- **Services**: Business logic layer (auth, image processing, etc.)
- **Routes**: HTTP request handlers
- **Templates**: Jinja2 HTML templates
- **Static**: Frontend assets (CSS, JS, images)

Key design patterns:
- Service layer pattern for business logic
- Repository pattern for database access
- Factory pattern for app creation
- Handler pattern for model-specific logic

## Security

- Environment variables for sensitive data
- CSRF protection enabled
- Secure session handling
- Input validation and sanitization
- Rate limiting on API endpoints

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Check the [documentation](docs/)
- Open an issue on GitHub
- Contact the development team 