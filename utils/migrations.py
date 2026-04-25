import os
import sqlite3
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def migrate_sandboxes():
    """Ensures all existing sandbox databases have the required columns."""
    if not os.path.exists(Config.SANDBOX_DIR):
        return

    print("Checking for sandbox migrations...")
    for sid in os.listdir(Config.SANDBOX_DIR):
        db_path = os.path.join(Config.SANDBOX_DIR, sid, 'db.sqlite')
        if not os.path.exists(db_path):
            continue

        try:
            conn = sqlite3.connect(db_path)
            # Check if sent_emails column exists
            cursor = conn.execute("PRAGMA table_info(users)")
            columns = [info[1] for info in cursor.fetchall()]
            
            if 'sent_emails' not in columns:
                print(f"Adding 'sent_emails' column to sandbox {sid}")
                conn.execute("ALTER TABLE users ADD COLUMN sent_emails INTEGER DEFAULT 0")
            
            if 'is_premium' not in columns:
                print(f"Adding 'is_premium' column to sandbox {sid}")
                conn.execute("ALTER TABLE users ADD COLUMN is_premium INTEGER DEFAULT 0")
            
            if 'active_theme' not in columns:
                print(f"Adding 'active_theme' column to sandbox {sid}")
                conn.execute("ALTER TABLE users ADD COLUMN active_theme TEXT DEFAULT 'default'")
                
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Failed to migrate sandbox {sid}: {str(e)}")

if __name__ == "__main__":
    migrate_sandboxes()
