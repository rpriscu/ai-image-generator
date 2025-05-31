# AI Image Generator - Code Style Guide

## Overview

This guide establishes coding standards and best practices for the AI Image Generator project. Following these guidelines ensures code consistency, readability, and maintainability across the team.

## Python Version

- **Target Version**: Python 3.8+
- **Compatibility**: Ensure code works with Python 3.8 through 3.13

## Code Formatting

### Tools

Use these tools for automatic code formatting:

```bash
# Install development dependencies
pip install black isort flake8 mypy

# Format code
black .
isort .

# Check code quality
flake8 .
mypy .
```

### Configuration

`.flake8`:
```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,venv,migrations
```

`pyproject.toml`:
```toml
[tool.black]
line-length = 88
target-version = ['py38']

[tool.isort]
profile = "black"
line_length = 88
```

## Naming Conventions

### General Rules

- Use descriptive names that explain purpose
- Avoid abbreviations except well-known ones
- Be consistent with existing codebase

### Specific Conventions

| Type | Convention | Example |
|------|------------|---------|
| Variables | `snake_case` | `user_input`, `image_file` |
| Functions | `snake_case` | `generate_image()`, `validate_input()` |
| Classes | `PascalCase` | `FalApiService`, `ImageProcessor` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_FILE_SIZE`, `API_TIMEOUT` |
| Private | Leading underscore | `_internal_method()` |
| Module | `snake_case` | `fal_api.py`, `model_handlers.py` |

## Type Hints

Always use type hints for function signatures:

```python
from typing import Dict, List, Optional, Union, Tuple, Any
from werkzeug.datastructures import FileStorage

def process_image(
    file: FileStorage,
    max_size: int = 1024,
    formats: List[str] = ["jpg", "png"]
) -> Tuple[str, Tuple[int, int]]:
    """
    Process an uploaded image file.
    
    Args:
        file: The uploaded file object
        max_size: Maximum dimension in pixels
        formats: Allowed image formats
        
    Returns:
        Tuple of (base64_string, (width, height))
        
    Raises:
        ValueError: If file format is invalid
        IOError: If file cannot be processed
    """
    pass
```

## Documentation

### Module Documentation

Every module should start with a docstring:

```python
"""
Module for handling FAL.ai API interactions.

This module provides a service class for communicating with the FAL.ai API,
handling authentication, request formatting, and response parsing.

Classes:
    FalApiService: Main service for API communication
    
Functions:
    parse_response: Parse API responses into standard format
"""
```

### Function Documentation

Use Google-style docstrings:

```python
def generate_content(
    self,
    prompt: str,
    model: Dict[str, Any],
    image_file: Optional[FileStorage] = None,
    mask_file: Optional[FileStorage] = None
) -> Dict[str, Union[str, int]]:
    """
    Generate content using the specified model.
    
    Args:
        prompt: Text description for generation
        model: Model configuration dictionary containing:
            - endpoint (str): API endpoint
            - type (str): Model type
            - params (dict): Default parameters
        image_file: Optional reference image for img2img models
        mask_file: Optional mask for inpainting models
        
    Returns:
        Dictionary containing:
            - url (str): Generated content URL
            - type (str): Content type ('image' or 'video')
            - id (int): Database asset ID
            
    Raises:
        ValueError: If required inputs are missing
        APIError: If API call fails
        
    Example:
        >>> result = service.generate_content(
        ...     prompt="A sunset over mountains",
        ...     model={"endpoint": "fal-ai/flux", "type": "text-to-image"}
        ... )
        >>> print(result['url'])
        '/static/generated/img_123.png'
    """
    pass
```

### Class Documentation

```python
class ImageProcessor:
    """
    Handles image processing operations.
    
    This class provides utilities for resizing, converting, and
    saving images in various formats. It's designed to work with
    both PIL Image objects and base64-encoded strings.
    
    Attributes:
        max_size (int): Maximum dimension for processed images
        quality (int): JPEG compression quality (1-100)
        
    Example:
        >>> processor = ImageProcessor(max_size=1024)
        >>> base64_img = processor.process_upload(file_storage)
    """
    
    def __init__(self, max_size: int = 1024, quality: int = 85):
        """
        Initialize the image processor.
        
        Args:
            max_size: Maximum width or height in pixels
            quality: JPEG compression quality
        """
        self.max_size = max_size
        self.quality = quality
```

## Code Organization

### Import Order

Follow this order for imports:

```python
# 1. Standard library imports
import os
import sys
from datetime import datetime
from typing import Dict, Optional

# 2. Third-party imports
import requests
from flask import Flask, request, jsonify
from PIL import Image

# 3. Local application imports
from app.models import User, Asset
from app.services.fal_api import FalApiService
from app.utils.validation import validate_image
```

### File Structure

```python
"""Module docstring"""

# Imports
import ...

# Constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FORMATS = ["jpg", "jpeg", "png", "webp"]

# Module-level variables (if needed)
logger = logging.getLogger(__name__)

# Classes
class MyClass:
    pass

# Functions
def my_function():
    pass

# Main execution (if applicable)
if __name__ == "__main__":
    main()
```

## Best Practices

### 1. Use Context Managers

```python
# Good
with open('file.txt', 'r') as f:
    content = f.read()

# Good - Custom context manager
from contextlib import contextmanager

@contextmanager
def timer(name: str):
    start = time.time()
    try:
        yield
    finally:
        logger.info(f"{name} took {time.time() - start:.2f}s")

# Usage
with timer("API call"):
    result = api.generate_image(prompt)
```

### 2. Handle Exceptions Properly

```python
# Good - Specific exception handling
try:
    result = api_service.generate(prompt)
except ValidationError as e:
    logger.warning(f"Invalid input: {e}")
    return jsonify({"error": str(e)}), 400
except APIError as e:
    logger.error(f"API failed: {e}")
    return jsonify({"error": "Service temporarily unavailable"}), 503
except Exception as e:
    logger.exception("Unexpected error")
    return jsonify({"error": "Internal server error"}), 500

# Bad - Catching all exceptions
try:
    result = api_service.generate(prompt)
except:
    return jsonify({"error": "Something went wrong"}), 500
```

### 3. Use Logging Instead of Print

```python
import logging

logger = logging.getLogger(__name__)

# Good
logger.info(f"Processing request for user {user_id}")
logger.warning(f"Rate limit approaching for user {user_id}")
logger.error(f"Failed to generate image: {error}")

# Bad
print(f"Processing request for user {user_id}")
```

### 4. Avoid Mutable Default Arguments

```python
# Bad
def add_item(item, items=[]):
    items.append(item)
    return items

# Good
def add_item(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items
```

### 5. Use Enumerate for Loops with Indices

```python
# Bad
for i in range(len(items)):
    print(f"{i}: {items[i]}")

# Good
for i, item in enumerate(items):
    print(f"{i}: {item}")
```

### 6. Prefer List Comprehensions (When Readable)

```python
# Good - Simple and readable
squares = [x**2 for x in range(10)]

# Good - With condition
even_squares = [x**2 for x in range(10) if x % 2 == 0]

# Bad - Too complex, use regular loop
result = [process(x) for x in items 
          if validate(x) and x.status == 'active' 
          for y in x.children if y.enabled]
```

### 7. Use Constants for Magic Values

```python
# Bad
if file_size > 10485760:
    raise ValueError("File too large")

# Good
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB

if file_size > MAX_FILE_SIZE_BYTES:
    raise ValueError(f"File exceeds {MAX_FILE_SIZE_BYTES} bytes")
```

## Testing Guidelines

### Test Naming

```python
class TestImageProcessor:
    def test_resize_image_maintains_aspect_ratio(self):
        """Test that resizing maintains the original aspect ratio."""
        pass
        
    def test_process_invalid_format_raises_error(self):
        """Test that invalid formats raise ValueError."""
        pass
```

### Test Structure (AAA Pattern)

```python
def test_generate_image_success(self):
    # Arrange
    service = FalApiService()
    prompt = "A beautiful sunset"
    model = {"endpoint": "fal-ai/flux"}
    
    # Act
    result = service.generate_image(prompt, model)
    
    # Assert
    assert result is not None
    assert 'url' in result
    assert result['url'].startswith('/static/generated/')
```

## Security Guidelines

### 1. Validate All Inputs

```python
def validate_file_upload(file: FileStorage) -> None:
    """Validate uploaded file for security."""
    # Check file extension
    if not file.filename:
        raise ValueError("No filename provided")
        
    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File type .{ext} not allowed")
    
    # Check file size
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    
    if size > MAX_FILE_SIZE:
        raise ValueError(f"File size {size} exceeds maximum")
    
    # Check file content matches extension
    mime_type = file.content_type
    if not mime_type.startswith('image/'):
        raise ValueError("File is not an image")
```

### 2. Never Store Sensitive Data in Code

```python
# Bad
API_KEY = "sk-1234567890abcdef"

# Good
API_KEY = os.environ.get('FAL_API_KEY')
if not API_KEY:
    raise ValueError("FAL_API_KEY environment variable not set")
```

### 3. Use Parameterized Queries

```python
# Bad - SQL injection risk
query = f"SELECT * FROM users WHERE email = '{email}'"

# Good - Using SQLAlchemy
user = User.query.filter_by(email=email).first()

# Good - Raw SQL with parameters
query = "SELECT * FROM users WHERE email = :email"
result = db.session.execute(query, {"email": email})
```

## Performance Guidelines

### 1. Use Generators for Large Data Sets

```python
# Bad - Loads all into memory
def get_all_assets():
    return [asset.to_dict() for asset in Asset.query.all()]

# Good - Generator
def get_all_assets():
    for asset in Asset.query.yield_per(100):
        yield asset.to_dict()
```

### 2. Cache Expensive Operations

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_model_config(model_id: str) -> Dict[str, Any]:
    """Get model configuration with caching."""
    return MODEL_CONFIGURATIONS.get(model_id, {})
```

### 3. Use Bulk Operations

```python
# Bad - Multiple queries
for item in items:
    asset = Asset(user_id=user_id, **item)
    db.session.add(asset)
    db.session.commit()

# Good - Single commit
assets = [Asset(user_id=user_id, **item) for item in items]
db.session.bulk_save_objects(assets)
db.session.commit()
```

## Git Commit Messages

Follow the conventional commits format:

```
type(scope): subject

body (optional)

footer (optional)
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Test additions or changes
- `chore`: Build process or auxiliary tool changes

Examples:
```
feat(api): add support for FLUX.1 pro model

fix(auth): resolve Google OAuth token validation issue

docs(readme): update installation instructions

refactor(services): split fal_api.py into smaller modules
- Extract REST client logic
- Move image processing to separate module
- Create response parser utility
```

## Code Review Checklist

Before submitting code for review:

- [ ] Code follows style guidelines
- [ ] All functions have type hints
- [ ] Complex logic is documented
- [ ] No hardcoded values (use constants)
- [ ] Error handling is appropriate
- [ ] Security considerations addressed
- [ ] Tests written for new functionality
- [ ] No commented-out code
- [ ] No print statements (use logging)
- [ ] Dependencies updated if needed 