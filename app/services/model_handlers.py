"""
Model Handlers for AI Image Generation
======================================

This module provides handler classes that encapsulate the behavior for different model types.
Each handler knows how to:
- Prepare API requests with model-specific parameters
- Process API responses into a standardized format
- Validate inputs according to model requirements

The handler pattern allows us to add new model types without modifying core logic.

Classes:
    BaseModelHandler: Abstract base class defining the handler interface
    TextToImageHandler: Handles standard text-to-image models
    ImageToVideoHandler: Handles image-to-video conversion models
    InpaintingHandler: Handles mask-based inpainting models
    ModelHandlerRegistry: Registry for managing handler instances
"""
from abc import ABC, abstractmethod
import logging
from typing import Dict, Any, Optional, List, Tuple
from werkzeug.datastructures import FileStorage

logger = logging.getLogger(__name__)


class BaseModelHandler(ABC):
    """
    Abstract base class for model handlers.
    
    All model handlers must inherit from this class and implement the required methods.
    This ensures a consistent interface for all model types.
    
    Attributes:
        config: The model configuration dictionary
        model_id: The model's endpoint identifier
        name: The model's display name
    """
    
    def __init__(self, model_config: Dict[str, Any]):
        """
        Initialize the handler with model configuration.
        
        Args:
            model_config: Dictionary containing model configuration including
                         endpoint, name, parameters, and validation rules
        """
        self.config = model_config
        self.model_id = model_config.get('endpoint', '')
        self.name = model_config.get('name', '')
        
    @abstractmethod
    def prepare_request(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Prepare the API request payload for the model.
        
        Args:
            prompt: The text prompt for generation
            **kwargs: Additional parameters like image_file, mask_file, num_outputs, etc.
            
        Returns:
            Dictionary containing the prepared request payload
            
        Raises:
            ValueError: If required parameters are missing
        """
        pass
    
    @abstractmethod
    def process_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process the API response and normalize it.
        
        Args:
            response: Raw API response dictionary
            
        Returns:
            List of dictionaries with 'url' and 'type' keys
            Example: [{'url': 'https://...', 'type': 'image'}]
        """
        pass
    
    @abstractmethod
    def validate_inputs(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Validate inputs according to model requirements.
        
        Args:
            prompt: The text prompt to validate
            **kwargs: Additional inputs to validate (image_file, mask_file, etc.)
            
        Returns:
            Dictionary with keys:
                - 'valid': Boolean indicating if inputs are valid
                - 'errors': Dictionary mapping field names to error messages
                
        Example:
            {'valid': False, 'errors': {'prompt': 'Prompt is required'}}
        """
        pass
    
    def get_num_outputs(self, requested: Optional[int] = None) -> int:
        """
        Get the number of outputs to generate, respecting model limits.
        
        Args:
            requested: Number of outputs requested by user
            
        Returns:
            Actual number of outputs to generate (capped by max_outputs)
            
        Example:
            >>> handler.get_num_outputs(10)  # If max is 4
            4
        """
        default = self.config.get('default_num_outputs', 1)
        max_outputs = self.config.get('max_outputs', 4)
        
        if requested is None:
            return default
        
        return min(requested, max_outputs)


class TextToImageHandler(BaseModelHandler):
    """
    Handler for standard text-to-image models.
    
    Supports models like FLUX, Recraft, and Stable Diffusion that generate
    images from text prompts. May also support optional reference images
    for hybrid models.
    """
    
    def prepare_request(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Prepare request for text-to-image generation.
        
        Args:
            prompt: Text description of the desired image
            **kwargs: Optional parameters including:
                - num_outputs: Number of images to generate
                - image_file: Optional reference image (FileStorage)
                - negative_prompt: What to avoid in the image
                - guidance_scale: How closely to follow the prompt
                - num_inference_steps: Quality/speed tradeoff
                - strength: How much to modify reference image
                - seed: Random seed for reproducibility
                
        Returns:
            Request payload dictionary with all parameters
            
        Example:
            >>> handler.prepare_request(
            ...     "A sunset over mountains",
            ...     num_outputs=4,
            ...     guidance_scale=7.5
            ... )
        """
        num_outputs = self.get_num_outputs(kwargs.get('num_outputs'))
        
        # Start with default params
        request_data = self.config.get('default_params', {}).copy()
        
        # Add prompt
        request_data['prompt'] = prompt
        
        # Handle optional image for hybrid models
        if kwargs.get('image_file') and self.config.get('ui_config', {}).get('show_image_upload'):
            request_data['image_file'] = kwargs['image_file']
            
        # Override with any custom params
        for key in ['negative_prompt', 'guidance_scale', 'num_inference_steps', 'strength', 'seed']:
            if key in kwargs and kwargs[key] is not None:
                request_data[key] = kwargs[key]
                
        logger.info(f"Prepared {self.name} request for {num_outputs} outputs")
        return request_data
    
    def process_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process response from text-to-image model.
        
        Handles various response formats from different APIs and normalizes
        them into a consistent structure.
        
        Args:
            response: API response which may contain:
                - 'image_url': Single image URL
                - 'images': List of image URLs
                
        Returns:
            Normalized list of results with URL and type
        """
        results = []
        
        # Handle different response formats
        if 'image_url' in response:
            results.append({
                'url': response['image_url'],
                'type': 'image'
            })
        elif 'images' in response:
            for img_url in response['images']:
                results.append({
                    'url': img_url,
                    'type': 'image'
                })
                
        return results
    
    def validate_inputs(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Validate inputs for text-to-image generation.
        
        Checks prompt requirements and optional image constraints.
        
        Args:
            prompt: Text prompt to validate
            **kwargs: May include 'image_file' for validation
            
        Returns:
            Validation result with any error messages
        """
        errors = {}
        validation = self.config.get('validation', {})
        
        # Validate prompt
        prompt_rules = validation.get('prompt', {})
        if prompt_rules.get('required', True) and not prompt:
            errors['prompt'] = 'Prompt is required'
        elif prompt:
            if len(prompt) < prompt_rules.get('min_length', 0):
                errors['prompt'] = f'Prompt must be at least {prompt_rules["min_length"]} characters'
            elif len(prompt) > prompt_rules.get('max_length', 1000):
                errors['prompt'] = f'Prompt must be less than {prompt_rules["max_length"]} characters'
                
        # Validate optional image
        if kwargs.get('image_file'):
            image_rules = validation.get('image', {})
            # TODO: Add image format and size validation
            
        return {'valid': len(errors) == 0, 'errors': errors}


class ImageToVideoHandler(BaseModelHandler):
    """
    Handler for image-to-video models.
    
    Converts static images into short video clips. Models like Stable Video
    Diffusion fall into this category.
    """
    
    def prepare_request(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Prepare request for video generation from image.
        
        Args:
            prompt: Typically ignored for image-to-video models
            **kwargs: Required and optional parameters:
                - image_file: Source image (required)
                - motion_bucket_id: Controls amount of motion
                - cond_aug: Conditioning augmentation
                - fps: Frames per second for output video
                
        Returns:
            Request payload for video generation
            
        Raises:
            ValueError: If image_file is not provided
        """
        # Video models typically don't need prompts
        request_data = self.config.get('default_params', {}).copy()
        
        # Image is required
        if not kwargs.get('image_file'):
            raise ValueError('Image file is required for video generation')
            
        request_data['image_file'] = kwargs['image_file']
        
        # Add video-specific params
        for param in ['motion_bucket_id', 'cond_aug', 'fps']:
            if param in kwargs and kwargs[param] is not None:
                request_data[param] = kwargs[param]
                
        logger.info(f"Prepared {self.name} video generation request")
        return request_data
    
    def process_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process response from video generation model.
        
        Args:
            response: May contain 'video_url' or nested 'video' object
            
        Returns:
            List with single video result
        """
        results = []
        
        if 'video_url' in response:
            results.append({
                'url': response['video_url'],
                'type': 'video'
            })
        elif 'video' in response and isinstance(response['video'], dict):
            video_url = response['video'].get('url')
            if video_url:
                results.append({
                    'url': video_url,
                    'type': 'video'
                })
                
        return results
    
    def validate_inputs(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Validate inputs for video generation.
        
        Ensures required image is provided.
        
        Args:
            prompt: Ignored for video generation
            **kwargs: Must include 'image_file'
            
        Returns:
            Validation result
        """
        errors = {}
        validation = self.config.get('validation', {})
        
        # Image is required for video generation
        image_rules = validation.get('image', {})
        if not kwargs.get('image_file'):
            errors['image'] = 'Image is required for video generation'
            
        return {'valid': len(errors) == 0, 'errors': errors}


class InpaintingHandler(BaseModelHandler):
    """
    Handler for inpainting/outpainting models.
    
    These models fill or extend parts of an image based on a mask.
    Examples include FLUX Pro Fill.
    """
    
    def prepare_request(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Prepare request for inpainting operation.
        
        Args:
            prompt: Description of what to generate in masked areas
            **kwargs: Required parameters:
                - image_file: Base image to inpaint
                - mask_file: Mask indicating areas to fill
                
        Returns:
            Request payload for inpainting
            
        Raises:
            ValueError: If image_file or mask_file is missing
        """
        request_data = self.config.get('default_params', {}).copy()
        
        # All three are required: prompt, image, and mask
        request_data['prompt'] = prompt
        
        if not kwargs.get('image_file'):
            raise ValueError('Image file is required for inpainting')
        if not kwargs.get('mask_file'):
            raise ValueError('Mask file is required for inpainting')
            
        request_data['image_file'] = kwargs['image_file']
        request_data['mask_file'] = kwargs['mask_file']
        
        logger.info(f"Prepared {self.name} inpainting request")
        return request_data
    
    def process_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process response from inpainting model.
        
        Args:
            response: Should contain 'image_url' with the result
            
        Returns:
            List with single inpainted image result
        """
        results = []
        
        if 'image_url' in response:
            results.append({
                'url': response['image_url'],
                'type': 'image'
            })
            
        return results
    
    def validate_inputs(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Validate inputs for inpainting.
        
        Ensures all required inputs (prompt, image, mask) are provided.
        
        Args:
            prompt: Text description to validate
            **kwargs: Must include 'image_file' and 'mask_file'
            
        Returns:
            Validation result with any errors
        """
        errors = {}
        validation = self.config.get('validation', {})
        
        # Validate prompt
        prompt_rules = validation.get('prompt', {})
        if prompt_rules.get('required', True) and not prompt:
            errors['prompt'] = 'Prompt is required'
            
        # Validate image
        if not kwargs.get('image_file'):
            errors['image'] = 'Image is required for inpainting'
            
        # Validate mask
        if not kwargs.get('mask_file'):
            errors['mask'] = 'Mask is required for inpainting'
            
        return {'valid': len(errors) == 0, 'errors': errors}


def create_model_handler(model_config: Dict[str, Any]) -> BaseModelHandler:
    """
    Factory function to create appropriate handler based on model type.
    
    Args:
        model_config: Model configuration dictionary with 'type' key
        
    Returns:
        Instance of appropriate handler class
        
    Example:
        >>> config = {'type': 'image-to-video', ...}
        >>> handler = create_model_handler(config)
        >>> isinstance(handler, ImageToVideoHandler)
        True
    """
    model_type = model_config.get('type', 'text-to-image')
    
    if model_type == 'image-to-video':
        return ImageToVideoHandler(model_config)
    elif model_type == 'inpainting':
        return InpaintingHandler(model_config)
    else:  # Default to text-to-image
        return TextToImageHandler(model_config)


class ModelHandlerRegistry:
    """
    Registry for managing model handler instances.
    
    Provides centralized access to all model handlers and handles
    their initialization from configuration.
    
    Attributes:
        _handlers: Dictionary mapping model IDs to handler instances
    """
    
    def __init__(self):
        """Initialize empty handler registry."""
        self._handlers: Dict[str, BaseModelHandler] = {}
        
    def register(self, model_id: str, handler: BaseModelHandler) -> None:
        """
        Register a handler for a model.
        
        Args:
            model_id: Unique identifier for the model
            handler: Handler instance for the model
        """
        self._handlers[model_id] = handler
        
    def get_handler(self, model_id: str) -> Optional[BaseModelHandler]:
        """
        Get handler for a specific model.
        
        Args:
            model_id: Model identifier to look up
            
        Returns:
            Handler instance or None if not found
        """
        return self._handlers.get(model_id)
        
    def initialize_from_config(self, model_configs: Dict[str, Dict[str, Any]]) -> None:
        """
        Initialize all handlers from configuration dictionary.
        
        Args:
            model_configs: Dictionary mapping model IDs to their configurations
            
        Example:
            >>> registry.initialize_from_config(MODEL_CONFIGURATIONS)
        """
        for model_id, config in model_configs.items():
            handler = create_model_handler(config)
            self.register(model_id, handler)
            
        logger.info(f"Initialized {len(self._handlers)} model handlers")


# Global registry instance for application-wide access
handler_registry = ModelHandlerRegistry() 