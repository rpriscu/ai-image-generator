"""
Monkey patch for Flask-Session to fix bytes/string type mismatch
"""
from flask_session import Session
from flask.sessions import SessionInterface

# Store the original save_session method
original_save_session = SessionInterface.save_session

def patched_save_session(self, app, session, response):
    try:
        return original_save_session(self, app, session, response)
    except TypeError as e:
        if "cannot use a string pattern on a bytes-like object" in str(e):
            # Convert the session ID to string if it's bytes
            if hasattr(session, 'sid') and isinstance(session.sid, bytes):
                session.sid = session.sid.decode('utf-8')
            return original_save_session(self, app, session, response)
        raise

# Apply the monkey patch
SessionInterface.save_session = patched_save_session 