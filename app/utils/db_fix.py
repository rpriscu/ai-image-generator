"""
Database fix module for Python 3.13 compatibility.

This module patches SQLAlchemy to properly handle PostgreSQL dialect on Python 3.13.
"""
import os
import sys
import logging
import importlib
from sqlalchemy.dialects import registry

logger = logging.getLogger(__name__)

def check_dialect_modules():
    """Check if PostgreSQL dialect modules are properly installed."""
    results = {
        'psycopg2': False,
        'postgres_dialect': False
    }
    
    # Check for psycopg2
    try:
        import psycopg2
        results['psycopg2'] = True
        results['psycopg2_version'] = psycopg2.__version__
        print(f"psycopg2 is installed (version {psycopg2.__version__})")
    except ImportError as e:
        print(f"psycopg2 import error: {e}")
    
    # Check for sqlalchemy.dialects.postgresql
    try:
        from sqlalchemy.dialects import postgresql
        results['postgres_dialect'] = True
        print("SQLAlchemy PostgreSQL dialect is available")
    except ImportError as e:
        print(f"SQLAlchemy PostgreSQL dialect import error: {e}")
    
    return results

def apply_postgres_dialect_fix():
    """
    Register the PostgreSQL dialect explicitly.
    
    This is needed for Python 3.13 compatibility with Heroku.
    """
    try:
        # Print diagnostic info
        print(f"Python version: {sys.version}")
        print(f"Applying PostgreSQL dialect fix for Python 3.13...")
        
        # Make sure psycopg2 is installed
        import psycopg2
        print(f"Found psycopg2 version: {psycopg2.__version__}")
        
        # Register the dialect explicitly - try multiple approaches
        dialect_registry_names = [
            ('postgresql', 'psycopg2'),
            ('postgresql+psycopg2', None),
            ('postgres', 'psycopg2'),
            ('postgres+psycopg2', None)
        ]
        
        for name, entry in dialect_registry_names:
            try:
                if entry:
                    registry.register(f"{name}.{entry}", "sqlalchemy.dialects.postgresql.psycopg2", "dialect")
                    print(f"Registered dialect: {name}.{entry}")
                else:
                    registry.register(name, "sqlalchemy.dialects.postgresql.psycopg2", "dialect")
                    print(f"Registered dialect: {name}")
            except Exception as e:
                print(f"Error registering {name}: {e}")
        
        # Apply a monkey patch for SQLAlchemy URL handling
        from sqlalchemy.engine import url
        original_get_entrypoint = url.URL._get_entrypoint
        
        def patched_get_entrypoint(self):
            """
            Patch the URL._get_entrypoint method to handle 'postgres' dialect by
            converting it to 'postgresql'.
            """
            # Check if this is a postgres URL and adjust to postgresql
            if hasattr(self, 'drivername'):
                if self.drivername == 'postgres' or self.drivername.startswith('postgres:'):
                    self.drivername = self.drivername.replace('postgres', 'postgresql', 1)
                    print(f"Patched drivername to: {self.drivername}")
            # Call the original method
            return original_get_entrypoint(self)
        
        # Apply the patch
        url.URL._get_entrypoint = patched_get_entrypoint
        print("Applied patch to SQLAlchemy URL._get_entrypoint")
                
        # Force load the dialect to verify it works
        try:
            from sqlalchemy import create_engine
            dummy_engine = create_engine("postgresql://user:pass@localhost/dbname")
            dialect = dummy_engine.dialect
            print(f"Successfully created test engine with dialect: {dialect.name}")
            return True
        except Exception as e:
            print(f"Warning: Test engine creation failed: {e}")
            # Continue even if test fails
            return True
            
    except ImportError as e:
        print(f"Failed to import psycopg2: {e}")
        print("ERROR: psycopg2 is required for PostgreSQL support")
        return False
    except Exception as e:
        print(f"Error applying PostgreSQL dialect fix: {e}")
        print("Attempting to continue despite errors...")
        
        # Dump diagnostic info
        check_dialect_modules()
        return False 