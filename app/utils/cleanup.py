"""
Cleanup utilities for the application.
"""
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def clean_temp_files(temp_dir=None, max_age_hours=24):
    """
    Clean up temporary files older than the specified age.
    
    Args:
        temp_dir (str): Directory path to clean. If None, uses default temp directory.
        max_age_hours (int): Maximum age of files in hours before they are deleted.
    
    Returns:
        int: Number of files deleted
    """
    try:
        # If temp_dir not specified and we're within Flask context, use default
        if temp_dir is None:
            from flask import current_app
            if current_app:
                temp_dir = os.path.join(current_app.root_path, 'static', 'temp')
            else:
                logger.error("No temp directory specified and not in Flask context")
                return 0
        
        if not os.path.exists(temp_dir):
            logger.info(f"Temp directory does not exist: {temp_dir}")
            return 0
        
        # Calculate cutoff time
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        files_deleted = 0
        
        # Walk through the temp directory
        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                
                # Get file modification time
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                # Delete if older than cutoff
                if file_mtime < cutoff_time:
                    try:
                        os.remove(file_path)
                        files_deleted += 1
                        logger.debug(f"Deleted old temp file: {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to delete temp file {file_path}: {str(e)}")
        
        logger.info(f"Cleaned up {files_deleted} temporary files older than {max_age_hours} hours")
        return files_deleted
        
    except Exception as e:
        logger.error(f"Error during temp file cleanup: {str(e)}")
        return 0

if __name__ == "__main__":
    # When run directly, clean up all temp files
    logging.basicConfig(level=logging.INFO)
    num_deleted = clean_temp_files()
    print(f"Cleaned up {num_deleted} temporary files") 