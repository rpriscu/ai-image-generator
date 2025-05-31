"""
Image Processing Service
========================

This module handles all image processing operations for the AI Image Generator.
It provides utilities for:
- Image resizing and format conversion
- Base64 encoding/decoding
- Image validation
- Mask processing for inpainting

These utilities are used by the FAL API service and other components
that need to process images before sending them to AI models.
"""

import base64
import io
import logging
from typing import Optional, Tuple, Union
from PIL import Image
from werkzeug.datastructures import FileStorage

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Handles image processing operations for AI model inputs."""
    
    # Maximum dimensions for processed images
    DEFAULT_MAX_SIZE = 1024
    SUPPORTED_FORMATS = {'jpg', 'jpeg', 'png', 'webp'}
    
    @staticmethod
    def process_image_file(
        image_file: FileStorage,
        max_size: int = DEFAULT_MAX_SIZE,
        output_format: str = 'PNG',
        quality: int = 95
    ) -> Tuple[str, Tuple[int, int]]:
        """
        Process an uploaded image file for API consumption.
        
        Args:
            image_file: The uploaded file from Flask request
            max_size: Maximum dimension (width or height) in pixels
            output_format: Output format (PNG, JPEG, etc.)
            quality: JPEG quality (1-100, only used for JPEG format)
            
        Returns:
            Tuple of (base64_string, (width, height))
            
        Raises:
            ValueError: If image processing fails
            
        Example:
            >>> img_b64, dimensions = ImageProcessor.process_image_file(request.files['image'])
            >>> print(f"Processed image: {dimensions[0]}x{dimensions[1]}")
        """
        try:
            # Open and validate image
            image = Image.open(image_file)
            logger.info(f"Original image: {image.size}, mode: {image.mode}")
            
            # Resize if needed while maintaining aspect ratio
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"Resized image to: {new_size}")
            
            # Convert to RGB if needed (required for JPEG)
            if image.mode not in ('RGB', 'RGBA'):
                image = image.convert('RGB')
                logger.info("Converted image to RGB mode")
            
            # Save to buffer
            buffer = io.BytesIO()
            save_kwargs = {'format': output_format}
            if output_format.upper() in ('JPEG', 'JPG'):
                save_kwargs['quality'] = quality
                
            image.save(buffer, **save_kwargs)
            
            # Convert to base64
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return img_str, image.size
            
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            raise ValueError(f"Failed to process image: {str(e)}")
    
    @staticmethod
    def create_data_uri(base64_string: str, mime_type: str = 'image/png') -> str:
        """
        Create a data URI from a base64 string.
        
        Args:
            base64_string: The base64 encoded image data
            mime_type: MIME type of the image
            
        Returns:
            Complete data URI string
            
        Example:
            >>> data_uri = ImageProcessor.create_data_uri(img_b64, 'image/jpeg')
            >>> # Returns: "data:image/jpeg;base64,..."
        """
        return f"data:{mime_type};base64,{base64_string}"
    
    @staticmethod
    def process_mask_image(
        mask_file: FileStorage,
        target_size: Tuple[int, int]
    ) -> str:
        """
        Process a mask image for inpainting operations.
        
        Masks should be grayscale where:
        - White (255) = areas to be filled/generated
        - Black (0) = areas to preserve
        
        Args:
            mask_file: The uploaded mask file
            target_size: Target dimensions to match the reference image
            
        Returns:
            Base64 encoded mask image
            
        Raises:
            ValueError: If mask processing fails
        """
        try:
            # Open mask image
            mask = Image.open(mask_file)
            logger.info(f"Original mask: {mask.size}, mode: {mask.mode}")
            
            # Resize to match target dimensions
            if mask.size != target_size:
                mask = mask.resize(target_size, Image.Resampling.LANCZOS)
                logger.info(f"Resized mask to match target: {target_size}")
            
            # Convert to grayscale
            if mask.mode not in ('L', '1'):
                mask = mask.convert('L')
                logger.info("Converted mask to grayscale")
            
            # Save to buffer
            buffer = io.BytesIO()
            mask.save(buffer, format='PNG')
            
            # Convert to base64
            mask_str = base64.b64encode(buffer.getvalue()).decode()
            
            return mask_str
            
        except Exception as e:
            logger.error(f"Error processing mask: {str(e)}")
            raise ValueError(f"Failed to process mask: {str(e)}")
    
    @staticmethod
    def validate_image_file(
        file: FileStorage,
        max_size_mb: float = 10,
        allowed_formats: Optional[set] = None
    ) -> bool:
        """
        Validate an uploaded image file.
        
        Args:
            file: The uploaded file to validate
            max_size_mb: Maximum file size in megabytes
            allowed_formats: Set of allowed format extensions
            
        Returns:
            True if valid, raises ValueError if invalid
            
        Raises:
            ValueError: If validation fails with specific reason
        """
        if not file:
            raise ValueError("No file provided")
        
        # Check file extension
        if allowed_formats is None:
            allowed_formats = ImageProcessor.SUPPORTED_FORMATS
            
        filename = file.filename or ''
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        
        if ext not in allowed_formats:
            raise ValueError(f"Unsupported format. Allowed: {', '.join(allowed_formats)}")
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        size_mb = file.tell() / (1024 * 1024)
        file.seek(0)  # Reset position
        
        if size_mb > max_size_mb:
            raise ValueError(f"File too large. Maximum size: {max_size_mb}MB")
        
        # Try to open as image
        try:
            Image.open(file)
            file.seek(0)  # Reset for future use
        except Exception:
            raise ValueError("Invalid image file")
        
        return True
    
    @staticmethod
    def save_base64_image(
        base64_data: str,
        output_dir: str,
        prefix: str = 'img'
    ) -> str:
        """
        Save a base64 encoded image to disk.
        
        Args:
            base64_data: Base64 encoded image data (with or without data URI prefix)
            output_dir: Directory to save the image
            prefix: Filename prefix
            
        Returns:
            Path to the saved file
            
        Example:
            >>> path = ImageProcessor.save_base64_image(img_b64, '/tmp', 'generated')
            >>> # Returns: '/tmp/generated_20240101_123456.png'
        """
        import os
        import datetime
        
        # Extract actual base64 data if it's a data URI
        if base64_data.startswith('data:'):
            base64_data = base64_data.split(',')[1]
        
        # Decode base64
        img_data = base64.b64decode(base64_data)
        
        # Generate unique filename
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = os.urandom(4).hex()
        filename = f"{prefix}_{timestamp}_{unique_id}.png"
        filepath = os.path.join(output_dir, filename)
        
        # Ensure directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Save file
        with open(filepath, 'wb') as f:
            f.write(img_data)
        
        logger.info(f"Saved image to: {filepath}")
        return filepath 