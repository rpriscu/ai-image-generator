#!/usr/bin/env python3
"""
Fix database schema by adding missing columns
"""
from app import create_app
from app.models.models import db
from sqlalchemy import text, inspect

def fix_schema():
    app = create_app()
    
    with app.app_context():
        inspector = inspect(db.engine)
        
        # Check if thumbnail_url column exists in asset table
        asset_columns = [col['name'] for col in inspector.get_columns('asset')]
        
        print(f"Current asset table columns: {asset_columns}")
        
        if 'thumbnail_url' not in asset_columns:
            print("Adding missing thumbnail_url column to asset table...")
            try:
                db.session.execute(text('ALTER TABLE asset ADD COLUMN thumbnail_url VARCHAR(512)'))
                db.session.commit()
                print("✅ Successfully added thumbnail_url column")
            except Exception as e:
                print(f"❌ Error adding thumbnail_url column: {e}")
        else:
            print("✅ thumbnail_url column already exists")
        
        # Verify the fix
        asset_columns_after = [col['name'] for col in inspector.get_columns('asset')]
        print(f"Asset table columns after fix: {asset_columns_after}")

if __name__ == "__main__":
    fix_schema() 