#!/usr/bin/env python3
"""
PostgreSQL database setup script
Creates weld_db database and weld_user user
"""

import psycopg2
import sys

def setup_postgresql():
    """Setup PostgreSQL database"""

    # Connect to PostgreSQL default database (usually postgres)
    try:
        # First try to connect with postgres user
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='postgres',  # Default database
            user='postgres',
            password='ghzzz123'
        )
        conn.autocommit = True  # Auto-commit for creating databases
        cursor = conn.cursor()
        print("SUCCESS: Connected to PostgreSQL")

    except psycopg2.OperationalError as e:
        print(f"ERROR: Failed to connect to PostgreSQL: {e}")
        print("Please check if PostgreSQL is running and username/password are correct")
        return False

    try:
        # Create user if not exists
        try:
            cursor.execute("""
                CREATE USER weld_user WITH PASSWORD 'weld_password';
            """)
            print("SUCCESS: Created user weld_user")
        except psycopg2.errors.DuplicateObject:
            print("INFO: User weld_user already exists")

        # Create database if not exists
        try:
            cursor.execute("""
                CREATE DATABASE weld_db OWNER weld_user;
            """)
            print("SUCCESS: Created database weld_db")
        except psycopg2.errors.DuplicateDatabase:
            print("INFO: Database weld_db already exists")

        # Grant privileges to user
        cursor.execute("""
            GRANT ALL PRIVILEGES ON DATABASE weld_db TO weld_user;
        """)
        print("SUCCESS: Granted privileges")

        # Connect to weld_db and create extensions
        conn.close()
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='weld_db',
            user='weld_user',
            password='weld_password'
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Create UUID extension
        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
            print("SUCCESS: Created UUID extension")
        except Exception as e:
            print(f"WARNING: Failed to create UUID extension: {e}")

        cursor.close()
        conn.close()

        print("\nPostgreSQL database setup completed!")
        print("Database info:")
        print("  Host: localhost")
        print("  Port: 5432")
        print("  Database: weld_db")
        print("  User: weld_user")
        print("  Password: weld_password")

        return True

    except Exception as e:
        print(f"ERROR: Failed to setup database: {e}")
        return False

if __name__ == "__main__":
    success = setup_postgresql()
    sys.exit(0 if success else 1)