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
        
        # Create a wrapper for the _cookie_no_quote_re.fullmatch function
        # instead of trying to replace the actual method which is read-only
        if hasattr(werkzeug_http, '_cookie_no_quote_re'):
            # We can't replace the fullmatch method directly since it's read-only
            # So instead create a custom wrapper function to handle the regexp matching
            
            def safe_fullmatch(pattern, string):
                """Safe wrapper around re.Pattern.fullmatch that handles string/bytes issues"""
                try:
                    # First try with original function
                    return pattern.fullmatch(string)
                except TypeError as e:
                    # If we have a bytes pattern and string input or vice versa
                    if isinstance(string, bytes):
                        try:
                            # Try to decode bytes to string
                            return pattern.fullmatch(string.decode('utf-8'))
                        except:
                            # If conversion fails, return None (no match)
                            return None
                    elif isinstance(string, str):
                        try:
                            # Try to encode string to bytes
                            return pattern.fullmatch(string.encode('utf-8'))
                        except:
                            # If conversion fails, return None (no match)
                            return None
                    else:
                        # If not string or bytes, return None (no match)
                        return None
            
            # Now monkey patch functions that use _cookie_no_quote_re.fullmatch
            
            # First, try to find functions in werkzeug.http that might use the pattern
            # The most likely candidate is _cookie_quote
            if hasattr(werkzeug_http, '_cookie_quote') and not hasattr(werkzeug_http._cookie_quote, '_patched_regex'):
                original_func = werkzeug_http._cookie_quote
                pattern = werkzeug_http._cookie_no_quote_re
                
                @functools.wraps(original_func)
                def regex_safe_func(string):
                    """Version of the function that uses our safe_fullmatch wrapper"""
                    # If the original implementation uses pattern.fullmatch(string),
                    # we replace that call with our safe version
                    match = safe_fullmatch(pattern, string)
                    if match:
                        return string
                    # Otherwise continue with original function
                    return original_func(string)
                
                # Mark as patched to avoid double patching
                regex_safe_func._patched_regex = True
                
                # Apply the patch
                werkzeug_http._cookie_quote = regex_safe_func
                print("Applied regex-safe patch to werkzeug.http._cookie_quote")
            
            print("Successfully handled _cookie_no_quote_re pattern matching")
        
        print("All Werkzeug patches applied successfully")
        return True
    except Exception as e:
        print(f"Error applying Werkzeug patches: {e}")
        return False

# The patch will only be applied for Python 3.13+
# This ensures it won't affect the Heroku environment
if __name__ == "__main__":
    patch_werkzeug_cookie_functions() 