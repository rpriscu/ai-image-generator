#!/usr/bin/env python3
"""
Background worker for processing long-running generation tasks.
This runs as a separate Heroku worker dyno to handle video generation
and other tasks that exceed the 30-second web timeout.
"""
import os
import sys
import time
import logging
from app import create_app
from app.services.background_jobs import background_job_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def main():
    """Main worker loop"""
    logger.info("Starting background worker...")
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        # Initialize background job service
        background_job_service.init_app(app)
        
        if not background_job_service.redis_client:
            logger.error("Redis not configured - worker cannot start")
            sys.exit(1)
        
        logger.info("Worker ready - waiting for jobs...")
        
        # Main processing loop
        while True:
            try:
                # Process next job (blocks for up to 5 seconds)
                job_processed = background_job_service.process_next_job()
                
                if not job_processed:
                    # No job was available, short sleep to prevent busy waiting
                    time.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("Worker shutting down...")
                break
            except Exception as e:
                logger.exception(f"Error in worker loop: {str(e)}")
                time.sleep(5)  # Wait before retrying

if __name__ == "__main__":
    main() 