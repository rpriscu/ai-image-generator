"""
Monkey patch for Flask-Session to fix bytes/string type mismatch in Python 3.13
"""
import sys
import logging
from flask_session import Session
from flask.sessions import SessionInterface

# Configure logging
logger = logging.getLogger(__name__)

# Store the original save_session method
original_save_session = SessionInterface.save_session

def patched_save_session(self, app, session, response):
    """
    Patched version of SessionInterface.save_session to handle
    bytes/string type mismatch in Python 3.13
    """
    try:
        if hasattr(app, 'logger'):
            app.logger.debug("Using patched SessionInterface.save_session")
        return original_save_session(self, app, session, response)
    except TypeError as e:
        error_msg = str(e)
        if "cannot use a string pattern on a bytes-like object" in error_msg:
            if hasattr(app, 'logger'):
                app.logger.info(f"Converting session ID from bytes to string: {error_msg}")
            # Convert the session ID to string if it's bytes
            if hasattr(session, 'sid') and isinstance(session.sid, bytes):
                session.sid = session.sid.decode('utf-8')
                if hasattr(app, 'logger'):
                    app.logger.info(f"Session ID converted to string: {session.sid}")
            return original_save_session(self, app, session, response)
        # If it's a different TypeError, log it but still raise
        if hasattr(app, 'logger'):
            app.logger.error(f"Unhandled TypeError in session handling: {error_msg}")
        raise

# Apply the monkey patch
if not hasattr(SessionInterface, '_patched_for_py313'):
    print(f"Applying SessionInterface.save_session patch for Python {sys.version_info.major}.{sys.version_info.minor}")
    SessionInterface.save_session = patched_save_session
    SessionInterface._patched_for_py313 = True
    print("Successfully applied SessionInterface.save_session patch")

def configure_session_interface(app):
    """
    Configure the session interface for the Flask app
    with the patched save_session method for Python 3.13 compatibility
    """
    # Apply Flask-Session configuration
    print("Configuring Flask-Session...")
    
    # Check if we're on Python 3.13
    is_py313 = sys.version_info.major == 3 and sys.version_info.minor == 13
    if is_py313:
        print("Running on Python 3.13 - applying session compatibility fixes")
    
    # Initialize Flask-Session
    try:
        session = Session(app)
        print("Flask-Session initialized successfully")
    except Exception as e:
        print(f"Warning: Error initializing Flask-Session: {e}")
        print("Attempting to continue...")
    
    # Make sure our patch is applied
    if SessionInterface.save_session != patched_save_session:
        print("Re-applying session_fix patch...")
        SessionInterface.save_session = patched_save_session
        SessionInterface._patched_for_py313 = True
        app.logger.info("Applied session_fix patch for Flask-Session compatibility with Python 3.13")
    else:
        print("Session patch already applied correctly")
    
    # Set a flag on the app to indicate our patch is applied
    app.config['SESSION_INTERFACE_PATCHED'] = True
    
    return app 