from flask import Blueprint, redirect, url_for, render_template, request, jsonify, flash, current_app
from app.utils.security import require_admin, get_admin_info
from app.models.models import User, MonthlyUsage, Admin, db
from app.services.usage_tracker import usage_tracker
from datetime import datetime
import logging

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
logger = logging.getLogger(__name__)

@admin_bp.route('/')
@require_admin
def dashboard():
    """Admin dashboard showing summary statistics"""
    # Get counts
    user_count = User.query.count()
    active_user_count = User.query.filter_by(is_active=True).count()
    
    # Get current month usage summary
    current_month = usage_tracker.get_current_month()
    monthly_usage = usage_tracker.get_monthly_summary(current_month)
    
    # Calculate total usage for the current month
    total_usage = sum(usage.request_count for usage in monthly_usage)
    
    # Get recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Get top users by usage
    top_users = db.session.query(
        User, MonthlyUsage.request_count
    ).join(
        MonthlyUsage
    ).filter(
        MonthlyUsage.month == current_month
    ).order_by(
        MonthlyUsage.request_count.desc()
    ).limit(5).all()
    
    return render_template(
        'admin/dashboard.html',
        admin=get_admin_info(),
        user_count=user_count,
        active_user_count=active_user_count,
        total_usage=total_usage,
        current_month=current_month,
        recent_users=recent_users,
        top_users=top_users
    )

@admin_bp.route('/users')
@require_admin
def user_list():
    """List all users"""
    users = User.query.order_by(User.email).all()
    
    # Get current month
    current_month = usage_tracker.get_current_month()
    
    # Get usage data for all users
    usage_data = {
        usage.user_id: usage.request_count 
        for usage in MonthlyUsage.query.filter_by(month=current_month).all()
    }
    
    return render_template(
        'admin/user_list.html',
        admin=get_admin_info(),
        users=users,
        usage_data=usage_data,
        current_month=current_month
    )

@admin_bp.route('/users/<int:user_id>')
@require_admin
def user_detail(user_id):
    """View user details"""
    user = User.query.get_or_404(user_id)
    
    # Get usage history
    usage_history = MonthlyUsage.query.filter_by(user_id=user_id).order_by(
        MonthlyUsage.month.desc()
    ).all()
    
    return render_template(
        'admin/user_detail.html',
        admin=get_admin_info(),
        user=user,
        usage_history=usage_history
    )

@admin_bp.route('/users/<int:user_id>/toggle_status', methods=['POST'])
@require_admin
def toggle_user_status(user_id):
    """Toggle user active status"""
    user = User.query.get_or_404(user_id)
    
    # Toggle status
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.email} has been {status}.', 'success')
    
    # Return to the user list
    return redirect(url_for('admin.user_list'))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@require_admin
def delete_user(user_id):
    """Delete a user and their usage history"""
    user = User.query.get_or_404(user_id)
    
    # Delete the user
    email = user.email
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {email} has been deleted.', 'success')
    
    # Return to the user list
    return redirect(url_for('admin.user_list'))

@admin_bp.route('/usage')
@require_admin
def usage_report():
    """View usage reports"""
    # Get all months with usage data
    months = db.session.query(MonthlyUsage.month).distinct().order_by(MonthlyUsage.month.desc()).all()
    months = [month[0] for month in months]
    
    # Get the selected month (default to current month)
    selected_month = request.args.get('month', usage_tracker.get_current_month())
    
    # Get usage data for the selected month
    usage_data = db.session.query(
        User, MonthlyUsage.request_count
    ).join(
        MonthlyUsage
    ).filter(
        MonthlyUsage.month == selected_month
    ).order_by(
        MonthlyUsage.request_count.desc()
    ).all()
    
    # Calculate total usage
    total_usage = sum(data[1] for data in usage_data)
    
    return render_template(
        'admin/usage_report.html',
        admin=get_admin_info(),
        months=months,
        selected_month=selected_month,
        usage_data=usage_data,
        total_usage=total_usage
    )

@admin_bp.route('/settings')
@require_admin
def settings():
    """Admin settings"""
    # Get all admin users
    admins = Admin.query.all()
    
    return render_template(
        'admin/settings.html',
        admin=get_admin_info(),
        admins=admins
    )

@admin_bp.route('/settings/add-admin', methods=['POST'])
@require_admin
def add_admin():
    """Add a new admin user"""
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Check if the username is taken
    if Admin.query.filter_by(username=username).first():
        flash('Username already taken.', 'error')
        return redirect(url_for('admin.settings'))
    
    # Create the admin
    new_admin = Admin.create_admin(username, password)
    
    flash(f'Admin user {username} created successfully.', 'success')
    return redirect(url_for('admin.settings')) 