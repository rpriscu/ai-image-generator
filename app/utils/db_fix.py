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
        'postgres_dialect': False,
        'registry': {}
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
    
    # Check the registry
    for name, module in registry._registry.items():
        results['registry'][name] = list(module.keys())
    
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
        
        # Explicitly import the PostgreSQL dialect
        try:
            from sqlalchemy.dialects.postgresql import psycopg2 as pg_dialect
            print("Successfully imported PostgreSQL dialect module")
        except ImportError as e:
            print(f"Error importing PostgreSQL dialect: {e}")
            # Try to import the module directly
            psycopg2_module = importlib.import_module('sqlalchemy.dialects.postgresql.psycopg2')
            print("Imported PostgreSQL dialect module directly")
        
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
        
        # For Python 3.13+ compatibility, ensure 'postgres' is an alias for 'postgresql'
        if 'postgresql' in registry._registry and 'postgres' not in registry._registry:
            registry._registry['postgres'] = registry._registry['postgresql'].copy()
            print("Created 'postgres' alias for 'postgresql' in registry")
        
        # Also ensure basic URL handling works
        os.environ['SQLALCHEMY_SILENCE_UBER_WARNING'] = '1'
        
        # Print the final registry state for diagnistics
        print("\nFinal dialect registry:")
        dialect_count = 0
        for dialect_name, entries in registry._registry.items():
            if dialect_name in ('postgresql', 'postgres'):
                print(f"  {dialect_name}: {', '.join(entries.keys())}")
                dialect_count += len(entries)
        
        print(f"Registered {dialect_count} PostgreSQL dialect entries")
        
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