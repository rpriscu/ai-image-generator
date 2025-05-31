"""
URL Shortening Service
======================

This module provides URL shortening functionality for long asset URLs.
It's particularly useful for video URLs that can exceed database column limits.

The service supports:
- Database-backed persistent storage (preferred)
- In-memory cache fallback
- Collision-resistant short key generation
"""

import hashlib
import logging
from datetime import datetime
from typing import Optional, Dict
from flask import current_app

logger = logging.getLogger(__name__)


class URLShortener:
    """
    Handles URL shortening with database persistence and cache fallback.
    
    This service is designed to handle URLs that exceed typical database
    column length limits (255 characters) by creating short keys that
    map to the original URLs.
    """
    
    # URL length threshold - URLs shorter than this won't be shortened
    URL_LENGTH_THRESHOLD = 255
    
    # In-memory cache for URL mappings (fallback when DB is unavailable)
    _cache: Dict[str, str] = {}
    
    @classmethod
    def shorten_url(cls, url: str, user_id: Optional[int] = None) -> str:
        """
        Create a shortened version of a long URL.
        
        Args:
            url: The long URL to shorten
            user_id: Optional user ID for tracking ownership
            
        Returns:
            Either a short URL path (/video/SHORT_KEY) or the original URL
            if it's already short enough
            
        Example:
            >>> short_url = URLShortener.shorten_url(long_video_url)
            >>> # Returns: '/video/abc123_1234567890'
        """
        logger.info(f"Processing URL for shortening: length={len(url)}")
        
        # Don't shorten if already short enough
        if len(url) <= cls.URL_LENGTH_THRESHOLD:
            return url
        
        # Generate a unique short key
        short_key = cls._generate_short_key(url)
        
        # Try to save to database first
        if cls._save_to_database(short_key, url, user_id):
            logger.info(f"URL shortened and saved to database: {short_key}")
        else:
            # Fallback to in-memory cache
            cls._save_to_cache(short_key, url)
            logger.warning(f"URL shortened using in-memory cache: {short_key}")
        
        # Return the short URL path
        return f"/video/{short_key}"
    
    @classmethod
    def resolve_url(cls, short_key: str) -> Optional[str]:
        """
        Resolve a short key back to its original URL.
        
        Args:
            short_key: The short key to resolve
            
        Returns:
            The original URL if found, None otherwise
            
        Example:
            >>> original_url = URLShortener.resolve_url('abc123_1234567890')
        """
        logger.info(f"Resolving short key: {short_key}")
        
        # Try database first
        url = cls._get_from_database(short_key)
        if url:
            logger.info(f"URL found in database for key: {short_key}")
            return url
        
        # Fallback to cache
        url = cls._get_from_cache(short_key)
        if url:
            logger.info(f"URL found in cache for key: {short_key}")
            return url
        
        logger.warning(f"No URL found for short key: {short_key}")
        return None
    
    @staticmethod
    def _generate_short_key(url: str) -> str:
        """
        Generate a collision-resistant short key for a URL.
        
        Uses MD5 hash (for speed) plus timestamp to minimize collisions.
        
        Args:
            url: The URL to generate a key for
            
        Returns:
            A short key like 'abc123def456_1234567890'
        """
        # Create hash of URL
        url_hash = hashlib.md5(url.encode()).hexdigest()[:16]
        
        # Add timestamp for uniqueness
        timestamp = int(datetime.now().timestamp())
        
        return f"{url_hash}_{timestamp}"
    
    @classmethod
    def _save_to_database(cls, short_key: str, url: str, user_id: Optional[int]) -> bool:
        """
        Save URL mapping to database.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Import here to avoid circular imports
            from app.models.models import ShortUrl, db
            
            short_url_obj = ShortUrl(
                short_key=short_key,
                original_url=url,
                user_id=user_id,
                created_at=datetime.utcnow()
            )
            
            db.session.add(short_url_obj)
            db.session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save URL to database: {str(e)}")
            try:
                db.session.rollback()
            except:
                pass
            return False
    
    @classmethod
    def _save_to_cache(cls, short_key: str, url: str) -> None:
        """Save URL mapping to in-memory cache."""
        cls._cache[short_key] = url
        
        # Also save to Flask app context if available
        try:
            if not hasattr(current_app, 'url_cache'):
                current_app.url_cache = {}
            current_app.url_cache[short_key] = url
        except RuntimeError:
            # Not in Flask context
            pass
    
    @staticmethod
    def _get_from_database(short_key: str) -> Optional[str]:
        """Retrieve URL from database."""
        try:
            from app.models.models import ShortUrl
            
            url_entry = ShortUrl.query.filter_by(short_key=short_key).first()
            if url_entry:
                return url_entry.original_url
                
        except Exception as e:
            logger.error(f"Error retrieving URL from database: {str(e)}")
        
        return None
    
    @classmethod
    def _get_from_cache(cls, short_key: str) -> Optional[str]:
        """Retrieve URL from cache."""
        # Try class cache first
        url = cls._cache.get(short_key)
        if url:
            return url
        
        # Try Flask app cache
        try:
            return current_app.url_cache.get(short_key)
        except (RuntimeError, AttributeError):
            pass
        
        return None
    
    @classmethod
    def cleanup_old_urls(cls, days_old: int = 30) -> int:
        """
        Clean up old URL mappings from database.
        
        Args:
            days_old: Remove URLs older than this many days
            
        Returns:
            Number of URLs deleted
        """
        try:
            from app.models.models import ShortUrl, db
            from datetime import timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            old_urls = ShortUrl.query.filter(
                ShortUrl.created_at < cutoff_date
            ).all()
            
            count = len(old_urls)
            
            for url in old_urls:
                db.session.delete(url)
            
            db.session.commit()
            
            logger.info(f"Cleaned up {count} old URL mappings")
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up old URLs: {str(e)}")
            return 0 