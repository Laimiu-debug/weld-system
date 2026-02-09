#!/usr/bin/env python
"""
Execute the modules_data migration to add the new JSONB field to WPS table.
"""
import os
import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import engine

def execute_migration():
    """Execute the modules_data migration."""
    migration_file = Path(__file__).parent / "migrations" / "add_modules_data_field.sql"

    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False

    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        print("📝 Executing migration: add_modules_data_field.sql")
        print("-" * 60)

        from sqlalchemy import text

        with engine.connect() as connection:
            # Split SQL statements and execute them individually
            statements = [s.strip() for s in sql_content.split(';') if s.strip()]

            for statement in statements:
                if statement and not statement.startswith('--'):
                    print(f"Executing: {statement[:80]}...")
                    connection.execute(text(statement))

            connection.commit()

        print("✅ Migration executed successfully!")
        print("-" * 60)
        return True

    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        print("-" * 60)
        return False

if __name__ == "__main__":
    success = execute_migration()
    sys.exit(0 if success else 1)

