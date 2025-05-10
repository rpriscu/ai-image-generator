from flask import Blueprint, redirect, url_for, render_template, request, jsonify, session, flash, current_app, send_file
from app.utils.security import require_login, get_user_info
from app.services.fal_api import fal_api_service, AVAILABLE_MODELS
from app.services.usage_tracker import track_usage, usage_tracker
from app.models.models import MonthlyUsage, Asset, AssetType, db
import logging
import os
from datetime import datetime
import requests
from urllib.parse import urlparse

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
    fal_api_key = current_app.config.get('FAL_KEY')
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
        # Get form data and files
        data = request.form
        prompt = data.get('prompt')
        model_id = data.get('model')
        image_file = request.files.get('image')
        mask_file = request.files.get('mask')
        num_images = int(data.get('num_images', 1))

        logger.info(f"Generate request - prompt: '{prompt}', model: {model_id}, has_image: {bool(image_file)}, has_mask: {bool(mask_file)}")
        
        # Validate input data
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        if not model_id or model_id not in AVAILABLE_MODELS:
            return jsonify({'error': 'Invalid model selected'}), 400

        model = AVAILABLE_MODELS[model_id]
        user_id = session.get('user_id')
        
        # Determine if we should use the image file
        should_use_image = image_file and (model.get('supports_image_input', False) or model.get('type') in ['image-to-image', 'hybrid'])
        
        # Extract additional parameters for Stable Diffusion
        if 'params' in model and model_id == 'stable_diffusion':
            params_to_update = {}
            
            # Process negative prompt
            if 'negative_prompt' in data and data.get('negative_prompt').strip():
                params_to_update['negative_prompt'] = data.get('negative_prompt')
            
            # Process numeric parameters
            for param_name in ['strength', 'guidance_scale', 'num_inference_steps']:
                if param_name in data and data.get(param_name).strip():
                    try:
                        val = float(data.get(param_name))
                        if param_name == 'num_inference_steps':
                            val = int(val)
                        params_to_update[param_name] = val
                    except ValueError:
                        pass
            
            # Process seed
            if 'seed' in data and data.get('seed').strip():
                try:
                    params_to_update['seed'] = int(data.get('seed'))
                except ValueError:
                    pass
                    
            # Update model params
            if params_to_update:
                model = model.copy()  # Avoid modifying the original
                model['params'].update(params_to_update)
        
        # Handle Recraft V3 parameters
        elif model_id == 'recraft':
            model = model.copy()  # Avoid modifying the original
            recraft_params = {}
            
            # Process style parameter
            if 'recraft_style' in data and data.get('recraft_style'):
                recraft_params['style'] = data.get('recraft_style')
            
            # Process image size
            if 'recraft_image_size' in data and data.get('recraft_image_size'):
                recraft_params['image_size'] = data.get('recraft_image_size')
            
            # Process safety checker
            if 'recraft_safety' in data:
                recraft_params['enable_safety_checker'] = data.get('recraft_safety') == 'true'
            
            # Process color parameters
            colors = []
            for i in range(1, 4):  # Up to 3 colors
                color_key = f'recraft_color{i}'
                if color_key in data and data.get(color_key).strip():
                    # Parse hex color to RGB
                    hex_color = data.get(color_key).lstrip('#')
                    if len(hex_color) == 6:
                        try:
                            r = int(hex_color[0:2], 16)
                            g = int(hex_color[2:4], 16)
                            b = int(hex_color[4:6], 16)
                            colors.append({'r': r, 'g': g, 'b': b})
                        except ValueError:
                            pass
            
            if colors:
                recraft_params['colors'] = colors
            
            # Add parameters to the model
            if recraft_params:
                if 'params' in model:
                    model['params'].update(recraft_params)
                else:
                    model['params'] = recraft_params
        
        # Check for Flux.1 [pro] Fill which requires both image and mask
        if model_id == 'flux_pro' and model.get('endpoint') == 'fal-ai/flux-pro/v1/fill':
            if not image_file:
                return jsonify({'error': 'Reference image is required for FLUX.1 [pro] Fill'}), 400
            if not mask_file:
                return jsonify({'error': 'Mask image is required for FLUX.1 [pro] Fill'}), 400
        
        # For premium models (both REST API direct and fal_client), we generate one image at a time
        if model.get('use_rest_api', False) or model.get('use_fal_client', False):
            # Limit to just one image for premium models to avoid excessive API calls
            try:
                # Generate using the appropriate method
                result = fal_api_service.generate_image(
                    prompt=prompt,
                    model=model,
                    image_file=image_file if should_use_image else None,
                    mask_file=mask_file if model_id == 'flux_pro' else None  # Pass mask file for Flux.1 [pro] Fill
                )
                
                if 'image_url' in result:
                    # Save to database
                    asset = Asset(
                        user_id=user_id,
                        file_url=result['image_url'],
                        type=AssetType.image,
                        prompt=prompt,
                        model=model['name']
                    )
                    db.session.add(asset)
                    db.session.commit()
                    
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
        for i in range(num_images):
            logger.info(f"Generating image {i+1}/{num_images}")
            # Generate image using the selected model
            result = fal_api_service.generate_image(
                prompt=prompt,
                model=model,
                image_file=image_file if should_use_image else None,
                mask_file=mask_file if model_id == 'flux_pro' else None  # Pass mask file for Flux.1 [pro] Fill
            )
            
            if 'image_url' in result:
                image_url = result['image_url']
                image_urls.append(image_url)
                logger.info(f"Successfully generated image: {image_url[:50]}...")
                
                # Save to database
                asset = Asset(
                    user_id=user_id,
                    file_url=image_url,
                    type=AssetType.image,
                    prompt=prompt,
                    model=model['name']
                )
                db.session.add(asset)
        
        # Commit all assets at once for better performance
        if image_urls:
            db.session.commit()
        
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

@user_bp.route('/library')
@require_login
def library():
    """Library page showing all user assets"""
    user_id = session.get('user_id')
    user_info = get_user_info()
    
    # Get filter parameters
    asset_type = request.args.get('type', 'all')
    sort_by = request.args.get('sort', 'newest')
    
    # Build query for assets
    query = Asset.query.filter_by(user_id=user_id)
    
    # Apply type filter if specified
    if asset_type != 'all':
        try:
            asset_type_enum = AssetType[asset_type]
            query = query.filter_by(type=asset_type_enum)
        except (KeyError, ValueError):
            # Invalid asset type, ignore filter
            pass
    
    # Apply sorting
    if sort_by == 'oldest':
        query = query.order_by(Asset.created_at.asc())
    else:  # default to newest
        query = query.order_by(Asset.created_at.desc())
    
    # Get all assets
    assets = query.all()
    
    return render_template(
        'user/library.html',
        user=user_info,
        assets=assets,
        filter_type=asset_type,
        sort_by=sort_by
    )

@user_bp.route('/asset/<int:asset_id>')
@require_login
def asset_detail(asset_id):
    """Asset detail page"""
    user_id = session.get('user_id')
    user_info = get_user_info()
    
    # Get the asset, ensuring it belongs to the current user
    asset = Asset.query.filter_by(id=asset_id, user_id=user_id).first_or_404()
    
    return render_template(
        'user/asset_detail.html',
        user=user_info,
        asset=asset
    )

@user_bp.route('/asset/<int:asset_id>/download')
@require_login
def asset_download(asset_id):
    """Download an asset"""
    user_id = session.get('user_id')
    
    # Get the asset, ensuring it belongs to the current user
    asset = Asset.query.filter_by(id=asset_id, user_id=user_id).first_or_404()
    
    # Parse URL to extract the filename
    parsed_url = urlparse(asset.file_url)
    filename = os.path.basename(parsed_url.path)
    
    # If no filename was found, use a default
    if not filename or '.' not in filename:
        if asset.type == AssetType.image:
            filename = f"asset_{asset.id}.png"
        elif asset.type == AssetType.video:
            filename = f"asset_{asset.id}.mp4"
        else:
            filename = f"asset_{asset.id}.gif"
    
    # For remote URLs, fetch the file content first
    if asset.file_url.startswith(('http://', 'https://')):
        try:
            response = requests.get(asset.file_url, stream=True)
            response.raise_for_status()
            
            # Create a temporary file with the downloaded content
            temp_dir = os.path.join(current_app.root_path, 'static', 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            temp_file = os.path.join(temp_dir, filename)
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Send the downloaded file to the user
            return send_file(temp_file, as_attachment=True, download_name=filename)
            
        except Exception as e:
            logger.exception(f"Error downloading asset: {str(e)}")
            flash(f"Error downloading asset: {str(e)}", "error")
            return redirect(url_for('user.asset_detail', asset_id=asset_id))
    
    # For local files, send them directly
    try:
        return send_file(asset.file_url, as_attachment=True, download_name=filename)
    except Exception as e:
        logger.exception(f"Error downloading asset: {str(e)}")
        flash(f"Error downloading asset: {str(e)}", "error")
        return redirect(url_for('user.asset_detail', asset_id=asset_id))

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

@user_bp.route('/api/delete-image', methods=['POST'])
@require_login
def delete_image():
    """API endpoint to delete an image from the user's library"""
    try:
        data = request.json
        url = data.get('url')
        
        if not url:
            return jsonify({'success': False, 'error': 'No URL provided'}), 400
        
        # Find the asset with this URL
        user_id = session.get('user_id')
        asset = Asset.query.filter_by(user_id=user_id, file_url=url).first()
        
        if not asset:
            return jsonify({'success': False, 'error': 'Image not found in your library'}), 404
        
        # Delete the asset
        db.session.delete(asset)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.exception(f"Error deleting image: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500 