@api_routes.route('/generate-async', methods=['POST'])
@require_auth
def generate_async():
    """
    Submit a generation job for async processing.
    Used for video generation and other long-running tasks to avoid 30s timeout.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        prompt = data.get('prompt', '').strip()
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        model_name = data.get('model')
        if not model_name:
            return jsonify({'error': 'Model is required'}), 400
        
        # Get model configuration
        model = AVAILABLE_MODELS.get(model_name)
        if not model:
            return jsonify({'error': f'Model {model_name} not found'}), 400
        
        # Prepare job data
        job_data = {
            'prompt': prompt,
            'model': model,
            'user_id': session.get('user_id')
        }
        
        # Handle file uploads
        if 'image' in request.files and request.files['image'].filename:
            image_file = request.files['image']
            # Convert to base64 for storage
            image_file.seek(0)
            image_data = image_file.read()
            import base64
            job_data['image_file_data'] = base64.b64encode(image_data).decode()
        
        if 'mask' in request.files and request.files['mask'].filename:
            mask_file = request.files['mask']
            # Convert to base64 for storage
            mask_file.seek(0)
            mask_data = mask_file.read()
            import base64
            job_data['mask_file_data'] = base64.b64encode(mask_data).decode()
        
        # Submit to background queue
        from app.services.background_jobs import background_job_service
        
        try:
            job_id = background_job_service.submit_generation_job(job_data)
            
            return jsonify({
                'success': True,
                'job_id': job_id,
                'message': 'Job submitted successfully. Use /api/job-status to check progress.'
            })
            
        except Exception as e:
            logger.error(f"Failed to submit background job: {str(e)}")
            return jsonify({'error': f'Failed to submit job: {str(e)}'}), 500
    
    except Exception as e:
        logger.exception(f"Error in generate_async: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api_routes.route('/job-status/<job_id>', methods=['GET'])
@require_auth
def get_job_status(job_id):
    """
    Get the status of a background job.
    """
    try:
        from app.services.background_jobs import background_job_service
        
        job_status = background_job_service.get_job_status(job_id)
        if not job_status:
            return jsonify({'error': 'Job not found'}), 404
        
        return jsonify(job_status)
    
    except Exception as e:
        logger.exception(f"Error getting job status: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500 