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

logger = logging.getLogger(__name__)

# Available models configuration
AVAILABLE_MODELS = {
    'flux': {
        'name': 'FLUX.1 [dev]',
        'endpoint': 'fal-ai/flux',
        'type': 'text-to-image'
    },
    'recraft': {
        'name': 'Recraft V3',
        'endpoint': 'fal-ai/recraft-v3',
        'type': 'text-to-image',
        'params': {
            'style': 'vector_illustration'
        }
    },
    'stable_diffusion': {
        'name': 'Stable Diffusion V3',
        'endpoint': 'fal-ai/stable-diffusion-v3-medium',
        'type': 'hybrid',
        'description': 'Creates detailed images with high fidelity. Supports both text prompts and image inputs.',
        'supports_image_input': True,
        'params': {
            'num_inference_steps': 30,
            'guidance_scale': 7.5,
            'negative_prompt': '',
            'strength': 0.75,
            'seed': None,
            'width': 1024,
            'height': 1024
        }
    }
}

class FalApiService:
    """Service to interact with the fal.ai API for image generation"""
    
    def __init__(self):
        self.api_key = None
        self.base_url = None
    
    def init_app(self, app):
        """Initialize the service with Flask app config"""
        self.api_key = app.config.get('FAL_KEY')
        self.base_url = app.config.get('FAL_API_BASE_URL', 'https://fal.run')
    
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
                # Extract file extension and base64 data
                file_ext = image_data_uri.split(';')[0].split('/')[1]
                if ',' not in file_ext:
                    file_ext = 'jpeg'  # Default extension
                
                base64_data = image_data_uri.split(',')[1]
                
                # Create directory for saved images
                static_folder = current_app.static_folder
                if not static_folder:
                    static_folder = os.path.join(os.path.dirname(current_app.root_path), 'static')
                    os.makedirs(static_folder, exist_ok=True)
                
                static_img_dir = os.path.join(static_folder, 'generated')
                os.makedirs(static_img_dir, exist_ok=True)
                
                # Create a unique filename
                timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                unique_id = os.urandom(4).hex()
                filename = f"img_{timestamp}_{unique_id}.{file_ext}"
                filepath = os.path.join(static_img_dir, filename)
                
                # Save the decoded image
                with open(filepath, 'wb') as f:
                    f.write(base64.b64decode(base64_data))
                
                image_url = f"/static/generated/{filename}"
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
    
    def _generate_with_fal_client(self, prompt, model):
        """Generate an image using the fal_client library"""
        logger.info(f"Generating image with fal_client: {model['endpoint']}")
        
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
            
            # Prepare arguments
            arguments = {
                "prompt": prompt,
                "finetune_id": ""  # Default empty, can be configured if needed
            }
            
            # Add model-specific parameters if they exist
            if 'params' in model:
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
            
            # Process the result
            if result:
                try:
                    image_url = self._extract_image_url(result)
                    return {'image_url': image_url}
                except Exception:
                    logger.error(f"Unexpected response structure from fal_client: {result}")
                    raise Exception('No image URL found in response')
            else:
                raise Exception("Empty response from fal_client")
                
        except Exception as e:
            logger.warning(f"Failed to use fal_client directly, trying fallback method: {str(e)}")
            return self._fallback_fal_client(prompt, model, image_file, mask_file)
    
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
                
                # Process image file for image-to-image generation if provided
                if image_file and model.get('supports_image_input', False):
                    logger.info("Processing reference image for FLUX Pro image-to-image generation")
                    
                    try:
                        # Read image from BytesIO
                        logger.info(f"Reading image file: {image_file.filename}")
                        img_stream = io.BytesIO(image_file.read())
                        # Reset file pointer for potential future use
                        image_file.seek(0)
                        
                        # Get file size for debugging
                        file_size = len(img_stream.getvalue())
                        logger.info(f"Image size: {file_size} bytes")
                        
                        # Convert to base64
                        base64_image = base64.b64encode(img_stream.getvalue()).decode('utf-8')
                        logger.info(f"Converted image to base64 (length: {len(base64_image)})")
                        
                        # For FLUX Pro, add the IP Adapter configuration
                        primary_payload['ip_adapters'] = [{
                            "image_url": f"data:image/jpeg;base64,{base64_image}",
                            "path": "h94/IP-Adapter",
                            "image_encoder_path": "openai/clip-vit-large-patch14",
                            "scale": 0.7
                        }]
                        
                        logger.debug("Successfully processed reference image for FLUX Pro")
                    except Exception as e:
                        logger.error(f"Error processing reference image for FLUX Pro: {str(e)}")
                        logger.exception("Detailed error:")
                        raise Exception(f"Failed to process reference image: {str(e)}")
                
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
                        primary_payload['image_url'] = f"data:image/jpeg;base64,{base64_image}"
                        primary_payload['mask_url'] = f"data:image/jpeg;base64,{base64_mask}"
                        
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
                        img_data_uri = f"data:image/jpeg;base64,{base64_image}"
                        
                        mask_stream = io.BytesIO()
                        pil_mask.save(mask_stream, format="JPEG", quality=95)
                        mask_stream.seek(0)
                        base64_mask = base64.b64encode(mask_stream.getvalue()).decode('utf-8')
                        mask_data_uri = f"data:image/jpeg;base64,{base64_mask}"
                        
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
                                "image_url": f"data:image/jpeg;base64,{base64_image}",
                                "path": "h94/IP-Adapter",
                                "image_encoder_path": "openai/clip-vit-large-patch14",
                                "scale": 0.7
                            }]
                        else:
                            alt_payload['image'] = f"data:image/jpeg;base64,{base64_image}"
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
        logger.info(f"Generating image with REST API: {model['endpoint']}")
        
        headers = {
            'Authorization': f'Key {self.api_key}',
            'Content-Type': 'application/json'
        }

        # Base payload
        payload = {
            'prompt': prompt
        }

        # Add model-specific parameters if they exist
        if 'params' in model:
            # Filter out None values and empty strings
            params = {k: v for k, v in model['params'].items() if v is not None and v != ''}
            payload.update(params)
            logger.info(f"Added model params: {params}")

        # Handle image-to-image models
        if (model['type'] == 'image-to-image' or model['type'] == 'hybrid') and image_file:
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
                        "image_url": f"data:image/jpeg;base64,{img_str}",
                        "path": "h94/IP-Adapter",
                        "image_encoder_path": "openai/clip-vit-large-patch14",
                        "scale": 0.7
                    }]
                    logger.info(f"Added ip_adapters to payload for FLUX model (image length: {len(img_str)})")
                else:
                    # Standard image_url format for other models like Stable Diffusion
                    payload['image_url'] = f"data:image/png;base64,{img_str}"
                    logger.info(f"Added image_url to payload (length: {len(img_str)})")
                
                # If strength is not specified, set a default for image-to-image
                if 'strength' not in payload:
                    payload['strength'] = 0.75
                    logger.info(f"Added default strength: 0.75")
                    
            except Exception as e:
                logger.error(f"Error processing image: {str(e)}")
                raise Exception(f'Failed to process input image: {str(e)}')
        elif (model['type'] == 'image-to-image' or model['type'] == 'hybrid'):
            logger.info(f"Model supports images but no image file was provided")

        try:
            logger.info(f"Making request to: {self.base_url}/{model['endpoint']}")
            logger.debug(f"With payload: {json.dumps({k: v for k, v in payload.items() if k != 'image_url'}, indent=2)}")
            
            # Set a longer timeout for Recraft models specifically
            request_timeout = 120 if 'recraft' in model['endpoint'].lower() else 60
            logger.info(f"Using timeout of {request_timeout} seconds for {model['endpoint']}")
            
            response = requests.post(
                f'{self.base_url}/{model["endpoint"]}',
                headers=headers,
                json=payload,
                timeout=request_timeout  # Increased timeout for Recraft models
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.debug(f"Response content: {response.text}")
            
            if not response.ok:
                error_msg = f"API request failed with status {response.status_code}"
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg = error_data['error']
                except:
                    pass
                raise Exception(error_msg)
                
            result = response.json()
            
            # Handle different response formats
            if 'images' in result and len(result['images']) > 0:
                if isinstance(result['images'][0], str):
                    return {'image_url': result['images'][0]}
                elif isinstance(result['images'][0], dict) and 'url' in result['images'][0]:
                    return {'image_url': result['images'][0]['url']}
            elif 'image' in result:
                if isinstance(result['image'], str):
                    return {'image_url': result['image']}
                elif isinstance(result['image'], dict) and 'url' in result['image']:
                    return {'image_url': result['image']['url']}
            
            logger.error(f"Unexpected response structure: {result}")
            raise Exception('No image URL found in response')

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise Exception(f'API request failed: {str(e)}')
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            raise Exception(f'Failed to parse API response: {str(e)}')
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise

# Create an instance of the service
fal_api_service = FalApiService()

# Import models configuration from separate file
from app.services.models_config import AVAILABLE_MODELS 