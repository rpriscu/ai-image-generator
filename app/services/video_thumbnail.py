"""
Video Thumbnail Generation Service
=================================

This service handles thumbnail generation for video assets by extracting
representative frames from video files. It supports both local and remote
video URLs and creates static image thumbnails for library display.

Features:
- Extract first frame as thumbnail
- Extract middle frame for better representation
- Support for various video formats
- Fallback handling for extraction failures
- Automatic thumbnail saving and cleanup

Author: AI Image Generator Team
"""

import requests
import tempfile
import os
import logging
from PIL import Image
import io
import base64
from datetime import datetime
from flask import current_app
from typing import Optional, Union

logger = logging.getLogger(__name__)


class VideoThumbnailService:
    """
    Service for generating thumbnails from video files.
    
    Extracts representative frames from videos and saves them as
    static thumbnails for use in the library interface.
    """
    
    @classmethod
    def generate_thumbnail(cls, video_url: str, asset_id: int) -> Optional[str]:
        """
        Generate a thumbnail from a video URL.
        
        Args:
            video_url: URL of the video file
            asset_id: Database ID of the asset for unique naming
            
        Returns:
            URL path to the generated thumbnail, or None if failed
            
        Example:
            >>> thumbnail_url = VideoThumbnailService.generate_thumbnail(
            ...     'https://example.com/video.mp4', 123
            ... )
            >>> # Returns: '/static/generated/thumbnails/video_123_thumb.jpg'
        """
        logger.info(f"Generating thumbnail for video: {video_url[:60]}...")
        
        try:
            # Try different extraction methods
            thumbnail_path = cls._extract_with_opencv(video_url, asset_id)
            
            if not thumbnail_path:
                # Fallback to first frame extraction method
                thumbnail_path = cls._extract_first_frame_fallback(video_url, asset_id)
            
            if thumbnail_path:
                logger.info(f"Successfully generated thumbnail: {thumbnail_path}")
                return thumbnail_path
            else:
                logger.warning(f"Failed to generate thumbnail for video: {video_url}")
                return cls._create_placeholder_thumbnail(asset_id)
                
        except Exception as e:
            logger.error(f"Error generating video thumbnail: {str(e)}")
            return cls._create_placeholder_thumbnail(asset_id)
    
    @classmethod
    def _extract_with_opencv(cls, video_url: str, asset_id: int) -> Optional[str]:
        """
        Extract thumbnail using OpenCV (if available).
        
        This is the preferred method as it provides more control
        over frame selection and video processing.
        """
        try:
            import cv2
            
            # Download video to temporary file if it's a remote URL
            if video_url.startswith(('http://', 'https://')):
                temp_video = cls._download_video_temp(video_url)
                if not temp_video:
                    return None
                video_path = temp_video
            else:
                video_path = video_url
            
            # Open video file
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.warning("Could not open video file with OpenCV")
                return None
            
            # Get total frame count to extract middle frame
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            middle_frame = total_frames // 3  # Extract frame at 1/3 position (better than first frame)
            
            # Set frame position
            cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
            
            # Read frame
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                logger.warning("Could not read frame from video")
                return None
            
            # Convert BGR to RGB (OpenCV uses BGR)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL Image
            pil_image = Image.fromarray(frame_rgb)
            
            # Save thumbnail
            thumbnail_path = cls._save_thumbnail(pil_image, asset_id)
            
            # Cleanup temporary file
            if video_url.startswith(('http://', 'https://')) and os.path.exists(video_path):
                os.unlink(video_path)
            
            return thumbnail_path
            
        except ImportError:
            logger.info("OpenCV not available, will try fallback method")
            return None
        except Exception as e:
            logger.error(f"OpenCV extraction failed: {str(e)}")
            return None
    
    @classmethod
    def _extract_first_frame_fallback(cls, video_url: str, asset_id: int) -> Optional[str]:
        """
        Fallback method using FFmpeg or other tools if available.
        
        This method tries to extract the first frame using system tools.
        """
        try:
            import subprocess
            
            # Check if ffmpeg is available
            result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
            if result.returncode != 0:
                logger.info("FFmpeg not available for thumbnail extraction")
                return None
            
            # Create temporary output file
            thumbnail_temp = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
            thumbnail_temp.close()
            
            # Download video if it's remote
            if video_url.startswith(('http://', 'https://')):
                temp_video = cls._download_video_temp(video_url)
                if not temp_video:
                    return None
                video_input = temp_video
            else:
                video_input = video_url
            
            # Extract frame at 2 seconds (skip any potential intro frames)
            cmd = [
                'ffmpeg', '-i', video_input,
                '-ss', '2',  # Seek to 2 seconds
                '-vframes', '1',  # Extract 1 frame
                '-y',  # Overwrite output
                thumbnail_temp.name
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(thumbnail_temp.name):
                # Load and save the thumbnail
                with Image.open(thumbnail_temp.name) as img:
                    thumbnail_path = cls._save_thumbnail(img, asset_id)
                
                # Cleanup
                os.unlink(thumbnail_temp.name)
                if video_url.startswith(('http://', 'https://')) and os.path.exists(video_input):
                    os.unlink(video_input)
                
                return thumbnail_path
            else:
                logger.warning(f"FFmpeg extraction failed: {result.stderr}")
                return None
                
        except (ImportError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.info(f"FFmpeg fallback not available: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"FFmpeg extraction failed: {str(e)}")
            return None
    
    @classmethod
    def _download_video_temp(cls, video_url: str) -> Optional[str]:
        """
        Download video to a temporary file.
        
        Only downloads first few MB to extract thumbnail efficiently.
        """
        try:
            logger.info("Downloading video for thumbnail extraction...")
            
            # Create temporary file
            temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            
            # Download with range request to get only first 10MB
            headers = {'Range': 'bytes=0-10485760'}  # First 10MB
            response = requests.get(video_url, headers=headers, stream=True, timeout=30)
            
            # Write to temp file
            for chunk in response.iter_content(chunk_size=8192):
                temp_video.write(chunk)
            
            temp_video.close()
            return temp_video.name
            
        except Exception as e:
            logger.error(f"Failed to download video: {str(e)}")
            return None
    
    @classmethod
    def _save_thumbnail(cls, image: Image.Image, asset_id: int) -> str:
        """
        Save PIL Image as thumbnail with proper naming and sizing.
        
        Args:
            image: PIL Image object
            asset_id: Asset ID for unique naming
            
        Returns:
            URL path to saved thumbnail
        """
        # Resize to thumbnail size while maintaining aspect ratio
        thumbnail_size = (320, 240)  # Standard thumbnail size
        image.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
        
        # Ensure RGB mode for JPEG
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Create thumbnails directory
        static_folder = current_app.static_folder
        if not static_folder:
            static_folder = os.path.join(os.path.dirname(current_app.root_path), 'static')
        
        thumbnails_dir = os.path.join(static_folder, 'generated', 'thumbnails')
        os.makedirs(thumbnails_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"video_{asset_id}_thumb_{timestamp}.jpg"
        filepath = os.path.join(thumbnails_dir, filename)
        
        # Save image
        image.save(filepath, format='JPEG', quality=85, optimize=True)
        
        # Return URL path
        return f"/static/generated/thumbnails/{filename}"
    
    @classmethod
    def _create_placeholder_thumbnail(cls, asset_id: int) -> str:
        """
        Create a placeholder thumbnail when video extraction fails.
        
        Returns:
            URL path to placeholder thumbnail
        """
        try:
            # Create a simple placeholder image
            placeholder = Image.new('RGB', (320, 240), color='#2c3e50')
            
            # Add some basic graphics/text
            try:
                from PIL import ImageDraw, ImageFont
                
                draw = ImageDraw.Draw(placeholder)
                
                # Draw video icon placeholder
                # Simple play button triangle
                triangle_points = [(140, 100), (140, 140), (180, 120)]
                draw.polygon(triangle_points, fill='white')
                
                # Draw border
                draw.rectangle([130, 90, 190, 150], outline='white', width=2)
                
                # Add text
                draw.text((160, 160), 'VIDEO', fill='white', anchor='mm')
                draw.text((160, 180), f'#{asset_id}', fill='#95a5a6', anchor='mm')
                
            except ImportError:
                # If PIL fonts not available, just use solid color
                pass
            
            return cls._save_thumbnail(placeholder, asset_id)
            
        except Exception as e:
            logger.error(f"Failed to create placeholder thumbnail: {str(e)}")
            # Return a default placeholder path
            return "/static/images/video-placeholder.jpg" 