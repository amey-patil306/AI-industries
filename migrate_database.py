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
                'intrusion_detection': 'BOOLEAN DEFAULT 0',
                'leakage_detection': 'BOOLEAN DEFAULT 0',
                'activity_monitoring': 'BOOLEAN DEFAULT 0',
                'defect_detection': 'BOOLEAN DEFAULT 0',
                'crowd_detection': 'BOOLEAN DEFAULT 0',
                'air_quality_monitoring': 'BOOLEAN DEFAULT 0'
            }
            
            for column_name, column_def in new_columns.items():
                if column_name not in columns:
                    try:
                        cursor.execute(f"ALTER TABLE camera ADD COLUMN {column_name} {column_def};")
                        print(f"✅ Added column: {column_name}")
                    except sqlite3.OperationalError as e:
                        print(f"⚠️ Column {column_name} might already exist: {e}")
            
            # Update Alert table to add new columns
            cursor.execute("PRAGMA table_info(alert);")
            alert_columns = [column[1] for column in cursor.fetchall()]
            
            alert_new_columns = {
                'severity': 'VARCHAR(20) DEFAULT "medium"',
                'description': 'TEXT',
                'camera_id': 'VARCHAR(100)',
                'confidence': 'FLOAT DEFAULT 0.0'
            }
            
            for column_name, column_def in alert_new_columns.items():
                if column_name not in alert_columns:
                    try:
                        cursor.execute(f"ALTER TABLE alert ADD COLUMN {column_name} {column_def};")
                        print(f"✅ Added alert column: {column_name}")
                    except sqlite3.OperationalError as e:
                        print(f"⚠️ Alert column {column_name} might already exist: {e}")
        else:
            print("❌ Camera table does not exist. Creating new tables...")
            # If table doesn't exist, create it with all columns
            create_tables()
        
        conn.commit()
        print("🎉 Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        conn.rollback()
    finally:
        conn.close()

def create_tables():
    """Create all tables with complete schema"""
    conn = sqlite3.connect('instance/user.db')
    cursor = conn.cursor()
    
    try:
        # Create User table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(100) UNIQUE,
                password VARCHAR(100),
                email VARCHAR(100)
            )
        ''')
        
        # Create Camera table with all columns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS camera (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                cam_id VARCHAR(100),
                fire_detection BOOLEAN DEFAULT 0,
                smoke_detection BOOLEAN DEFAULT 0,
                pose_alert BOOLEAN DEFAULT 0,
                restricted_zone BOOLEAN DEFAULT 0,
                safety_gear_detection BOOLEAN DEFAULT 0,
                enhanced_gear_detection BOOLEAN DEFAULT 0,
                intrusion_detection BOOLEAN DEFAULT 0,
                leakage_detection BOOLEAN DEFAULT 0,
                activity_monitoring BOOLEAN DEFAULT 0,
                defect_detection BOOLEAN DEFAULT 0,
                crowd_detection BOOLEAN DEFAULT 0,
                air_quality_monitoring BOOLEAN DEFAULT 0,
                region BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        ''')
        
        # Create Alert table with all columns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alert (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date_time DATETIME,
                alert_type VARCHAR(50),
                severity VARCHAR(20) DEFAULT 'medium',
                frame_snapshot BLOB,
                description TEXT,
                camera_id VARCHAR(100),
                confidence FLOAT DEFAULT 0.0,
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        ''')
        
        # Create SystemMetrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_cameras INTEGER DEFAULT 0,
                active_alerts INTEGER DEFAULT 0,
                system_uptime FLOAT DEFAULT 0.0,
                detection_accuracy FLOAT DEFAULT 0.0
            )
        ''')
        
        conn.commit()
        print("✅ All tables created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
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
            print(f"🗑️ Deleted {db_file}")
    
    print("🔄 Database reset completed. Run the app to recreate tables.")

def check_database_status():
    """Check current database status and columns"""
    if not os.path.exists('instance/user.db'):
        print("❌ Database does not exist!")
        return
    
    conn = sqlite3.connect('instance/user.db')
    cursor = conn.cursor()
    
    try:
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📊 Existing tables: {[table[0] for table in tables]}")
        
        # Check camera table columns
        if any('camera' in table for table in tables):
            cursor.execute("PRAGMA table_info(camera);")
            columns = cursor.fetchall()
            print(f"🎥 Camera table columns: {[col[1] for col in columns]}")
        
        # Check alert table columns
        if any('alert' in table for table in tables):
            cursor.execute("PRAGMA table_info(alert);")
            columns = cursor.fetchall()
            print(f"🚨 Alert table columns: {[col[1] for col in columns]}")
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔧 Database Migration Tool for IndustrialAI")
    print("=" * 50)
    print("1. Migrate existing database (recommended)")
    print("2. Reset database (WARNING: Deletes all data)")
    print("3. Check database status")
    print("4. Create fresh database")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        print("\n🔄 Starting database migration...")
        migrate_database()
    elif choice == "2":
        confirm = input("⚠️ Are you sure you want to delete all data? Type 'YES' to confirm: ")
        if confirm == "YES":
            reset_database()
        else:
            print("❌ Reset cancelled.")
    elif choice == "3":
        print("\n📊 Checking database status...")
        check_database_status()
    elif choice == "4":
        print("\n🆕 Creating fresh database...")
        reset_database()
        create_tables()
    else:
        print("❌ Invalid choice.")