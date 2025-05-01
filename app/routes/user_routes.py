from flask import Blueprint, redirect, url_for, render_template, request, jsonify, session, flash, current_app
from app.utils.security import require_login, get_user_info
from app.services.fal_api import fal_api_service, AVAILABLE_MODELS
from app.services.usage_tracker import track_usage, usage_tracker
from app.models.models import MonthlyUsage
import logging

user_bp = Blueprint('user', __name__)
logger = logging.getLogger(__name__)

@user_bp.route('/')
def index():
    """Landing page - redirects to login if not authenticated, otherwise to the dashboard"""
    if 'user_id' in session:
        return redirect(url_for('user.dashboard'))
    return redirect(url_for('auth.login'))

@user_bp.route('/dashboard')
@require_login
def dashboard():
    """Main dashboard with the image generator interface"""
    user_info = get_user_info()
    
    # Get usage statistics
    user_id = session.get('user_id')
    current_usage = usage_tracker.get_user_usage(user_id)
    
    # Check if FAL API key is configured
    fal_api_key = current_app.config.get('FAL_API_KEY')
    if not fal_api_key:
        flash('Warning: FAL API key is not configured. Image generation will not work.', 'error')
        logger.warning("FAL API key not configured. Image generation will fail.")
    
    return render_template(
        'user/dashboard.html',
        user=user_info,
        models=AVAILABLE_MODELS,
        current_usage=current_usage,
        api_configured=bool(fal_api_key)
    )

@user_bp.route('/api/generate', methods=['POST'])
@require_login
@track_usage
def generate():
    """API endpoint to generate images"""
    try:
        data = request.form
        prompt = data.get('prompt')
        model_id = data.get('model')
        image_file = request.files.get('image')
        num_images = int(data.get('num_images', 1))  # Default to 1 if not specified

        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        if not model_id or model_id not in AVAILABLE_MODELS:
            return jsonify({'error': 'Invalid model selected'}), 400

        model = AVAILABLE_MODELS[model_id]
        
        # For premium models (both REST API direct and fal_client), we generate one image at a time
        if model.get('use_rest_api', False) or model.get('use_fal_client', False):
            # Limit to just one image for premium models to avoid excessive API calls
            try:
                # Generate using the appropriate method
                result = fal_api_service.generate_image(
                    prompt=prompt,
                    model=model
                )
                
                if 'image_url' in result:
                    return jsonify({'image_urls': [result['image_url']]})
                else:
                    return jsonify({'error': 'Failed to generate image with premium model'}), 500
            except Exception as e:
                logger.exception(f"Error with premium model: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        # For standard models, continue with batch generation
        # Limit number of images to generate
        num_images = min(num_images, 4)  # Maximum 4 images
        
        # Track generated images
        image_urls = []
        
        # Generate the requested number of images
        for _ in range(num_images):
            # Generate image using the selected model
            result = fal_api_service.generate_image(
                prompt=prompt,
                model=model,
                image_file=image_file if model['type'] == 'image-to-image' else None
            )
            
            if 'image_url' in result:
                image_urls.append(result['image_url'])
        
        # If we couldn't generate any images, return an error
        if not image_urls:
            return jsonify({'error': 'Failed to generate any images'}), 500
            
        return jsonify({'image_urls': image_urls})

    except Exception as e:
        logger.exception(f"Error generating images: {str(e)}")
        return jsonify({'error': str(e)}), 500

@user_bp.route('/usage')
@require_login
def usage_stats():
    """Page showing user's usage statistics"""
    user_id = session.get('user_id')
    user_info = get_user_info()
    
    # Get current month usage
    current_usage = usage_tracker.get_user_usage(user_id)
    
    # Get all usage history for the user
    usage_history = MonthlyUsage.query.filter_by(user_id=user_id).order_by(
        MonthlyUsage.month.desc()
    ).all()
    
    return render_template(
        'user/usage.html',
        user=user_info,
        current_usage=current_usage,
        usage_history=usage_history
    )

@user_bp.route('/api/model-info/<model_id>', methods=['GET'])
@require_login
def get_model_info(model_id):
    """API endpoint to get detailed information about a model"""
    try:
        if model_id not in AVAILABLE_MODELS:
            return jsonify({'error': 'Invalid model ID'}), 404
            
        model = AVAILABLE_MODELS[model_id]
        
        # Check if the model has detailed info
        if 'detailed_info' not in model:
            return jsonify({'error': 'No detailed information available for this model'}), 404
            
        # Return model info
        return jsonify({
            'name': model['name'],
            'info': model['detailed_info']
        })
        
    except Exception as e:
        logger.exception(f"Error getting model info: {str(e)}")
        return jsonify({'error': str(e)}), 500 