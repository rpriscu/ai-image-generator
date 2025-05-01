import requests
from flask import current_app, redirect, url_for, session, request
import json
from oauthlib.oauth2 import WebApplicationClient
from app.models.models import User, db
from datetime import datetime
import os

# Allow OAuth over HTTP in development (do not use in production)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

class GoogleAuthService:
    """Handles Google OAuth2 authentication flow"""
    
    def __init__(self):
        self.client = None
        self.client_id = None
    
    def init_client(self):
        """Initialize the OAuth client"""
        if self.client is None:
            self.client_id = current_app.config['GOOGLE_CLIENT_ID']
            self.client = WebApplicationClient(self.client_id)
        return self.client
    
    def get_google_provider_cfg(self):
        """Retrieve Google's provider configuration"""
        try:
            return requests.get(current_app.config['GOOGLE_DISCOVERY_URL']).json()
        except Exception as e:
            current_app.logger.error(f"Failed to get Google provider config: {str(e)}")
            return None
    
    def get_authorization_url(self, redirect_uri):
        """Get the authorization URL for Google login"""
        client = self.init_client()
        google_provider_cfg = self.get_google_provider_cfg()
        
        if not google_provider_cfg:
            return None
        
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]
        
        # Use the library to construct the request for Google login
        return client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=redirect_uri,
            scope=["openid", "email", "profile"],
        )
    
    def handle_callback(self, redirect_uri):
        """Process the OAuth callback from Google"""
        current_app.logger.info(f"Processing OAuth callback with redirect URI: {redirect_uri}")
        client = self.init_client()
        code = request.args.get("code")
        
        if not code:
            current_app.logger.error("No authorization code received in callback")
            return False, "No authorization code received"
        
        # Find out what URL to hit to get tokens
        google_provider_cfg = self.get_google_provider_cfg()
        if not google_provider_cfg:
            return False, "Could not fetch Google provider config"
        
        token_endpoint = google_provider_cfg["token_endpoint"]
        
        # Get the current URL but ensure it uses the same host as the redirect_uri
        # This is important because the current request might be to 127.0.0.1 but the 
        # registered redirect URI is localhost
        current_url = request.url
        
        # If we're using localhost in redirect_uri but got called on 127.0.0.1 (or vice versa),
        # adjust the current URL to match what's registered
        if 'localhost' in redirect_uri and '127.0.0.1' in current_url:
            current_url = current_url.replace('127.0.0.1', 'localhost')
        elif '127.0.0.1' in redirect_uri and 'localhost' in current_url:
            current_url = current_url.replace('localhost', '127.0.0.1')
        
        # Log both URLs for debugging
        current_app.logger.info(f"Authorization response URL: {current_url}")
        current_app.logger.info(f"Redirect URL: {redirect_uri}")
        
        # If using HTTP in development, ensure consistency
        if 'http:' in redirect_uri and 'https:' in current_url:
            current_url = current_url.replace('https:', 'http:')
        
        try:
            # Prepare the token request
            token_url, headers, body = client.prepare_token_request(
                token_endpoint,
                authorization_response=current_url,
                redirect_url=redirect_uri,
                code=code
            )
            
            # Exchange the authorization code for tokens
            token_response = requests.post(
                token_url,
                headers=headers,
                data=body,
                auth=(current_app.config['GOOGLE_CLIENT_ID'], current_app.config['GOOGLE_CLIENT_SECRET']),
            )
            
            # Log token response status for debugging
            current_app.logger.info(f"Token response status: {token_response.status_code}")
            
            if not token_response.ok:
                error_details = token_response.text
                current_app.logger.error(f"Token request failed: {error_details}")
                return False, f"Failed to get token: {error_details}"
            
            # Parse the tokens
            client.parse_request_body_response(json.dumps(token_response.json()))
            
            # Get user info from Google
            userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
            uri, headers, body = client.add_token(userinfo_endpoint)
            userinfo_response = requests.get(uri, headers=headers, data=body)
            
            # Verify the email is from the correct domain
            if not userinfo_response.json().get("email_verified"):
                return False, "Email not verified by Google"
            
            # Get user information
            user_info = userinfo_response.json()
            user_email = user_info["email"]
            user_name = user_info.get("name")
            user_picture = user_info.get("picture")
            
            # Check if the email domain is allowed
            allowed_domain = current_app.config['ALLOWED_EMAIL_DOMAIN']
            if allowed_domain and not user_email.endswith(f'@{allowed_domain}'):
                return False, f"Access restricted to @{allowed_domain} email addresses"
            
            # Get or create the user
            user = User.get_or_create(
                email=user_email,
                name=user_name,
                picture=user_picture
            )
            
            # Update login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Check if the user is active
            if not user.is_active:
                return False, "Your account has been deactivated. Please contact an administrator."
            
            # Store user info in session
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['user_name'] = user.name
            session['user_picture'] = user.picture
            
            return True, user
        except Exception as e:
            current_app.logger.error(f"Error processing callback: {str(e)}")
            return False, f"Error processing callback: {str(e)}"
    
    def logout(self):
        """Log the user out by clearing the session"""
        session.pop('user_id', None)
        session.pop('user_email', None)
        session.pop('user_name', None)
        session.pop('user_picture', None)
        session.clear()
        return True
        
google_auth_service = GoogleAuthService() 