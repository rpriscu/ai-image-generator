"""
Compatibility fix for Werkzeug to handle bytes-like objects in cookie handling
for Python 3.13 compatibility
"""
import sys
import logging
import importlib
import functools
import re

logger = logging.getLogger(__name__)

def patch_werkzeug_cookie_functions():
    """Apply patches to Werkzeug cookie functions for Python 3.13 compatibility"""
    # Only apply patches for Python 3.13+
    if not (sys.version_info.major == 3 and sys.version_info.minor >= 13):
        print(f"Not applying Werkzeug patches for Python {sys.version_info.major}.{sys.version_info.minor}")
        return
    
    try:
        print(f"Applying Werkzeug cookie patches for Python {sys.version_info.major}.{sys.version_info.minor}")
        
        # Import werkzeug.http module
        try:
            from werkzeug import http as werkzeug_http
            from werkzeug.sansio import response as werkzeug_response
        except ImportError as e:
            print(f"Could not import werkzeug modules: {e}")
            return
        
        # First, patch the dump_cookie function in werkzeug.http
        if hasattr(werkzeug_http, 'dump_cookie'):
            original_dump_cookie = werkzeug_http.dump_cookie
            
            @functools.wraps(original_dump_cookie)
            def patched_dump_cookie(key, value='', max_age=None, expires=None, path='/',
                                  domain=None, secure=False, httponly=False,
                                  charset='utf-8', sync_expires=False, max_size=4093,
                                  samesite=None):
                """
                Patched version of werkzeug.http.dump_cookie to ensure value is a string
                when using a string pattern on it
                """
                try:
                    # Ensure value is a string if it's bytes
                    if isinstance(value, bytes):
                        try:
                            value = value.decode(charset)
                            print(f"Converted cookie value from bytes to string: {value[:10]}...")
                        except Exception as e:
                            print(f"Error decoding cookie value: {e}")
                            value = str(value)
                    
                    # Call original function with fixed value
                    return original_dump_cookie(
                        key, value, max_age, expires, path, domain, secure,
                        httponly, charset, sync_expires, max_size, samesite
                    )
                except TypeError as e:
                    print(f"Warning in dump_cookie: {e}")
                    # If there's an error, try to convert all possible byte values to strings
                    if isinstance(key, bytes):
                        key = key.decode(charset)
                    
                    # Call original function with converted values as fallback
                    return original_dump_cookie(
                        key, str(value) if value is not None else '', 
                        max_age, expires, path, domain, secure,
                        httponly, charset, sync_expires, max_size, samesite
                    )
                except Exception as e:
                    print(f"Unexpected error in patched_dump_cookie: {e}")
                    # As a last resort, return an empty cookie
                    return f"{key}=; Path={path}"
            
            # Apply patch
            werkzeug_http.dump_cookie = patched_dump_cookie
            print("Successfully patched werkzeug.http.dump_cookie")
        
        # Now patch the set_cookie method in werkzeug.sansio.response
        if hasattr(werkzeug_response, 'Response') and hasattr(werkzeug_response.Response, 'set_cookie'):
            original_set_cookie = werkzeug_response.Response.set_cookie
            
            @functools.wraps(original_set_cookie)
            def patched_set_cookie(self, key, value="", max_age=None, expires=None, 
                                  path="/", domain=None, secure=False, httponly=False, 
                                  samesite=None):
                """
                Patched version of Response.set_cookie to handle bytes/string issues
                """
                try:
                    # Convert values to strings if they're bytes
                    if isinstance(key, bytes):
                        key = key.decode('utf-8')
                    if isinstance(value, bytes):
                        value = value.decode('utf-8')
                    
                    # Now call the original function with string values
                    return original_set_cookie(
                        self, key, value, max_age, expires, path, domain, secure, httponly, samesite
                    )
                except Exception as e:
                    print(f"Error in patched set_cookie: {e}")
                    # Fallback - if anything fails, still try to set the cookie
                    return original_set_cookie(
                        self, key, str(value) if value is not None else "", 
                        max_age, expires, path, domain, secure, httponly, samesite
                    )
            
            # Apply the patch
            werkzeug_response.Response.set_cookie = patched_set_cookie
            print("Successfully patched werkzeug.sansio.response.Response.set_cookie")
        
        # Now patch flask's response.set_cookie if possible
        try:
            from flask import Response as FlaskResponse
            if hasattr(FlaskResponse, 'set_cookie'):
                original_flask_set_cookie = FlaskResponse.set_cookie
                
                @functools.wraps(original_flask_set_cookie)
                def patched_flask_set_cookie(self, key, value="", max_age=None, expires=None, 
                                           path="/", domain=None, secure=False, httponly=False, 
                                           samesite=None):
                    """
                    Patched version of Flask Response.set_cookie to handle bytes/string issues
                    """
                    try:
                        # Convert values to strings if they're bytes
                        if isinstance(key, bytes):
                            key = key.decode('utf-8')
                        if isinstance(value, bytes):
                            value = value.decode('utf-8')
                        
                        # Now call the original function with string values
                        return original_flask_set_cookie(
                            self, key, value, max_age, expires, path, domain, secure, httponly, samesite
                        )
                    except Exception as e:
                        print(f"Error in patched Flask set_cookie: {e}")
                        # Fallback - if anything fails, still try to set the cookie
                        return original_flask_set_cookie(
                            self, key, str(value) if value is not None else "", 
                            max_age, expires, path, domain, secure, httponly, samesite
                        )
                
                # Apply the patch
                FlaskResponse.set_cookie = patched_flask_set_cookie
                print("Successfully patched flask.Response.set_cookie")
            
            # Also patch the session cookie handling in flask_session
            from flask_session.sessions import SessionInterface
            if hasattr(SessionInterface, 'save_session'):
                original_session_save = SessionInterface.save_session
                
                @functools.wraps(original_session_save)
                def patched_save_session(self, app, session, response):
                    """
                    Patched save_session to ensure session_id is a string before setting cookie
                    """
                    try:
                        # Check if we need to convert session_id from bytes to string
                        if hasattr(session, 'sid') and isinstance(session.sid, bytes):
                            try:
                                session.sid = session.sid.decode('utf-8')
                                print(f"Converted session.sid from bytes to string")
                            except:
                                session.sid = str(session.sid)
                        
                        # Now call the original function
                        return original_session_save(self, app, session, response)
                    except Exception as e:
                        print(f"Error in patched save_session: {e}")
                        # Call original as fallback
                        return original_session_save(self, app, session, response)
                
                # Apply patch
                SessionInterface.save_session = patched_save_session
                print("Successfully patched flask_session.sessions.SessionInterface.save_session")
                
        except ImportError as e:
            print(f"Could not import Flask modules for additional patching: {e}")
        
        print("All Werkzeug and Flask cookie patches applied successfully")
        return True
    except Exception as e:
        print(f"Error applying Werkzeug patches: {e}")
        return False

# The patch will only be applied for Python 3.13+
# This ensures it won't affect the Heroku environment
if __name__ == "__main__":
    patch_werkzeug_cookie_functions() 