"""
Background job processing service for long-running tasks like video generation.
Uses Redis and Celery to handle tasks that exceed Heroku's 30-second timeout.
"""
import os
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json
import redis
from flask import current_app

logger = logging.getLogger(__name__)

class BackgroundJobService:
    """
    Service for managing background jobs that can run longer than 30 seconds.
    Uses Redis for job storage and status tracking.
    """
    
    def __init__(self):
        self.redis_client = None
        self.job_timeout = 600  # 10 minutes max for video generation
    
    def init_app(self, app):
        """Initialize with Flask app"""
        redis_url = app.config.get('REDIS_URL') or os.environ.get('REDIS_URL')
        if redis_url:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            logger.info("Connected to Redis for background jobs")
        else:
            logger.warning("No Redis URL configured - background jobs will not work")
    
    def submit_generation_job(self, job_data: Dict[str, Any]) -> str:
        """
        Submit a generation job to the background queue.
        
        Args:
            job_data: Dictionary containing job parameters
                - prompt: The generation prompt
                - model: Model configuration
                - user_id: User ID
                - image_file_data: Base64 encoded image (if applicable)
                - mask_file_data: Base64 encoded mask (if applicable)
        
        Returns:
            str: Job ID for tracking
        """
        if not self.redis_client:
            raise Exception("Redis not configured - cannot submit background job")
        
        job_id = str(uuid.uuid4())
        
        # Store job data
        job_info = {
            'id': job_id,
            'status': 'pending',
            'submitted_at': datetime.utcnow().isoformat(),
            'data': job_data,
            'progress': 0,
            'message': 'Job submitted and waiting to start'
        }
        
        # Store in Redis with expiration
        self.redis_client.setex(
            f"job:{job_id}",
            self.job_timeout,
            json.dumps(job_info)
        )
        
        # Add to processing queue
        self.redis_client.lpush("generation_queue", job_id)
        
        logger.info(f"Submitted background job {job_id}")
        return job_id
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current status of a job.
        
        Args:
            job_id: The job ID
            
        Returns:
            Dict with job status or None if not found
        """
        if not self.redis_client:
            return None
        
        job_data = self.redis_client.get(f"job:{job_id}")
        if job_data:
            return json.loads(job_data)
        return None
    
    def update_job_status(self, job_id: str, status: str, progress: int = None, 
                         message: str = None, result: Dict[str, Any] = None):
        """
        Update job status.
        
        Args:
            job_id: Job ID
            status: New status ('pending', 'processing', 'completed', 'failed')
            progress: Progress percentage (0-100)
            message: Status message
            result: Result data if completed
        """
        if not self.redis_client:
            return
        
        job_info = self.get_job_status(job_id)
        if not job_info:
            return
        
        job_info['status'] = status
        if progress is not None:
            job_info['progress'] = progress
        if message is not None:
            job_info['message'] = message
        if result is not None:
            job_info['result'] = result
        
        job_info['updated_at'] = datetime.utcnow().isoformat()
        
        # Store updated info
        self.redis_client.setex(
            f"job:{job_id}",
            self.job_timeout,
            json.dumps(job_info)
        )
        
        logger.info(f"Updated job {job_id}: {status} ({progress}%) - {message}")
    
    def process_next_job(self) -> bool:
        """
        Process the next job in the queue.
        This would typically be called by a worker dyno.
        
        Returns:
            bool: True if a job was processed, False if queue was empty
        """
        if not self.redis_client:
            return False
        
        # Get next job from queue (blocking for 5 seconds)
        result = self.redis_client.brpop("generation_queue", timeout=5)
        if not result:
            return False
        
        queue_name, job_id = result
        
        try:
            job_info = self.get_job_status(job_id)
            if not job_info:
                logger.error(f"Job {job_id} not found")
                return True
            
            self.update_job_status(job_id, 'processing', 0, 'Starting generation...')
            
            # Extract job data
            job_data = job_info['data']
            prompt = job_data['prompt']
            model = job_data['model']
            
            # Import here to avoid circular imports
            from app.services.fal_api import fal_api_service
            
            # Process image/mask files if provided
            image_file = None
            mask_file = None
            
            if 'image_file_data' in job_data:
                # Convert base64 back to file-like object
                import base64
                import io
                image_data = base64.b64decode(job_data['image_file_data'])
                image_file = io.BytesIO(image_data)
            
            if 'mask_file_data' in job_data:
                import base64
                import io
                mask_data = base64.b64decode(job_data['mask_file_data'])
                mask_file = io.BytesIO(mask_data)
            
            self.update_job_status(job_id, 'processing', 25, 'Calling API...')
            
            # Generate content
            result = fal_api_service.generate_content(
                prompt=prompt,
                model=model,
                image_file=image_file,
                mask_file=mask_file
            )
            
            if 'error' in result:
                self.update_job_status(job_id, 'failed', 100, result['error'])
            else:
                self.update_job_status(job_id, 'completed', 100, 'Generation completed successfully', result)
            
            return True
            
        except Exception as e:
            logger.exception(f"Error processing job {job_id}: {str(e)}")
            self.update_job_status(job_id, 'failed', 100, f"Error: {str(e)}")
            return True

# Global instance
background_job_service = BackgroundJobService() 