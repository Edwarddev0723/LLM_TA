"""
Migration script to add new columns to error_records table.
Run this script to update the existing database schema.
"""
import sqlite3
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ai_math_tutor.db")


def migrate():
    """Add missing columns to error_records table."""
    print(f"Migrating database: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print("Database file not found. It will be created on first run.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get existing columns
    cursor.execute("PRAGMA table_info(error_records)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    print(f"Existing columns: {existing_columns}")
    
    # Columns to add with their definitions
    new_columns = [
        ("session_id", "VARCHAR REFERENCES sessions(id)"),
        ("concept", "VARCHAR"),
        ("unit", "VARCHAR"),
        ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
        ("is_repaired", "BOOLEAN DEFAULT 0"),
        ("recurrence_count", "INTEGER DEFAULT 0"),
    ]
    
    for col_name, col_def in new_columns:
        if col_name not in existing_columns:
            try:
                sql = f"ALTER TABLE error_records ADD COLUMN {col_name} {col_def}"
                print(f"Adding column: {col_name}")
                cursor.execute(sql)
                print(f"  ✓ Added {col_name}")
            except sqlite3.OperationalError as e:
                print(f"  ✗ Error adding {col_name}: {e}")
        else:
            print(f"  - Column {col_name} already exists")
    
    conn.commit()
    conn.close()
    print("\nMigration complete!")


if __name__ == "__main__":
    migrate()
