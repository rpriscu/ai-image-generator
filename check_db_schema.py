#!/usr/bin/env python3
"""
Database schema checker for Heroku deployment
"""
from app import create_app
from app.models.models import db
from sqlalchemy import inspect

def check_schema():
    app = create_app()
    
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        print("=== DATABASE SCHEMA ANALYSIS ===")
        print(f"Tables found: {tables}")
        
        for table in sorted(tables):
            print(f"\nTable: {table}")
            columns = inspector.get_columns(table)
            for col in columns:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                default = f" DEFAULT {col['default']}" if col['default'] else ""
                print(f"  {col['name']}: {col['type']} {nullable}{default}")
                
        # Check for foreign keys
        print("\n=== FOREIGN KEYS ===")
        for table in sorted(tables):
            fks = inspector.get_foreign_keys(table)
            if fks:
                print(f"Table {table}:")
                for fk in fks:
                    print(f"  {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")

if __name__ == "__main__":
    check_schema() 