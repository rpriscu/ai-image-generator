from flask import Blueprint, redirect, url_for, render_template, request, jsonify, session, flash, current_app, send_file
from app.utils.security import require_login, get_user_info
from app.services.usage_tracker import track_usage, usage_tracker
from app.services.fal_api import fal_api_service, AVAILABLE_MODELS
from app.models.models import MonthlyUsage, Asset, AssetType, db, ShortUrl
import logging
import os
from datetime import datetime, timedelta
import requests
from urllib.parse import urlparse
from flask_login import current_user
from app.services.models_config import MODEL_CONFIGURATIONS, get_model_config
from app.services.model_handlers import handler_registry
from PIL import Image
import io
import base64
import json
from app.services.video_thumbnail import VideoThumbnailService
from app.services.url_shortener import URLShortener

user_bp = Blueprint('user', __name__)
logger = logging.getLogger(__name__)

# Initialize model handlers on startup
handler_registry.initialize_from_config(MODEL_CONFIGURATIONS)

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
    """API endpoint to generate images or videos"""
    try:
        # Get form data and files
        data = request.form
        model_id = data.get('model')
        
        # Get model configuration and handler
        model_config = get_model_config(model_id)
        if not model_config:
            return jsonify({'error': 'Invalid model selected'}), 400
            
        handler = handler_registry.get_handler(model_id)
        if not handler:
            logger.error(f"No handler found for model: {model_id}")
            return jsonify({'error': 'Model handler not configured'}), 500
        
        # Extract inputs
        prompt = data.get('prompt', '')
        image_file = request.files.get('image')
        mask_file = request.files.get('mask')
        
        # Validate inputs using handler
        validation_result = handler.validate_inputs(
            prompt=prompt,
            image_file=image_file,
            mask_file=mask_file
        )
        
        if not validation_result['valid']:
            errors = validation_result['errors']
            error_message = '; '.join([f"{k}: {v}" for k, v in errors.items()])
            return jsonify({'error': error_message}), 400
        
        # Prepare kwargs for handler
        handler_kwargs = {
            'image_file': image_file,
            'mask_file': mask_file,
            'num_outputs': handler.get_num_outputs()
        }
        
        # Add any model-specific parameters from the form
        for param_name in model_config.get('default_params', {}).keys():
            if param_name in data:
                handler_kwargs[param_name] = data.get(param_name)
        
        logger.info(f"Generate request - model: {model_id}, prompt: '{prompt[:50]}...', has_image: {bool(image_file)}, has_mask: {bool(mask_file)}")
        
        # Get user info
        user_id = session.get('user_id')
        
        # Prepare request using handler
        try:
            request_payload = handler.prepare_request(prompt, **handler_kwargs)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        # Determine number of outputs to generate
        num_outputs = handler.get_num_outputs()
        
        # Track generated content
        all_results = []
        errors = []
        
        # Generate the requested number of outputs
        for i in range(num_outputs):
            logger.info(f"Generating output {i+1}/{num_outputs} for model {model_id}")
            try:
                # Use the fal_api_service to generate content
                api_result = fal_api_service.generate_content(
                    prompt=request_payload.get('prompt', ''),
                    model=model_config,
                    image_file=request_payload.get('image_file'),
                    mask_file=request_payload.get('mask_file')
                )
                
                # Process response using handler
                results = handler.process_response(api_result)
                
                # Save to database and format response
                for result in results:
                    # Determine if this is a video result
                    is_video = result['type'] == 'video'
                    
                    # Generate thumbnail for video assets
                    thumbnail_url = None
                    if is_video:
                        try:
                            # Get the actual video URL (resolve if it's shortened)
                            video_url = result['url']
                            if video_url.startswith('/video/'):
                                # This is a shortened URL, resolve it
                                short_key = video_url.split('/')[-1]
                                resolved_url = URLShortener.resolve_url(short_key)
                                if resolved_url:
                                    video_url = resolved_url
                                else:
                                    logger.warning(f"Could not resolve shortened video URL: {video_url}")
                            
                            # Generate thumbnail after the asset is created (we need the ID)
                            logger.info(f"Will generate thumbnail for video: {video_url[:60]}...")
                        except Exception as e:
                            logger.error(f"Error preparing thumbnail generation: {str(e)}")
                    
                    # Save to database
                    asset = Asset(
                        user_id=user_id,
                        file_url=result['url'],
                        type=AssetType.video if is_video else AssetType.image,
                        prompt=prompt,
                        model=model_config['name']
                    )
                    db.session.add(asset)
                    db.session.commit()
                    
                    # Generate thumbnail for video assets after asset is saved
                    if is_video:
                        try:
                            thumbnail_url = VideoThumbnailService.generate_thumbnail(
                                video_url=video_url if 'video_url' in locals() else result['url'],
                                asset_id=asset.id
                            )
                            if thumbnail_url:
                                asset.thumbnail_url = thumbnail_url
                                db.session.commit()
                                logger.info(f"Generated thumbnail for video asset {asset.id}: {thumbnail_url}")
                            else:
                                logger.warning(f"Failed to generate thumbnail for video asset {asset.id}")
                        except Exception as e:
                            logger.error(f"Error generating thumbnail for video asset {asset.id}: {str(e)}")
                    
                    # Add to results with database ID
                    all_results.append({
                        'url': result['url'],
                        'id': asset.id,
                        'type': result['type'],
                        'thumbnail_url': thumbnail_url
                    })
                    
                    logger.info(f"Successfully generated {result['type']}: {result['url'][:50]}...")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout occurred when generating output {i+1}/{num_outputs}")
                errors.append(f"Output {i+1} generation timed out")
            except Exception as e:
                logger.exception(f"Error generating output {i+1}/{num_outputs}: {str(e)}")
                errors.append(f"Output {i+1} failed: {str(e)}")
        
        # Return results
        if all_results:
            response = {'results': all_results}
            if errors:
                response['warnings'] = errors
                logger.warning(f"Returning partial success with warnings: {errors}")
            return jsonify(response)
            
        # If no results were generated, return error
        return jsonify({'error': 'Failed to generate any outputs', 'details': errors}), 500

    except Exception as e:
        logger.exception(f"Error generating content: {str(e)}")
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

@user_bp.route('/api/generation-status/<request_id>', methods=['GET'])
@require_login
def get_generation_status(request_id):
    """API endpoint to check the status of a generation request"""
    from datetime import datetime, timedelta
    
    try:
        user_id = session.get('user_id')
        
        # Extract timestamp from request_id (format: gen_timestamp_randomstring)
        try:
            if not request_id.startswith('gen_'):
                logger.warning(f"Invalid request_id format: {request_id}")
                return jsonify({'error': 'Invalid request ID format'}), 404
                
            timestamp_str = request_id.split('_')[1]
            generation_start = datetime.utcfromtimestamp(int(timestamp_str) / 1000)
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Could not parse timestamp from request_id {request_id}: {str(e)}")
            return jsonify({'error': 'Invalid request ID format'}), 404
        
        now = datetime.utcnow()
        time_elapsed = now - generation_start
        
        # Only look for assets created AFTER this generation started
        # (with a small buffer to account for timing differences)
        generation_cutoff = generation_start - timedelta(seconds=30)
        
        # Look for assets created after this generation started
        assets_after_generation = Asset.query.filter(
            Asset.user_id == user_id,
            Asset.created_at >= generation_cutoff
        ).order_by(Asset.created_at.desc()).all()
        
        if assets_after_generation:
            # Found assets created after this generation started - likely completed
            logger.info(f"Found {len(assets_after_generation)} asset(s) created after generation {request_id} started")
            
            # Format the results
            results = []
            for asset in assets_after_generation:
                results.append({
                    'url': asset.file_url,
                    'id': asset.id,
                    'type': asset.type.value,
                    'thumbnail_url': asset.thumbnail_url
                })
            
            return jsonify({
                'status': 'completed',
                'results': results
            })
        
        # No assets found yet. Check if generation is still within reasonable time limits.
        max_video_time = timedelta(minutes=8)  # Conservative for video generation
        max_image_time = timedelta(minutes=3)  # Conservative for image generation
        
        # If less than image timeout, assume still in progress
        if time_elapsed < max_image_time:
            logger.info(f"Generation {request_id} started {time_elapsed.total_seconds():.1f}s ago, likely still in progress")
            return jsonify({'status': 'pending'})
        
        # If less than video timeout but more than image timeout, 
        # assume it might be a video still in progress
        elif time_elapsed < max_video_time:
            logger.info(f"Generation {request_id} started {time_elapsed.total_seconds():.1f}s ago, possibly video still in progress")
            return jsonify({'status': 'pending'})
        
        # If more than video timeout, likely failed
        else:
            logger.info(f"Generation {request_id} started {time_elapsed.total_seconds():.1f}s ago, likely failed or timed out")
            return jsonify({'error': 'Generation likely failed or timed out'}), 404
        
    except Exception as e:
        logger.exception(f"Error checking generation status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@user_bp.route('/api/clear-generation-state', methods=['POST'])
@require_login
def clear_generation_state():
    """API endpoint to clear all generation state (for debugging/cleanup)"""
    try:
        logger.info("Generation state cleared by user request")
        return jsonify({'success': True, 'message': 'Generation state cleared successfully'})
    except Exception as e:
        logger.exception(f"Error clearing generation state: {str(e)}")
        return jsonify({'error': str(e)}), 500

@user_bp.route('/api/assets/<int:asset_id>', methods=['DELETE'])
@require_login
def delete_asset(asset_id):
    """API endpoint to delete an asset by ID"""
    try:
        user_id = session.get('user_id')
        
        # Find the asset, ensuring it belongs to the current user
        asset = Asset.query.filter_by(id=asset_id, user_id=user_id).first()
        
        if not asset:
            return jsonify({'error': 'Asset not found'}), 404
        
        # Delete the asset
        db.session.delete(asset)
        db.session.commit()
        
        logger.info(f"Asset {asset_id} deleted by user {user_id}")
        return jsonify({'success': True})
        
    except Exception as e:
        logger.exception(f"Error deleting asset {asset_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@user_bp.route('/video/<short_key>')
@require_login
def get_video(short_key):
    """Redirect to the original video URL from a shortened URL"""
    logger.info(f"Video access request for short key: {short_key}")
    
    # Use URLShortener service to resolve the URL
    try:
        original_url = URLShortener.resolve_url(short_key)
        
        if original_url:
            logger.info(f"URL resolved successfully for key: {short_key}")
            logger.info(f"Redirecting to original video URL: {original_url[:60]}...")
            return redirect(original_url)
        else:
            logger.warning(f"No URL found for short key: {short_key}")
            flash('Video not found or has expired', 'error')
            return redirect(url_for('user.dashboard'))
            
    except Exception as e:
        logger.error(f"Error resolving video URL for key {short_key}: {str(e)}")
        flash('Error accessing video', 'error')
        return redirect(url_for('user.dashboard')) 