# AI Coding Guide for AI Image Generator

## Overview

This guide is designed to help AI models understand and work effectively with the AI Image Generator codebase. The project is a Flask-based web application that provides a unified interface for multiple AI image generation models.

## Architecture Overview

```
ai-image-generator/
├── app/
│   ├── __init__.py              # Flask app initialization
│   ├── models/                  # Database models
│   │   └── models.py           # SQLAlchemy models
│   ├── routes/                  # HTTP route handlers
│   │   ├── auth_routes.py      # Authentication endpoints
│   │   └── user_routes.py      # User-facing endpoints
│   ├── services/               # Business logic layer
│   │   ├── fal_api.py         # FAL.ai API integration
│   │   ├── models_config.py    # Model configurations
│   │   ├── model_handlers.py   # Model-specific handlers
│   │   ├── image_processor.py  # Image processing utilities
│   │   ├── url_shortener.py    # URL shortening service
│   │   └── usage_tracker.py    # Usage tracking service
│   ├── static/                 # Static assets
│   │   ├── css/               # Stylesheets
│   │   │   └── dashboard.css  # Dashboard styles
│   │   └── js/                # JavaScript modules
│   │       ├── model-ui-manager.js  # UI state management
│   │       └── dashboard-api.js     # API client
│   └── templates/              # Jinja2 templates
│       └── user/
│           └── dashboard.html  # Main interface
├── requirements.txt            # Python dependencies
└── config.py                  # Configuration management
```

## Key Design Patterns

### 1. **Model Configuration System**
All model behaviors are centralized in `models_config.py`:
- UI requirements (what inputs to show/hide)
- Validation rules
- Default parameters
- API endpoints

**When adding a new model:**
```python
MODEL_CONFIGURATIONS['new_model'] = {
    'name': 'Model Display Name',
    'endpoint': 'api/endpoint',
    'type': 'text-to-image',  # or 'image-to-video', 'inpainting'
    'ui_config': {...},
    'validation': {...},
    'default_params': {...}
}
```

### 2. **Handler Pattern**
Each model type has a handler in `model_handlers.py`:
- `TextToImageHandler` - Standard image generation
- `ImageToVideoHandler` - Video generation from images
- `InpaintingHandler` - Mask-based editing

Handlers encapsulate:
- Request preparation
- Response processing
- Input validation

### 3. **Service Layer**
Business logic is separated into services:
- **FalApiService**: API communication
- **ImageProcessor**: Image manipulation
- **URLShortener**: URL management
- **UsageTracker**: Usage monitoring

## Common Tasks

### Adding a New Model

1. **Add configuration** in `models_config.py`:
```python
'new_model': {
    'name': 'New Model Name',
    'endpoint': 'fal-ai/new-model',
    'type': 'text-to-image',
    'default_num_outputs': 4,
    'ui_config': {
        'show_prompt': True,
        'prompt_required': True,
        # ... other UI settings
    },
    'validation': {
        'prompt': {
            'required': True,
            'min_length': 3,
            'max_length': 1000
        }
    }
}
```

2. **Create handler** if needed (for new model types)
3. **Update UI** - The frontend will automatically adapt based on configuration

### Modifying API Behavior

API methods are in `fal_api.py`:
- `_generate_with_rest_api()` - Standard REST calls
- `_generate_with_fal_client()` - Using fal_client library
- `_fallback_fal_client()` - Fallback method

### Frontend Modifications

JavaScript is modularized:
- `model-ui-manager.js` - UI state based on model
- `dashboard-api.js` - API calls
- Dashboard template uses these modules

## Error Handling

### API Errors
- Always return JSON with `error` key
- Log errors with context
- Provide user-friendly messages

### Validation
- Use model handlers for input validation
- Return specific error messages
- Validate both client and server side

## Database Schema

Key models in `models.py`:
- **User**: Authentication and profile
- **Asset**: Generated images/videos
- **MonthlyUsage**: Usage tracking
- **ShortUrl**: URL shortening

## Best Practices

### 1. **Use Type Hints**
```python
def process_image(file: FileStorage, max_size: int = 1024) -> Tuple[str, Tuple[int, int]]:
    """Process image and return base64 and dimensions."""
```

### 2. **Document Complex Logic**
```python
# For flux and recraft, default to 4 images if not specified
default_num_images = 4 if model_id in ['flux', 'recraft'] else 1
```

### 3. **Handle Edge Cases**
```python
# Check if mask dimensions match image
if mask_size != image_size:
    logger.info(f"Resizing mask to match image: {image_size}")
    mask = mask.resize(image_size)
```

### 4. **Log Important Operations**
```python
logger.info(f"Generating {num_outputs} outputs for model {model_id}")
```

## Common Pitfalls to Avoid

1. **Don't hardcode model behaviors** - Use configuration
2. **Don't mix concerns** - Keep handlers, services, and routes separate
3. **Don't forget error handling** - Every external call can fail
4. **Don't ignore validation** - Validate inputs early
5. **Don't create circular imports** - Use proper module structure

## Testing Checklist

When modifying code, test:
- [ ] All model types (text-to-image, video, inpainting)
- [ ] File uploads (images and masks)
- [ ] Error cases (invalid inputs, API failures)
- [ ] UI responsiveness
- [ ] Database operations

## Debugging Tips

1. **Check logs** - Extensive logging throughout
2. **Verify configuration** - Most issues are config-related
3. **Test API directly** - Use curl/Postman to isolate issues
4. **Check browser console** - Frontend errors appear there
5. **Database state** - Use Flask shell to inspect

## Performance Considerations

1. **Image processing** - Resize large images before API calls
2. **Database queries** - Use eager loading for relationships
3. **Caching** - URL shortener uses cache for performance
4. **Async operations** - Long-running tasks should be async

## Security Notes

1. **API keys** - Never commit to version control
2. **File uploads** - Validate type and size
3. **SQL injection** - Use SQLAlchemy, not raw SQL
4. **XSS prevention** - Jinja2 auto-escapes by default

## Future Improvements

Areas that could be enhanced:
1. **Queue system** for long-running generations
2. **WebSocket** for real-time updates
3. **CDN integration** for generated assets
4. **Advanced caching** strategies
5. **Batch processing** support

---

 