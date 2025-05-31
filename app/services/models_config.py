"""
Model Configuration System for AI Image Generator
=================================================

This module contains the centralized configuration for all AI image generation models.
Each model configuration defines:
- API endpoints and authentication methods
- UI behavior and requirements
- Validation rules
- Default parameters
- Output specifications

Configuration Structure:
-----------------------
Each model configuration is a dictionary with the following keys:

- name (str): Display name of the model
- endpoint (str): API endpoint for the model
- type (str): Model type ('text-to-image', 'image-to-video', 'inpainting', 'hybrid')
- output_type (str, optional): Output type ('image' or 'video'), defaults to 'image'
- description (str): Short description for UI display
- use_rest_api (bool, optional): Whether to use REST API directly
- default_num_outputs (int): Default number of outputs to generate
- max_outputs (int): Maximum allowed outputs
- ui_config (dict): UI behavior configuration
- default_params (dict): Default API parameters
- param_config (dict, optional): Dynamic parameter UI configuration
- validation (dict): Input validation rules

Example Usage:
--------------
    # Get configuration for a specific model
    flux_config = get_model_config('flux')
    
    # Get UI configuration
    ui_config = get_ui_config('flux')
    if ui_config['show_image_upload']:
        # Enable image upload in UI
        
    # Get validation rules
    rules = get_validation_rules('flux')
    if rules['prompt']['required']:
        # Validate prompt is provided

Author: AI Image Generator Team
Last Updated: 2024
"""

from typing import Dict, Any, Optional, List, Tuple

# Type aliases for clarity
ModelConfig = Dict[str, Any]
UIConfig = Dict[str, Any]
ValidationRules = Dict[str, Dict[str, Any]]
ParamConfig = Dict[str, Dict[str, Any]]

# Model configuration with all behaviors and requirements centralized
MODEL_CONFIGURATIONS: Dict[str, ModelConfig] = {
    'flux': {
        'name': 'FLUX.1 [dev]',
        'endpoint': 'fal-ai/flux',
        'type': 'text-to-image',
        'description': 'High-quality text-to-image generation',
        
        # Generation behavior
        'default_num_outputs': 4,
        'max_outputs': 4,
        
        # UI Configuration
        'ui_config': {
            'show_prompt': True,
            'prompt_required': True,
            'show_image_upload': True,
            'image_required': False,
            'show_mask_upload': False,
            'show_params': False,
            'button_text': 'Generate 4 Images'
        },
        
        # API Parameters
        'default_params': {
            'num_images': 4,
            'image_size': '1024x1024',
            'num_inference_steps': 30
        },
        
        # Validation rules
        'validation': {
            'prompt': {
                'required': True,
                'min_length': 3,
                'max_length': 1000
            },
            'image': {
                'required': False,
                'formats': ['jpg', 'jpeg', 'png', 'webp'],
                'max_size_mb': 10
            }
        }
    },
    
    'recraft': {
        'name': 'Recraft V3',
        'endpoint': 'fal-ai/recraft-v3',
        'type': 'text-to-image',
        'description': 'Vector illustration generation',
        
        # Generation behavior
        'default_num_outputs': 1,  # Limited due to timeouts
        'max_outputs': 2,
        
        # UI Configuration
        'ui_config': {
            'show_prompt': True,
            'prompt_required': True,
            'show_image_upload': False,
            'image_required': False,
            'show_mask_upload': False,
            'show_params': False,
            'button_text': 'Generate Vector Art'
        },
        
        # API Parameters - Fixed to use correct Recraft V3 style parameter
        'default_params': {
            'style': 'vector_illustration',
            'image_size': 'square_hd'
        },
        
        # Validation rules
        'validation': {
            'prompt': {
                'required': True,
                'min_length': 3,
                'max_length': 500
            }
        },
        
        # Detailed information
        'detailed_info': {
            'what_is': '''Recraft V3 is a state-of-the-art vector illustration model that creates clean, scalable artwork.
            
Key Features:
• Vector-based illustrations (SVG-style)
• Flat design aesthetic with no backgrounds
• Perfect for logos, icons, and illustrations
• Consistent style and color palettes''',
            
            'use_cases': '''Perfect for:
• Logo design and branding
• Web illustrations and icons
• Marketing materials and posters
• Children's book illustrations
• Technical diagrams and infographics''',
            
            'tips': '''For best results:
• Use descriptive terms like "flat vector illustration"
• Specify "no background", "minimalist", "simple lines"
• Include color preferences like "pastel colors" or "monochrome"
• Mention style keywords like "SVG-style", "clean design"
• Avoid photorealistic terms like "photography" or "realistic"'''
        }
    },
    
    'stable_video': {
        'name': 'Stable Video Diffusion',
        'endpoint': 'fal-ai/stable-video',
        'type': 'image-to-video',
        'output_type': 'video',
        'description': 'Transform images into short video clips',
        
        # Generation behavior
        'default_num_outputs': 1,
        'max_outputs': 1,
        
        # UI Configuration
        'ui_config': {
            'show_prompt': False,
            'prompt_required': False,
            'show_image_upload': True,
            'image_required': True,
            'show_mask_upload': False,
            'show_params': True,  # Show video-specific params
            'button_text': 'Generate Video'
        },
        
        # API Parameters
        'default_params': {
            'motion_bucket_id': 127,
            'cond_aug': 0.02,
            'fps': 10
        },
        
        # Video-specific parameters UI
        'param_config': {
            'motion_bucket_id': {
                'type': 'slider',
                'min': 1,
                'max': 255,
                'default': 127,
                'label': 'Motion Amount'
            },
            'fps': {
                'type': 'select',
                'options': [6, 8, 10, 12, 14],
                'default': 10,
                'label': 'Frames Per Second'
            }
        },
        
        # Validation rules
        'validation': {
            'image': {
                'required': True,
                'formats': ['jpg', 'jpeg', 'png'],
                'max_size_mb': 5,
                'min_dimensions': [256, 256],
                'max_dimensions': [1024, 1024]
            }
        }
    },
    
    'flux_pro': {
        'name': 'FLUX.1 [pro] Fill',
        'endpoint': 'fal-ai/flux-pro/v1/fill',
        'type': 'inpainting',
        'description': 'Advanced inpainting with mask support',
        'use_rest_api': True,
        'api_format': 'flux-pro-fill',
        
        # Generation behavior
        'default_num_outputs': 1,
        'max_outputs': 1,
        
        # UI Configuration
        'ui_config': {
            'show_prompt': True,
            'prompt_required': True,
            'show_image_upload': True,
            'image_required': True,
            'show_mask_upload': True,
            'mask_required': True,
            'show_params': False,
            'button_text': 'Generate Fill'
        },
        
        # API Parameters
        'default_params': {
            'num_images': 1,
            'safety_tolerance': '2',
            'output_format': 'jpeg',
            'sync_mode': True
        },
        
        # Validation rules
        'validation': {
            'prompt': {
                'required': True,
                'min_length': 3,
                'max_length': 500
            },
            'image': {
                'required': True,
                'formats': ['jpg', 'jpeg', 'png'],
                'max_size_mb': 5
            },
            'mask': {
                'required': True,
                'formats': ['jpg', 'jpeg', 'png'],
                'max_size_mb': 5,
                'must_match_image_dimensions': True
            }
        }
    },
    
    'stable_diffusion': {
        'name': 'Stable Diffusion V3',
        'endpoint': 'fal-ai/stable-diffusion-v3-medium',
        'type': 'hybrid',
        'description': 'Versatile text-to-image with advanced parameters',
        
        # Generation behavior
        'default_num_outputs': 4,
        'max_outputs': 4,
        
        # UI Configuration
        'ui_config': {
            'show_prompt': True,
            'prompt_required': True,
            'show_image_upload': True,
            'image_required': False,
            'show_mask_upload': False,
            'show_params': True,
            'show_advanced_params': True,
            'button_text': 'Generate 4 Images'
        },
        
        # API Parameters
        'default_params': {
            'num_inference_steps': 30,
            'guidance_scale': 7.5,
            'negative_prompt': '',
            'strength': 0.75,
            'seed': None,
            'width': 1024,
            'height': 1024
        },
        
        # Advanced parameters UI configuration
        'param_config': {
            'negative_prompt': {
                'type': 'textarea',
                'placeholder': "Things you don't want in the image",
                'label': 'Negative Prompt'
            },
            'strength': {
                'type': 'slider',
                'min': 0,
                'max': 1,
                'step': 0.05,
                'default': 0.75,
                'label': 'Image Influence Strength',
                'show_when': 'image_uploaded'
            },
            'guidance_scale': {
                'type': 'slider',
                'min': 1,
                'max': 20,
                'step': 0.5,
                'default': 7.5,
                'label': 'Guidance Scale'
            },
            'num_inference_steps': {
                'type': 'slider',
                'min': 10,
                'max': 50,
                'step': 1,
                'default': 30,
                'label': 'Quality Steps'
            },
            'seed': {
                'type': 'number',
                'placeholder': 'Random seed for reproducibility',
                'label': 'Seed (Optional)'
            }
        },
        
        # Validation rules
        'validation': {
            'prompt': {
                'required': True,
                'min_length': 3,
                'max_length': 1000
            },
            'image': {
                'required': False,
                'formats': ['jpg', 'jpeg', 'png', 'webp'],
                'max_size_mb': 10
            }
        }
    }
}

# Helper functions to work with configurations
def get_model_config(model_id: str) -> ModelConfig:
    """
    Get complete configuration for a specific model.
    
    Args:
        model_id: The unique identifier of the model (e.g., 'flux', 'stable_diffusion')
        
    Returns:
        Dictionary containing the complete model configuration, or empty dict if not found
        
    Example:
        >>> config = get_model_config('flux')
        >>> print(config['name'])  # 'FLUX.1 [dev]'
    """
    return MODEL_CONFIGURATIONS.get(model_id, {})


def get_ui_config(model_id: str) -> UIConfig:
    """
    Get UI configuration for a model.
    
    The UI configuration determines:
    - Which form elements to show/hide
    - Required vs optional inputs
    - Button text
    - Parameter sections visibility
    
    Args:
        model_id: The unique identifier of the model
        
    Returns:
        Dictionary containing UI configuration settings
        
    Example:
        >>> ui_config = get_ui_config('stable_video')
        >>> if ui_config['show_prompt']:
        ...     # Show prompt textarea
    """
    return get_model_config(model_id).get('ui_config', {})


def get_validation_rules(model_id: str) -> ValidationRules:
    """
    Get validation rules for a model's inputs.
    
    Validation rules define constraints for each input type:
    - Required/optional status
    - Min/max lengths for text
    - Allowed file formats
    - File size limits
    - Dimension constraints
    
    Args:
        model_id: The unique identifier of the model
        
    Returns:
        Dictionary mapping input types to their validation rules
        
    Example:
        >>> rules = get_validation_rules('flux')
        >>> prompt_rules = rules.get('prompt', {})
        >>> if prompt_rules.get('required'):
        ...     # Validate prompt exists
    """
    return get_model_config(model_id).get('validation', {})


def get_default_params(model_id: str) -> Dict[str, Any]:
    """
    Get default API parameters for a model.
    
    These parameters are sent with every API request unless overridden.
    
    Args:
        model_id: The unique identifier of the model
        
    Returns:
        Dictionary of default parameter values
        
    Example:
        >>> params = get_default_params('stable_diffusion')
        >>> print(params['num_inference_steps'])  # 30
    """
    return get_model_config(model_id).get('default_params', {})


def get_param_config(model_id: str) -> ParamConfig:
    """
    Get parameter UI configuration for dynamic form generation.
    
    This configuration defines how to render parameter inputs:
    - Input type (slider, select, textarea, number)
    - Min/max values and steps
    - Labels and placeholders
    - Conditional visibility rules
    
    Args:
        model_id: The unique identifier of the model
        
    Returns:
        Dictionary mapping parameter names to their UI configuration
        
    Example:
        >>> param_config = get_param_config('stable_video')
        >>> motion_config = param_config['motion_bucket_id']
        >>> # Render slider with min=1, max=255
    """
    return get_model_config(model_id).get('param_config', {})


def should_show_param(model_id: str, param_name: str, context: Optional[Dict[str, Any]] = None) -> bool:
    """
    Check if a parameter should be shown based on current context.
    
    Some parameters have conditional visibility based on other inputs or state.
    
    Args:
        model_id: The unique identifier of the model
        param_name: Name of the parameter to check
        context: Optional context dictionary with current state (e.g., {'has_image': True})
        
    Returns:
        True if the parameter should be shown, False otherwise
        
    Example:
        >>> # Show 'strength' parameter only when image is uploaded
        >>> context = {'has_image': True}
        >>> if should_show_param('stable_diffusion', 'strength', context):
        ...     # Show strength slider
    """
    param_config = get_param_config(model_id)
    param_info = param_config.get(param_name, {})
    
    show_when = param_info.get('show_when')
    if not show_when:
        return True
        
    # Example: show 'strength' only when image is uploaded
    if show_when == 'image_uploaded' and context:
        return context.get('has_image', False)
    
    return True


def get_models_by_type(model_type: str) -> List[Tuple[str, ModelConfig]]:
    """
    Get all models of a specific type.
    
    Args:
        model_type: The type to filter by ('text-to-image', 'image-to-video', etc.)
        
    Returns:
        List of tuples containing (model_id, config) for matching models
        
    Example:
        >>> video_models = get_models_by_type('image-to-video')
        >>> for model_id, config in video_models:
        ...     print(f"{model_id}: {config['name']}")
    """
    return [
        (model_id, config) 
        for model_id, config in MODEL_CONFIGURATIONS.items() 
        if config.get('type') == model_type
    ]


def get_models_with_capability(capability: str) -> List[Tuple[str, ModelConfig]]:
    """
    Get all models that have a specific capability.
    
    Args:
        capability: The capability to check for (e.g., 'supports_image_input', 'use_rest_api')
        
    Returns:
        List of tuples containing (model_id, config) for models with the capability
        
    Example:
        >>> # Get all models that support image input
        >>> image_models = get_models_with_capability('supports_image_input')
    """
    results = []
    for model_id, config in MODEL_CONFIGURATIONS.items():
        # Check in main config
        if config.get(capability):
            results.append((model_id, config))
        # Also check in ui_config for UI-related capabilities
        elif config.get('ui_config', {}).get(capability):
            results.append((model_id, config))
    return results 