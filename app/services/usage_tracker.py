from flask import session
from app.models.models import User, MonthlyUsage, db
from datetime import datetime
import functools

class UsageTracker:
    """Tracks API usage per user per month"""
    
    @staticmethod
    def get_current_month():
        """Get the current month in YYYY-MM format"""
        return datetime.utcnow().strftime("%Y-%m")
    
    @staticmethod
    def increment_usage(user_id, count=1):
        """Increment the usage count for a user in the current month"""
        if not user_id:
            return False
        
        current_month = UsageTracker.get_current_month()
        
        # Get or create the usage record for this month
        usage = MonthlyUsage.query.filter_by(
            user_id=user_id,
            month=current_month
        ).first()
        
        if not usage:
            # Create a new record for this month
            usage = MonthlyUsage(
                user_id=user_id,
                month=current_month,
                request_count=0
            )
            db.session.add(usage)
        
        # Increment the count
        usage.request_count += count
        db.session.commit()
        
        return usage.request_count
    
    @staticmethod
    def get_user_usage(user_id, month=None):
        """Get the usage for a user in a specific month"""
        if not month:
            month = UsageTracker.get_current_month()
            
        usage = MonthlyUsage.query.filter_by(
            user_id=user_id,
            month=month
        ).first()
        
        return usage.request_count if usage else 0
    
    @staticmethod
    def get_all_usage():
        """Get all usage records"""
        return MonthlyUsage.query.all()
    
    @staticmethod
    def get_monthly_summary(month=None):
        """Get a summary of all usage for a specific month"""
        if not month:
            month = UsageTracker.get_current_month()
            
        usages = MonthlyUsage.query.filter_by(month=month).all()
        return usages

def track_usage(f):
    """Decorator to track API usage"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Get the current user from the session
        user_id = session.get('user_id')
        
        # Call the original function
        result = f(*args, **kwargs)
        
        # Increment the usage count if we have a user
        if user_id:
            UsageTracker.increment_usage(user_id)
            
        return result
    return decorated_function

usage_tracker = UsageTracker() 