import sqlite3
import os

def migrate_database():
    """
    Migrate existing database to add new columns for enhanced features
    """
    db_paths = [
        'instance/user.db',
        'instance/cams.db', 
        'instance/alerts.db'
    ]
    
    # Create instance directory if it doesn't exist
    os.makedirs('instance', exist_ok=True)
    
    # Connect to the main database (user.db contains all tables)
    conn = sqlite3.connect('instance/user.db')
    cursor = conn.cursor()
    
    try:
        # Check if camera table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='camera';")
        table_exists = cursor.fetchone()
        
        if table_exists:
            # Get current columns
            cursor.execute("PRAGMA table_info(camera);")
            columns = [column[1] for column in cursor.fetchall()]
            print(f"Current columns: {columns}")
            
            # Add missing columns one by one
            new_columns = {
                'smoke_detection': 'BOOLEAN DEFAULT 0',
                'enhanced_gear_detection': 'BOOLEAN DEFAULT 0', 
                'intrusion_detection': 'BOOLEAN DEFAULT 0'
            }
            
            for column_name, column_def in new_columns.items():
                if column_name not in columns:
                    try:
                        cursor.execute(f"ALTER TABLE camera ADD COLUMN {column_name} {column_def};")
                        print(f"Added column: {column_name}")
                    except sqlite3.OperationalError as e:
                        print(f"Column {column_name} might already exist: {e}")
            
            # Update Alert table to add new columns
            cursor.execute("PRAGMA table_info(alert);")
            alert_columns = [column[1] for column in cursor.fetchall()]
            
            alert_new_columns = {
                'severity': 'VARCHAR(20) DEFAULT "medium"',
                'description': 'TEXT'
            }
            
            for column_name, column_def in alert_new_columns.items():
                if column_name not in alert_columns:
                    try:
                        cursor.execute(f"ALTER TABLE alert ADD COLUMN {column_name} {column_def};")
                        print(f"Added alert column: {column_name}")
                    except sqlite3.OperationalError as e:
                        print(f"Alert column {column_name} might already exist: {e}")
        
        conn.commit()
        print("Database migration completed successfully!")
        
    except Exception as e:
        print(f"Migration error: {e}")
        conn.rollback()
    finally:
        conn.close()

def reset_database():
    """
    Reset database by deleting existing files (WARNING: This will delete all data!)
    """
    db_files = [
        'instance/user.db',
        'instance/cams.db',
        'instance/alerts.db'
    ]
    
    for db_file in db_files:
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"Deleted {db_file}")
    
    print("Database reset completed. Run the app to recreate tables.")

if __name__ == "__main__":
    print("Database Migration Tool")
    print("1. Migrate existing database (recommended)")
    print("2. Reset database (WARNING: Deletes all data)")
    
    choice = input("Enter your choice (1 or 2): ").strip()
    
    if choice == "1":
        migrate_database()
    elif choice == "2":
        confirm = input("Are you sure you want to delete all data? Type 'YES' to confirm: ")
        if confirm == "YES":
            reset_database()
        else:
            print("Reset cancelled.")
    else:
        print("Invalid choice.")