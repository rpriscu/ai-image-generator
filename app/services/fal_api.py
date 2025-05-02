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

logger = logging.getLogger(__name__)

class FalApiService:
    """Service to interact with the fal.ai API for image generation"""
    
    def __init__(self):
        self.api_key = None
        self.base_url = None
    
    def init_app(self, app):
        """Initialize the service with Flask app config"""
        self.api_key = app.config.get('FAL_KEY')
        self.base_url = app.config.get('FAL_API_BASE_URL', 'https://fal.run')
    
    def generate_image(self, prompt, model, image_file=None):
        """
        Generate an image using the specified fal.ai model.
        
        Args:
            prompt (str): The text prompt for image generation
            model (dict): The model configuration
            image_file (FileStorage, optional): The reference image file for image-to-image models
        
        Returns:
            dict: The generated image data
        """
        if not self.api_key:
            self.api_key = current_app.config.get('FAL_KEY')
            self.base_url = current_app.config.get('FAL_API_BASE_URL', 'https://fal.run')
        
        # Check which API method to use based on model configuration
        if model.get('use_rest_api', False):
            return self._fallback_fal_client(prompt, model)
        elif model.get('use_fal_client', False):
            return self._generate_with_fal_client(prompt, model)
        else:
            return self._generate_with_rest_api(prompt, model, image_file)
    
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
        # Check for 'images' array
        if 'images' in result and len(result['images']) > 0:
            if isinstance(result['images'][0], str):
                return result['images'][0]
            elif isinstance(result['images'][0], dict) and 'url' in result['images'][0]:
                return result['images'][0]['url']
        
        # Check for single 'image' field
        elif 'image' in result:
            if isinstance(result['image'], str):
                return result['image']
            elif isinstance(result['image'], dict) and 'url' in result['image']:
                return result['image']['url']
        
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
            return self._fallback_fal_client(prompt, model)
    
    def _fallback_fal_client(self, prompt, model):
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
            logger.debug(f"With payload: {json.dumps(payload, indent=2)}")
            
            try:
                response = requests.post(
                    f'{self.base_url}/{endpoint}',
                    headers=headers,
                    json=payload,
                    timeout=60  # Longer timeout for Pro models
                )
                
                logger.info(f"Response status: {response.status_code}")
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
                
                # For FLUX Pro, the endpoint is simply 'flux'
                primary_endpoint = model['endpoint']
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
                try:
                    image_url = self._extract_image_url(result)
                    return {'image_url': image_url}
                except Exception:
                    logger.error(f"Unexpected response structure: {result}")
                    raise Exception('No image URL found in primary response')
            
            # If we get here, the primary request failed
            logger.info("Primary request failed, trying alternative formats...")
            
            # Try each alternative format
            alt_formats = model.get('alt_formats', [])
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
            raise Exception("All request formats failed. Please check your API key and model configuration.")
            
        except Exception as e:
            logger.exception(f"Fallback method failed: {str(e)}")
            raise Exception(f"Failed to generate image with Pro model: {str(e)}")
    
    def _generate_with_rest_api(self, prompt, model, image_file=None):
        """Generate an image using the standard REST API"""
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
            payload.update(model['params'])

        # Handle image-to-image models
        if (model['type'] == 'image-to-image' or model['type'] == 'hybrid') and image_file:
            image = Image.open(image_file)
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            payload['image_url'] = f"data:image/png;base64,{img_str}"

        try:
            logger.info(f"Making request to: {self.base_url}/{model['endpoint']}")
            logger.debug(f"With payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                f'{self.base_url}/{model["endpoint"]}',
                headers=headers,
                json=payload,
                timeout=30
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
            
            # Extract image URL using the shared method
            try:
                image_url = self._extract_image_url(result)
                return {'image_url': image_url}
            except Exception as e:
                logger.error(f"Error extracting image URL: {str(e)}")
                raise
                
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