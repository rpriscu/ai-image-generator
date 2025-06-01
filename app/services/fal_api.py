"""
Service to interact with the fal.ai API for image generation.
Handles different model types and authentication methods.
"""
import requests
from PIL import Image
import io
import base64
import json
from flask import current_app
import logging
import os
import datetime
import secrets
import hashlib
from app.services.models_config import MODEL_CONFIGURATIONS as AVAILABLE_MODELS
from app.services.image_processor import ImageProcessor
from app.services.url_shortener import URLShortener

logger = logging.getLogger(__name__)

# Constants for data URI prefixes
DATA_URI_PREFIX_JPEG = "data:image/jpeg;base64,"
DATA_URI_PREFIX_PNG = "data:image/png;base64,"
STATIC_GENERATED_PATH = "/static/generated/"

class FalApiService:
    """Service to interact with the fal.ai API for image generation"""
    
    def __init__(self):
        self.api_key = None
        self.base_url = None
    
    def init_app(self, app):
        """Initialize the service with Flask app config"""
        self.api_key = app.config.get('FAL_KEY')
        self.base_url = app.config.get('FAL_API_BASE_URL', 'https://fal.run')
        
        # Initialize URL cache for video URLs
        if not hasattr(app, 'url_cache'):
            app.url_cache = {}
    
    def shorten_url(self, url):
        """
        Create a shortened version of a long URL using the URLShortener service.
        
        Args:
            url (str): The long URL to shorten
            
        Returns:
            str: The shortened URL or the original if it's already short enough
        """
        return URLShortener.shorten_url(url)
    
    def generate_image(self, prompt, model, image_file=None, mask_file=None):
        """
        Generate an image using the specified fal.ai model.
        
        Args:
            prompt (str): The text prompt for image generation
            model (dict): The model configuration
            image_file (FileStorage, optional): The reference image file for image-to-image models
            mask_file (FileStorage, optional): The mask image file for inpainting/outpainting models like FLUX.1 [pro] Fill
        
        Returns:
            dict: The generated image data
        """
        if not self.api_key:
            self.api_key = current_app.config.get('FAL_KEY')
            self.base_url = current_app.config.get('FAL_API_BASE_URL', 'https://fal.run')
        
        # Check which API method to use based on model configuration
        if model.get('use_rest_api', False):
            return self._fallback_fal_client(prompt, model, image_file, mask_file)
        elif model.get('use_fal_client', False):
            return self._generate_with_fal_client(prompt, model)
        else:
            return self._generate_with_rest_api(prompt, model, image_file, mask_file)
    
    def generate_content(self, prompt, model, image_file=None, mask_file=None):
        """
        Generate content (image or video) using the specified fal.ai model.
        
        Args:
            prompt (str): The text prompt for content generation
            model (dict): The model configuration
            image_file (FileStorage, optional): The reference image file for image-to-image or image-to-video models
            mask_file (FileStorage, optional): The mask image file for inpainting/outpainting models
        
        Returns:
            dict: The generated content data with appropriate URL
        """
        if not self.api_key:
            self.api_key = current_app.config.get('FAL_KEY')
            self.base_url = current_app.config.get('FAL_API_BASE_URL', 'https://fal.run')
        
        # Check if this is a video model
        is_video_model = model.get('output_type') == 'video'
        logger.info(f"Generating content with model: {model.get('name')}, type: {model.get('type')}, output_type: {model.get('output_type')}")
        
        # For image-to-video models, ensure we have an image
        if model.get('type') == 'image-to-video' and not image_file:
            logger.error("Image-to-video model requires an image file")
            return {'error': 'Image file is required for video generation'}
        
        # Check which API method to use based on model configuration
        if model.get('use_rest_api', False):
            logger.info("Using REST API fallback method")
            result = self._fallback_fal_client(prompt, model, image_file, mask_file)
        elif model.get('use_fal_client', False):
            logger.info("Using fal_client library")
            result = self._generate_with_fal_client(prompt, model, image_file)
        else:
            logger.info("Using standard REST API")
            result = self._generate_with_rest_api(prompt, model, image_file, mask_file)
        
        # Process result based on content type
        if is_video_model and 'video_url' in result:
            logger.info(f"Generated video: {result['video_url'][:60]}...")
            
            # Shorten the video URL if it's too long
            video_url = self.shorten_url(result['video_url'])
            return {'video_url': video_url}
        elif is_video_model and 'video' in result:
            # Get video URL from the video object
            video_url = result['video'].get('url')
            if video_url:
                logger.info(f"Extracted video URL from result: {video_url[:60]}...")
                return {'video_url': video_url}
            else:
                logger.error("Video URL not found in response")
                return {'error': 'No video URL found in response'}
        elif 'image_url' in result:
            logger.info(f"Received image URL result: {result['image_url'][:60]}...")
            return result
        else:
            logger.error(f"Unexpected response format: {result}")
            return {'error': 'Unexpected response format'}
    
    def _extract_image_url(self, result):
        """
        Extract image URL from API response in a consistent way.
        Handles different response formats from various models.
        
        Args:
            result (dict): The API response
            
        Returns:
            str: The image URL if found
            
        Raises:
            Exception: If no image URL is found
        """
        logger.debug(f"Extracting image URL from result: {json.dumps({k: v for k, v in result.items() if k not in ['images'] or not isinstance(v, list)})}")
        
        def save_base64_image(image_data_uri):
            """Save a base64 image and return its URL path"""
            # Check if it's a base64 data URI
            if not image_data_uri.startswith('data:image/'):
                return image_data_uri
                
            try:
                # Create directory for saved images
                static_folder = current_app.static_folder
                if not static_folder:
                    static_folder = os.path.join(os.path.dirname(current_app.root_path), 'static')
                    os.makedirs(static_folder, exist_ok=True)
                
                static_img_dir = os.path.join(static_folder, 'generated')
                
                # Use ImageProcessor to save the image
                filepath = ImageProcessor.save_base64_image(
                    image_data_uri,
                    static_img_dir,
                    prefix='img'
                )
                
                # Convert absolute path to URL path
                image_url = f"{STATIC_GENERATED_PATH}{os.path.basename(filepath)}"
                logger.info(f"Saved base64 image to: {image_url}")
                return image_url
            except Exception as e:
                logger.error(f"Failed to save base64 image: {str(e)}")
                return image_data_uri
        
        # Check for images in various response formats
        if 'images' in result and result['images']:
            image_data = result['images'][0]
            if isinstance(image_data, str):
                return save_base64_image(image_data)
            elif isinstance(image_data, dict) and 'url' in image_data:
                return save_base64_image(image_data['url'])
        
        # Check for single 'image' field
        elif 'image' in result:
            image_data = result['image']
            if isinstance(image_data, str):
                return save_base64_image(image_data)
            elif isinstance(image_data, dict) and 'url' in image_data:
                return save_base64_image(image_data['url'])
        
        # Generic check for any field with image URL
        for key, value in result.items():
            if isinstance(value, str) and (
                value.startswith(('http://', 'https://', 'data:image/')) and
                (any(ext in value.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']) or 
                value.startswith('data:image/'))
            ):
                logger.info(f"Found image URL in field '{key}': {value[:60]}...")
                return save_base64_image(value)
        
        # No image URL found
        logger.error(f"Unexpected response structure: {result}")
        raise Exception('No image URL found in response')
    
    def _generate_with_fal_client(self, prompt, model, image_file=None):
        """Generate content using the fal_client library"""
        logger.info(f"Generating with fal_client: {model['endpoint']}")
        
        try:
            # Set environment variable first, before importing fal_client
            import os
            
            # fal_client looks for FAL_KEY environment variable
            if self.api_key:
                # The key MUST be named FAL_KEY for fal_client to work
                os.environ['FAL_KEY'] = self.api_key
                logger.info(f"Set FAL_KEY environment variable for fal_client using API key from config")
            else:
                raise Exception("No API key available. Please check your configuration.")
                
            # Now import fal_client after setting the environment variable
            import fal_client
            
            # Define callback for logs
            def on_queue_update(update):
                if isinstance(update, fal_client.InProgress):
                    for log in update.logs:
                        logger.info(f"FAL client log: {log['message']}")
            
            # Prepare arguments based on model type
            arguments = {}
            
            # Only add prompt if the model requires it
            if not model.get('requires_prompt', True) == False:
                arguments["prompt"] = prompt
            
            # Process image file for image-to-image or image-to-video models
            if image_file and (model.get('type') == 'image-to-image' or 
                              model.get('type') == 'hybrid' or 
                              model.get('type') == 'image-to-video' or
                              model.get('supports_image_input', False)):
                try:
                    # Process the image
                    image = Image.open(image_file)
                    logger.info(f"Original image size: {image.size}, mode: {image.mode}")
                    
                    # Resize if needed
                    max_size = 1024
                    if max(image.size) > max_size:
                        ratio = max_size / max(image.size)
                        new_size = tuple(int(dim * ratio) for dim in image.size)
                        image = image.resize(new_size, Image.Resampling.LANCZOS)
                        logger.info(f"Resized image to: {new_size}")
                    
                    # Convert to RGB if needed
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                        logger.info(f"Converted image to RGB mode")
                    
                    # Save as base64
                    buffered = io.BytesIO()
                    image.save(buffered, format="PNG", quality=95)
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    
                    # For video models like Stable Video Diffusion
                    if model.get('type') == 'image-to-video':
                        arguments["input"] = {
                            "image_url": f"{DATA_URI_PREFIX_PNG}{img_str}"
                        }
                        logger.info("Added image as input for image-to-video model")
                    else:
                        # For hybrid models
                        arguments["image_url"] = f"{DATA_URI_PREFIX_PNG}{img_str}"
                        logger.info("Added image_url to arguments")
                        
                except Exception as e:
                    logger.error(f"Error processing image file: {str(e)}")
                    raise Exception(f"Failed to process image file: {str(e)}")
            
            # Add model-specific parameters if they exist
            if 'params' in model:
                if model.get('type') == 'image-to-video':
                    # For video models, params need to be in the input object
                    if "input" not in arguments:
                        arguments["input"] = {}
                    arguments["input"].update(model['params'])
                else:
                    # For other models, add params directly
                    arguments.update(model['params'])
            
            # Call the FAL client API
            logger.debug(f"FAL client arguments: {json.dumps(arguments, indent=2)}")
            result = fal_client.subscribe(
                model['endpoint'],
                arguments=arguments,
                with_logs=True,
                on_queue_update=on_queue_update,
            )
            
            logger.debug(f"FAL client result: {result}")
            
            # Check if result is a Dictionary (for newer fal_client)
            if hasattr(result, 'get'):
                # Process result based on model type
                if model.get('output_type') == 'video' and 'video' in result:
                    # For video models
                    video_url = result['video'].get('url')
                    logger.info(f"Generated video: {video_url[:60]}...")
                    return {'video_url': video_url}
                else:
                    # For image models
                    # Extract image URL from result - structure depends on model
                    image_url = self._extract_image_url(result)
                    logger.info(f"Generated image: {image_url[:60]}...")
                    return {'image_url': image_url}
            else:
                # Legacy handling for older fal_client versions
                logger.warning("Using legacy result processing for older fal_client")
                if hasattr(result, 'images') and result.images:
                    image_url = result.images[0]
                    logger.info(f"Generated image (legacy): {image_url[:60]}...")
                    return {'image_url': image_url}
                elif hasattr(result, 'video') and result.video:
                    video_url = result.video.url
                    logger.info(f"Generated video (legacy): {video_url[:60]}...")
                    return {'video_url': video_url}
                else:
                    raise Exception("No image or video found in result")
                    
        except Exception as e:
            logger.exception(f"Error using fal_client: {str(e)}")
            raise Exception(f"Failed to generate with fal_client: {str(e)}")
    
    def _fallback_fal_client(self, prompt, model, image_file=None, mask_file=None):
        """Fallback method to call fal.ai API directly with REST API instead of fal_client"""
        logger.info(f"Using fallback method for {model['endpoint']}")
        
        # Helper method to parse response and get detailed error
        def parse_error_response(resp):
            error_msg = f"API request failed with status {resp.status_code}"
            try:
                error_data = resp.json()
                if 'error' in error_data:
                    error_msg = f"{error_msg}: {error_data['error']}"
                elif 'detail' in error_data:
                    if isinstance(error_data['detail'], list) and len(error_data['detail']) > 0:
                        error_details = error_data['detail'][0]
                        if 'msg' in error_details:
                            error_msg = f"{error_msg}: {error_details['msg']}"
                    elif isinstance(error_data['detail'], str):
                        error_msg = f"{error_msg}: {error_data['detail']}"
            except Exception as parse_err:
                logger.warning(f"Could not parse error response: {str(parse_err)}")
                try:
                    error_msg = f"{error_msg}: {resp.text}"
                except:
                    pass
            return error_msg
        
        # Helper function to make a request with given endpoint and payload
        def make_request(endpoint, payload):
            headers = {
                'Authorization': f'Key {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            logger.info(f"Making REST API request to: {self.base_url}/{endpoint}")
            logger.debug(f"With payload: {json.dumps({k: '...' if k in ['image', 'image_url', 'reference_image_url', 'ip_adapters', 'mask_url'] and isinstance(payload[k], (str, list)) and ((isinstance(payload[k], str) and len(payload[k]) > 100) or isinstance(payload[k], list)) else payload[k] for k in payload}, indent=2)}")
            
            try:
                response = requests.post(
                    f'{self.base_url}/{endpoint}',
                    headers=headers,
                    json=payload,
                    timeout=60  # Longer timeout for Pro models
                )
                
                logger.info(f"Response status: {response.status_code}")
                
                # Log more detailed error information
                if not response.ok:
                    logger.error(f"Request failed with status {response.status_code}")
                    try:
                        error_data = response.json()
                        logger.error(f"Error response: {json.dumps(error_data, indent=2)}")
                    except:
                        logger.error(f"Error response (raw): {response.text}")
                
                logger.debug(f"Response content: {response.text}")
                
                return response
            except Exception as e:
                logger.error(f"Request failed: {str(e)}")
                return None
        
        # Try with the primary configuration
        try:
            # Check if model has a special API format
            api_format = model.get('api_format', None)
            
            # Base payload - this varies based on model type
            if api_format == 'flux-pro':
                # For FLUX Pro models, use this specific payload structure
                primary_payload = {
                    'prompt': prompt,
                    'model_version': model.get('params', {}).get('model_version', 'v1.1-ultra-finetuned'),
                    'image_size': model.get('params', {}).get('image_size', '1024x1024'),
                    'num_inference_steps': model.get('params', {}).get('num_inference_steps', 30),
                    'seed': 42  # Optional - provides reproducibility
                }
                
                # Handle file uploads for Pro models if provided
                if image_file:
                    primary_payload['image_file'] = image_file
                if mask_file:
                    primary_payload['mask_file'] = mask_file

                # For flux_pro (fill), convert files to data URIs and send as image_url/mask_url
                if api_format == 'flux-pro' and image_file and mask_file:
                    try:
                        logger.info("Processing image and mask for FLUX Pro Fill data URI format...")
                        image_file.seek(0)
                        img_stream = io.BytesIO(image_file.read())
                        base64_image = base64.b64encode(img_stream.getvalue()).decode('utf-8')
                        primary_payload['image_url'] = f"{DATA_URI_PREFIX_PNG}{base64_image}" # Use PNG for lossless mask compatibility
                        logger.info(f"Prepared image_url for FLUX Pro (length: {len(primary_payload['image_url'])})")

                        mask_file.seek(0)
                        mask_stream = io.BytesIO(mask_file.read())
                        base64_mask = base64.b64encode(mask_stream.getvalue()).decode('utf-8')
                        primary_payload['mask_url'] = f"{DATA_URI_PREFIX_PNG}{base64_mask}"
                        logger.info(f"Prepared mask_url for FLUX Pro (length: {len(primary_payload['mask_url'])})")

                        # Remove file objects if they were added
                        primary_payload.pop('image_file', None)
                        primary_payload.pop('mask_file', None)
                        logger.info("Removed file objects, using data URIs for FLUX Pro Fill.")
                    except Exception as e:
                        logger.error(f"Error converting images to data URIs for FLUX Pro: {str(e)}")
                        raise Exception(f"Failed to prepare images for FLUX Pro: {str(e)}")
                
                # For FLUX Pro, the endpoint is simply 'flux'
                primary_endpoint = model['endpoint']
            elif api_format == 'flux-pro-fill':
                # For FLUX Pro Fill models, use the specific payload structure
                primary_payload = {
                    'prompt': prompt,
                    'num_images': model.get('params', {}).get('num_images', 1),
                    'safety_tolerance': model.get('params', {}).get('safety_tolerance', '2'),
                    'output_format': model.get('params', {}).get('output_format', 'jpeg'),
                    'sync_mode': True  # Ensures we wait for the result
                }
                
                # Both image_url and mask_url are required for this model
                if image_file and mask_file:
                    logger.info("Processing images for FLUX Pro Fill inpainting/outpainting")
                    
                    try:
                        # Use PIL to resize images to match each other
                        from PIL import Image
                        
                        # Process the main image
                        image_file.seek(0)
                        pil_image = Image.open(image_file)
                        image_size = pil_image.size
                        logger.info(f"Original image size: {image_size[0]}x{image_size[1]}")
                        
                        # Process the mask image and resize to match the main image if needed
                        mask_file.seek(0)
                        pil_mask = Image.open(mask_file)
                        mask_size = pil_mask.size
                        logger.info(f"Original mask size: {mask_size[0]}x{mask_size[1]}")
                        
                        # Resize mask to match image if dimensions don't match
                        if mask_size != image_size:
                            logger.info(f"Resizing mask to match image dimensions: {image_size[0]}x{image_size[1]}")
                            pil_mask = pil_mask.resize(image_size, Image.Resampling.LANCZOS)
                        
                        # Convert to RGB mode if needed
                        if pil_image.mode != 'RGB':
                            pil_image = pil_image.convert('RGB')
                        
                        # Ensure mask is grayscale
                        if pil_mask.mode != 'L' and pil_mask.mode != '1':
                            pil_mask = pil_mask.convert('L')
                        
                        # Save images to byte streams
                        img_stream = io.BytesIO()
                        pil_image.save(img_stream, format="JPEG", quality=95)
                        img_stream.seek(0)
                        base64_image = base64.b64encode(img_stream.getvalue()).decode('utf-8')
                        
                        mask_stream = io.BytesIO()
                        pil_mask.save(mask_stream, format="JPEG", quality=95)
                        mask_stream.seek(0)
                        base64_mask = base64.b64encode(mask_stream.getvalue()).decode('utf-8')
                        
                        # Use data URI format
                        primary_payload['image_url'] = f"{DATA_URI_PREFIX_JPEG}{base64_image}"
                        primary_payload['mask_url'] = f"{DATA_URI_PREFIX_JPEG}{base64_mask}"
                        
                        logger.info("Successfully processed image and mask for FLUX Pro Fill")
                        logger.debug(f"Payload keys: {list(primary_payload.keys())}")
                    except Exception as e:
                        logger.error(f"Error processing images for FLUX Pro Fill: {str(e)}")
                        logger.exception("Detailed error:")
                        raise Exception(f"Failed to process images: {str(e)}")
                else:
                    # FLUX Fill requires both image_url and mask_url
                    logger.error("FLUX Pro Fill requires both an image and a mask")
                    raise Exception("Missing required image or mask file for FLUX Pro Fill model")
                
                # Use the endpoint from the model config
                primary_endpoint = model['endpoint']
                
                # Log the full endpoint for debugging
                logger.info(f"Using endpoint: {primary_endpoint}")
            else:
                # Standard payload for other models
                primary_payload = {
                    'prompt': prompt
                }
                
                # Add model-specific parameters if they exist
                if 'params' in model:
                    primary_payload.update(model['params'])
                
                # Use rest_endpoint if defined in the model, otherwise use normal endpoint
                if 'rest_endpoint' in model:
                    primary_endpoint = model['rest_endpoint']
                else:
                    # Extract the model ID from the endpoint (e.g., "fal-ai/flux-pro/v1.1-ultra-finetuned")
                    endpoint_parts = model['endpoint'].split('/')
                    if len(endpoint_parts) >= 2:
                        # Reconstruct for REST API
                        primary_endpoint = '/'.join(endpoint_parts)
                    else:
                        primary_endpoint = model['endpoint']
            
            # Make the primary request
            response = make_request(primary_endpoint, primary_payload)
            
            if response and response.ok:
                result = response.json()
                logger.debug(f"Successful response: {json.dumps(result)}")
                try:
                    image_url = self._extract_image_url(result)
                    logger.info(f"Successfully extracted image URL: {image_url[:60]}...")
                    return {'image_url': image_url}
                except Exception as e:
                    logger.error(f"Error extracting image URL: {str(e)}")
                    logger.error(f"Unexpected response structure: {result}")
                    raise Exception('No image URL found in primary response')
            
            # If we get here, the primary request failed
            logger.info("Primary request failed, trying alternative formats...")
            
            # Check if the model has alternate formats to try
            alt_formats = model.get('alt_formats', [])
            if not alt_formats:
                # No alternative formats available, provide more detailed error info
                error_msg = "API request failed with no alternative formats available"
                if response:
                    try:
                        error_data = response.json()
                        if 'error' in error_data:
                            error_msg = f"API error: {error_data['error']}"
                        elif 'detail' in error_data:
                            error_msg = f"API error: {error_data['detail']}"
                        else:
                            error_msg = f"API error: {json.dumps(error_data)}"
                    except:
                        error_msg = f"API error: {response.text}"
                
                logger.error(error_msg)
                raise Exception(error_msg)
            
            # Try each alternative format
            for alt_format in alt_formats:
                alt_endpoint = alt_format.get('endpoint')
                alt_payload_template = alt_format.get('payload', {})
                
                # Replace any template variables in the payload
                alt_payload = {}
                for key, value in alt_payload_template.items():
                    if isinstance(value, str) and '{prompt}' in value:
                        alt_payload[key] = value.replace('{prompt}', prompt)
                    else:
                        alt_payload[key] = value
                
                # Process image file for alternative formats if supported
                if image_file and mask_file and api_format == 'flux-pro-fill':
                    try:
                        # Use PIL to resize images to match each other
                        from PIL import Image
                        
                        # Process the main image
                        image_file.seek(0)
                        pil_image = Image.open(image_file)
                        image_size = pil_image.size
                        logger.info(f"Alternative format - Original image size: {image_size[0]}x{image_size[1]}")
                        
                        # Process the mask image and resize to match the main image if needed
                        mask_file.seek(0)
                        pil_mask = Image.open(mask_file)
                        mask_size = pil_mask.size
                        logger.info(f"Alternative format - Original mask size: {mask_size[0]}x{mask_size[1]}")
                        
                        # Resize mask to match image if dimensions don't match
                        if mask_size != image_size:
                            logger.info(f"Alternative format - Resizing mask to match image dimensions: {image_size[0]}x{image_size[1]}")
                            pil_mask = pil_mask.resize(image_size, Image.Resampling.LANCZOS)
                        
                        # Convert to RGB mode if needed
                        if pil_image.mode != 'RGB':
                            pil_image = pil_image.convert('RGB')
                        
                        # Ensure mask is grayscale
                        if pil_mask.mode != 'L' and pil_mask.mode != '1':
                            pil_mask = pil_mask.convert('L')
                            
                        # Save images to byte streams
                        img_stream = io.BytesIO()
                        pil_image.save(img_stream, format="JPEG", quality=95)
                        img_stream.seek(0)
                        base64_image = base64.b64encode(img_stream.getvalue()).decode('utf-8')
                        img_data_uri = f"{DATA_URI_PREFIX_JPEG}{base64_image}"
                        
                        mask_stream = io.BytesIO()
                        pil_mask.save(mask_stream, format="JPEG", quality=95)
                        mask_stream.seek(0)
                        base64_mask = base64.b64encode(mask_stream.getvalue()).decode('utf-8')
                        mask_data_uri = f"{DATA_URI_PREFIX_JPEG}{base64_mask}"
                        
                        # Replace template variable if present
                        if 'image_url' in alt_payload and isinstance(alt_payload['image_url'], str) and '{image_url}' in alt_payload['image_url']:
                            alt_payload['image_url'] = img_data_uri
                        else:
                            alt_payload['image_url'] = img_data_uri
                        
                        # Replace template variable if present
                        if 'mask_url' in alt_payload and isinstance(alt_payload['mask_url'], str) and '{mask_url}' in alt_payload['mask_url']:
                            alt_payload['mask_url'] = mask_data_uri
                        else:
                            alt_payload['mask_url'] = mask_data_uri
                        
                        logger.info(f"Processed image and mask for alt format: {alt_endpoint}")
                    except Exception as e:
                        logger.warning(f"Failed to process image and mask for alt format: {str(e)}")
                elif image_file and model.get('supports_image_input', False):
                    try:
                        image_file.seek(0)  # Reset file pointer
                        img_stream = io.BytesIO(image_file.read())
                        base64_image = base64.b64encode(img_stream.getvalue()).decode('utf-8')
                        
                        # Add the image data in the format required by the alt endpoint
                        if 'flux' in alt_endpoint.lower():
                            alt_payload['ip_adapters'] = [{
                                "image_url": f"{DATA_URI_PREFIX_JPEG}{base64_image}",
                                "path": "h94/IP-Adapter",
                                "image_encoder_path": "openai/clip-vit-large-patch14",
                                "scale": 0.7
                            }]
                        else:
                            alt_payload['image'] = f"{DATA_URI_PREFIX_JPEG}{base64_image}"
                    except Exception as e:
                        logger.warning(f"Failed to process image for alt format: {str(e)}")
                
                logger.info(f"Trying alternative format with endpoint: {alt_endpoint}")
                response = make_request(alt_endpoint, alt_payload)
                
                if response and response.ok:
                    result = response.json()
                    try:
                        image_url = self._extract_image_url(result)
                        logger.info("Alternative format succeeded!")
                        return {'image_url': image_url}
                    except Exception:
                        continue
            
            # If we get here, all attempts failed
            error_msg = "All request formats failed. Please check your API key and model configuration."
            
            # Add more specific error message for common errors
            if response:
                try:
                    error_data = response.json()
                    if 'detail' in error_data:
                        detail = error_data['detail']
                        if isinstance(detail, str) and "Image and mask sizes do not match" in detail:
                            error_msg = "Error: Image and mask sizes do not match. The application attempted to resize them automatically but failed. Please ensure your mask image has the same dimensions as your reference image."
                        elif 'detail' in error_data:
                            error_msg = f"API error: {error_data['detail']}"
                except:
                    pass
                    
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except Exception as e:
            logger.exception(f"Fallback method failed: {str(e)}")
            raise Exception(f"Failed to generate image with Pro model: {str(e)}")
    
    def _generate_with_rest_api(self, prompt, model, image_file=None, mask_file=None):
        """Generate an image using the REST API"""
        logger.info(f"Generating with REST API: {model['endpoint']}")
        
        headers = {
            'Authorization': f'Key {self.api_key}',
            'Content-Type': 'application/json'
        }

        # Set timeout based on model - longer timeout for video models
        timeout = 120 if model.get('output_type') == 'video' else 60
        
        # For Recraft model, which can take longer than other models
        if 'recraft' in model.get('endpoint', '').lower():
            timeout = 120

        # Base payload
        payload = {}
        
        # Only add prompt if the model requires it
        if not model.get('requires_prompt', True) == False:
            payload['prompt'] = prompt

        # Add model-specific parameters if they exist
        if 'params' in model:
            # Filter out None values and empty strings
            params = {k: v for k, v in model['params'].items() if v is not None and v != ''}
            payload.update(params)
            logger.info(f"Added model params: {params}")

        # Handle image-to-image or image-to-video models
        if image_file and (model.get('type') in ['image-to-image', 'hybrid', 'image-to-video'] or model.get('supports_image_input', False)):
            try:
                logger.info(f"Processing image for {model['type']} model")
                image = Image.open(image_file)
                logger.info(f"Original image size: {image.size}, mode: {image.mode}")
                
                # Resize image if needed (maintain aspect ratio)
                max_size = 1024
                if max(image.size) > max_size:
                    ratio = max_size / max(image.size)
                    new_size = tuple(int(dim * ratio) for dim in image.size)
                    image = image.resize(new_size, Image.Resampling.LANCZOS)
                    logger.info(f"Resized image to: {new_size}")
                
                # Convert to RGB if needed
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                    logger.info(f"Converted image to RGB mode")
                
                buffered = io.BytesIO()
                image.save(buffered, format="PNG", quality=95)
                img_str = base64.b64encode(buffered.getvalue()).decode()
                
                # Special handling for FLUX models that require ip_adapters format
                if 'flux' in model['endpoint'].lower():
                    # FLUX models need a specific format with ip_adapters for reference images
                    payload['ip_adapters'] = [{
                        "image_url": f"{DATA_URI_PREFIX_JPEG}{img_str}",
                        "path": "h94/IP-Adapter",
                        "image_encoder_path": "openai/clip-vit-large-patch14",
                        "scale": 0.7
                    }]
                    logger.info(f"Added ip_adapters to payload for FLUX model (image length: {len(img_str)})")
                # Special handling for video models
                elif model.get('type') == 'image-to-video':
                    # Video models use flat structure, not nested input
                    payload['image_url'] = f"{DATA_URI_PREFIX_PNG}{img_str}"
                    logger.info(f"Added image_url to video model payload (length: {len(img_str)})")
                else:
                    # Standard image_url format for other models like Stable Diffusion
                    payload['image_url'] = f"{DATA_URI_PREFIX_PNG}{img_str}"
                    logger.info(f"Added image_url to payload (length: {len(img_str)})")
            except Exception as e:
                logger.error(f"Error processing image file: {str(e)}")
                return {'error': f"Failed to process image file: {str(e)}"}

        # Process mask file if provided (for inpainting models)
        if mask_file and model.get('endpoint') == 'fal-ai/flux-pro/v1/fill':
            try:
                logger.info("Processing mask file for inpainting model")
                mask = Image.open(mask_file)
                logger.info(f"Original mask size: {mask.size}, mode: {mask.mode}")
                
                # Resize mask if needed
                max_size = 1024
                if max(mask.size) > max_size:
                    ratio = max_size / max(mask.size)
                    new_size = tuple(int(dim * ratio) for dim in mask.size)
                    mask = mask.resize(new_size, Image.Resampling.LANCZOS)
                    logger.info(f"Resized mask to: {new_size}")
                
                # Convert to RGB if needed
                if mask.mode != 'RGB':
                    mask = mask.convert('RGB')
                    logger.info(f"Converted mask to RGB mode")
                
                mask_buffered = io.BytesIO()
                mask.save(mask_buffered, format="PNG", quality=95)
                mask_str = base64.b64encode(mask_buffered.getvalue()).decode()
                
                # Add mask to payload
                payload['mask_url'] = f"{DATA_URI_PREFIX_PNG}{mask_str}"
                logger.info(f"Added mask_url to payload (length: {len(mask_str)})")
            except Exception as e:
                logger.error(f"Error processing mask file: {str(e)}")
                return {'error': f"Failed to process mask file: {str(e)}"}

        # Helper function to make a request with given endpoint and payload
        def make_request(endpoint, payload):
            logger.info(f"Making REST API request to: {self.base_url}/{endpoint}")
            logger.debug(f"With payload: {json.dumps({k: '...' if k in ['image', 'image_url', 'reference_image_url', 'ip_adapters', 'mask_url', 'input'] and isinstance(payload[k], (str, list, dict)) and ((isinstance(payload[k], str) and len(payload[k]) > 100) or isinstance(payload[k], (list, dict))) else payload[k] for k in payload}, indent=2)}")
            
            try:
                response = requests.post(
                    f'{self.base_url}/{endpoint}',
                    headers=headers,
                    json=payload,
                    timeout=timeout  # Adjusted timeout
                )
                
                logger.info(f"Response status: {response.status_code}")
                
                # Log more detailed error information
                if not response.ok:
                    logger.error(f"Request failed with status {response.status_code}")
                    try:
                        error_data = response.json()
                        logger.error(f"Error response: {json.dumps(error_data, indent=2)}")
                    except:
                        logger.error(f"Error response (raw): {response.text}")
                
                logger.debug(f"Response content: {response.text}")
                
                return response
            except Exception as e:
                logger.error(f"Request failed: {str(e)}")
                return None

        # Make the primary request
        response = make_request(model['endpoint'], payload)
        
        if response and response.ok:
            result = response.json()
            logger.debug(f"Successful response: {json.dumps(result)}")
            
            # Process result based on model type
            if model.get('output_type') == 'video':
                # For video models
                try:
                    if 'video' in result and 'url' in result['video']:
                        video_url = result['video']['url']
                        logger.info(f"Generated video: {video_url[:60]}...")
                        return {'video_url': video_url}
                    else:
                        logger.error(f"No video URL found in response: {result}")
                        return {'error': 'No video URL found in response'}
                except Exception as e:
                    logger.error(f"Error extracting video URL: {str(e)}")
                    logger.error(f"Unexpected response structure: {result}")
                    return {'error': f'Error extracting video URL: {str(e)}'}
            else:
                # For image models
                try:
                    image_url = self._extract_image_url(result)
                    logger.info(f"Generated image: {image_url[:60]}...")
                    return {'image_url': image_url}
                except Exception as e:
                    logger.error(f"Error extracting image URL: {str(e)}")
                    logger.error(f"Unexpected response structure: {result}")
                    return {'error': f'Error extracting image URL: {str(e)}'}
        
        # If we get here, the request failed
        logger.error("Request failed, no valid response")
        error_msg = "Failed to generate content with the model"
        if response:
            try:
                error_data = response.json()
                if 'error' in error_data:
                    error_msg = error_data['error']
            except:
                if response.text:
                    error_msg = response.text
                else:
                    error_msg = f"Request failed with status {response.status_code}"
        
        return {'error': error_msg}

# Create an instance of the service
fal_api_service = FalApiService()

# Import models configuration from separate file
from app.services.models_config import MODEL_CONFIGURATIONS 