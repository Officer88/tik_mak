
from app import app, db
from sqlalchemy import text

def migrate_popular_fields():
    try:
        with app.app_context():
            conn = db.engine.connect()
            
            # Get existing columns
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='event'"))
            columns = [row[0] for row in result]
            
            # Add is_popular if it doesn't exist
            if 'is_popular' not in columns:
                print("Adding column is_popular...")
                conn.execute(text("ALTER TABLE event ADD COLUMN is_popular BOOLEAN DEFAULT FALSE"))
            
            # Add is_featured if it doesn't exist
            if 'is_featured' not in columns:
                print("Adding column is_featured...")
                conn.execute(text("ALTER TABLE event ADD COLUMN is_featured BOOLEAN DEFAULT FALSE"))
            
            conn.commit()
            print("Migration successfully completed!")
            
    except Exception as e:
        print(f"Error during migration: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = migrate_popular_fields()
    import sys
    sys.exit(0 if success else 1)
