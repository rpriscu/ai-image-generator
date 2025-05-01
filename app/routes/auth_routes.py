from flask import Blueprint, redirect, url_for, render_template, request, flash, session, current_app
from app.services.google_auth import google_auth_service
from app.models.models import Admin, db, User
from werkzeug.security import check_password_hash
import os

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login')
def login():
    """User login page"""
    # Check if user is already logged in
    if 'user_id' in session:
        return redirect(url_for('user.dashboard'))
    
    # Get the next URL (where to redirect after login)
    next_url = request.args.get('next', url_for('user.dashboard'))
    
    # Make sure template exists
    try:
        return render_template('auth/login.html', next=next_url)
    except Exception as e:
        current_app.logger.error(f"Error rendering login template: {str(e)}")
        return f"Error loading login page: {str(e)}", 500

@auth_bp.route('/google-login')
def google_login():
    """Initiate Google OAuth login"""
    # Build the callback URL with http://localhost:8080 as base
    # This must match exactly what's configured in Google Developer Console
    callback_url = "http://localhost:8080/auth/google-callback"
    
    # Get the authorization URL
    auth_url = google_auth_service.get_authorization_url(callback_url)
    
    # If we couldn't get the authorization URL, show an error
    if not auth_url:
        flash('Failed to connect to Google. Please try again later.', 'error')
        return redirect(url_for('auth.login'))
    
    # Save the callback URL in session for later use
    session['oauth_callback_url'] = callback_url
    
    # Redirect to Google for authentication
    return redirect(auth_url)

@auth_bp.route('/google-callback')
def google_callback():
    """Handle the Google OAuth callback"""
    try:
        # Get the callback URL from session or use the hardcoded one
        callback_url = session.get('oauth_callback_url', "http://localhost:8080/auth/google-callback")
        
        # Log for debugging
        current_app.logger.info(f"Handling Google callback with URL: {callback_url}")
        
        # Process the callback
        success, result = google_auth_service.handle_callback(callback_url)
        
        if not success:
            # If authentication failed, show an error
            error_message = str(result) if isinstance(result, str) else "Authentication failed"
            current_app.logger.error(f"Google auth failed: {error_message}")
            flash(f'Authentication failed: {error_message}', 'error')
            return redirect(url_for('auth.login'))
        
        # Get the 'next' URL from the session
        next_url = request.args.get('next', url_for('user.dashboard'))
        
        # Authentication succeeded, redirect to the dashboard
        return redirect(next_url)
    except Exception as e:
        current_app.logger.error(f"Exception in Google callback: {str(e)}")
        flash(f'Authentication error: {str(e)}', 'error')
        return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
def logout():
    """Log the user out"""
    google_auth_service.logout()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

# Admin authentication routes
@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    # Check if admin is already logged in
    if 'admin_id' in session:
        return redirect(url_for('admin.dashboard'))
    
    # Handle form submission
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and admin.check_password(password):
            # Store admin info in session
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            
            # Get the next URL
            next_url = request.args.get('next', url_for('admin.dashboard'))
            
            return redirect(next_url)
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('auth/admin_login.html')

@auth_bp.route('/admin/logout')
def admin_logout():
    """Log the admin out"""
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.admin_login'))

@auth_bp.route('/debug')
def debug():
    """Debug page for OAuth setup"""
    callback_url = url_for('auth.google_callback', _external=True)
    hardcoded_callback = "http://localhost:8080/auth/google-callback"
    client_id = current_app.config.get('GOOGLE_CLIENT_ID', 'Not set')
    client_secret_set = 'Set' if current_app.config.get('GOOGLE_CLIENT_SECRET') else 'Not set'
    allowed_domain = current_app.config.get('ALLOWED_EMAIL_DOMAIN', 'Not set')
    
    # Check if environment variables are set
    env_client_id = os.environ.get('GOOGLE_CLIENT_ID', 'Not set')
    env_client_secret = 'Set' if os.environ.get('GOOGLE_CLIENT_SECRET') else 'Not set'
    
    debug_info = {
        'dynamic_callback_url': callback_url,
        'hardcoded_callback_url': hardcoded_callback,
        'config_client_id': client_id,
        'config_client_secret': client_secret_set,
        'env_client_id': env_client_id,
        'env_client_secret': env_client_secret,
        'allowed_domain': allowed_domain,
        'server_name': request.host,
        'scheme': request.scheme
    }
    
    instructions = f"""
    <h2>How to Fix:</h2>
    <ol>
        <li>Go to <a href="https://console.developers.google.com/" target="_blank">Google Developer Console</a></li>
        <li>Select your project</li>
        <li>Go to Credentials -> OAuth 2.0 Client IDs</li>
        <li>Edit your Web client</li>
        <li>Add exactly this URI as an Authorized redirect URI: <code>{hardcoded_callback}</code></li>
        <li>Make sure your .env file has the GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET set</li>
    </ol>
    """
    
    return f"""
    <h1>OAuth Debug Info</h1>
    <p>When setting up Google OAuth, make sure to add the callback URL to your Google OAuth credentials.</p>
    <pre>{debug_info}</pre>
    {instructions}
    """ 