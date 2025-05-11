"""
Compatibility fix for Werkzeug to handle bytes-like objects in cookie handling
for Python 3.13 compatibility
"""
import sys
import logging
import importlib
import functools

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
        except ImportError:
            print("Could not import werkzeug.http module")
            return
        
        # Check if dump_cookie exists
        if not hasattr(werkzeug_http, 'dump_cookie'):
            print("werkzeug.http.dump_cookie function not found")
            return
        
        # Store original function
        original_dump_cookie = werkzeug_http.dump_cookie
        
        # Create patched function
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
                    value = value.decode(charset)
                
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
        
        # Now also patch _cookie_quote function if it exists
        if hasattr(werkzeug_http, '_cookie_quote'):
            original_cookie_quote = werkzeug_http._cookie_quote
            
            @functools.wraps(original_cookie_quote)
            def patched_cookie_quote(b):
                """Ensure we have a proper string or bytes before quoting"""
                try:
                    # First try with original function
                    return original_cookie_quote(b)
                except TypeError as e:
                    # If bytes/string mismatch, convert appropriately and retry
                    if isinstance(b, bytes):
                        try:
                            return original_cookie_quote(b.decode('utf-8'))
                        except Exception:
                            # If conversion fails, use str() as fallback
                            return original_cookie_quote(str(b))
                    elif isinstance(b, str):
                        try:
                            return original_cookie_quote(b.encode('utf-8'))
                        except Exception:
                            # If conversion fails, use str() as fallback
                            return original_cookie_quote(str(b))
                    # For other types, use str() as fallback
                    return original_cookie_quote(str(b))
                
            # Apply patch
            werkzeug_http._cookie_quote = patched_cookie_quote
            print("Successfully patched werkzeug.http._cookie_quote")
        
        # Check if we also need to patch the _cookie_no_quote_re function
        if hasattr(werkzeug_http, '_cookie_no_quote_re') and hasattr(werkzeug_http._cookie_no_quote_re, 'fullmatch'):
            original_fullmatch = werkzeug_http._cookie_no_quote_re.fullmatch
            
            def patched_fullmatch(string):
                """Ensure we have a string before matching"""
                try:
                    # First try with original function
                    return original_fullmatch(string)
                except TypeError as e:
                    # If we have a bytes pattern and string input or vice versa
                    if isinstance(string, bytes):
                        try:
                            # Try to decode bytes to string
                            return original_fullmatch(string.decode('utf-8'))
                        except:
                            # If conversion fails, return None (no match)
                            return None
                    elif isinstance(string, str):
                        try:
                            # Try to encode string to bytes
                            return original_fullmatch(string.encode('utf-8'))
                        except:
                            # If conversion fails, return None (no match)
                            return None
                    else:
                        # If not string or bytes, return None (no match)
                        return None
            
            # Apply patch
            werkzeug_http._cookie_no_quote_re.fullmatch = patched_fullmatch
            print("Successfully patched werkzeug.http._cookie_no_quote_re.fullmatch")
        
        print("All Werkzeug patches applied successfully")
        return True
    except Exception as e:
        print(f"Error applying Werkzeug patches: {e}")
        return False

# The patch will only be applied for Python 3.13+
# This ensures it won't affect the Heroku environment
if __name__ == "__main__":
    patch_werkzeug_cookie_functions() 