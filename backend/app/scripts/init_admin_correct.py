"""
Correct admin portal data initialization script based on actual database structure
"""
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import engine, SessionLocal
from app.core.security import get_password_hash


def init_admin_data():
    """Initialize admin portal data with correct database structure"""

    # Create database session
    db = SessionLocal()

    try:
        print("Starting correct admin data initialization...")

        # 1. Ensure admin user exists in users table
        admin_email = "Laimiu.new@gmail.com"
        admin_password = "ghzzz123"

        # Check if admin user exists in users table
        result = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": admin_email}).fetchone()

        if not result:
            print(f"Creating admin user in users table: {admin_email}")

            # Insert into users table
            db.execute(text("""
                INSERT INTO users (email, username, full_name, hashed_password, is_active, is_verified, is_superuser, member_tier, created_at, updated_at)
                VALUES (:email, :username, :full_name, :hashed_password, :is_active, :is_verified, :is_superuser, :member_tier, :created_at, :updated_at)
                RETURNING id
            """), {
                "email": admin_email,
                "username": "admin",
                "full_name": "System Administrator",
                "hashed_password": get_password_hash(admin_password),
                "is_active": True,
                "is_verified": True,
                "is_superuser": True,
                "member_tier": "enterprise_pro_max",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })

            result = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": admin_email}).fetchone()
            print("Admin user created successfully in users table")
        else:
            print(f"Admin user already exists in users table: {admin_email}")

        # 2. Ensure admin user exists in admins table
        admin_result = db.execute(text("SELECT id FROM admins WHERE email = :email"), {"email": admin_email}).fetchone()

        if not admin_result:
            print(f"Creating admin user in admins table: {admin_email}")

            # Insert into admins table
            db.execute(text("""
                INSERT INTO admins (email, username, hashed_password, full_name, is_active, is_super_admin, admin_level, created_at, updated_at)
                VALUES (:email, :username, :hashed_password, :full_name, :is_active, :is_super_admin, :admin_level, :created_at, :updated_at)
            """), {
                "email": admin_email,
                "username": "admin",
                "hashed_password": get_password_hash(admin_password),
                "full_name": "System Administrator",
                "is_active": True,
                "is_super_admin": True,
                "admin_level": "super_admin",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })

            print("Admin user created successfully in admins table")
        else:
            print(f"Admin user already exists in admins table: {admin_email}")

        # 3. Create some test users
        test_users_data = [
            {
                "email": "test1@example.com",
                "username": "testuser1",
                "full_name": "Test User 1",
                "member_tier": "personal_pro"
            },
            {
                "email": "test2@example.com",
                "username": "testuser2",
                "full_name": "Test User 2",
                "member_tier": "personal_advanced"
            },
            {
                "email": "test3@example.com",
                "username": "testuser3",
                "full_name": "Test User 3",
                "member_tier": "free"
            },
            {
                "email": "enterprise@example.com",
                "username": "enterprise_user",
                "full_name": "Enterprise User",
                "member_tier": "enterprise"
            }
        ]

        created_count = 0
        for user_data in test_users_data:
            existing_user = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": user_data["email"]}).fetchone()
            if not existing_user:
                print(f"Creating test user: {user_data['email']}")

                db.execute(text("""
                    INSERT INTO users (email, username, full_name, hashed_password, is_active, is_verified, member_tier, created_at, updated_at)
                    VALUES (:email, :username, :full_name, :hashed_password, :is_active, :is_verified, :member_tier, :created_at, :updated_at)
                """), {
                    "email": user_data["email"],
                    "username": user_data["username"],
                    "full_name": user_data["full_name"],
                    "hashed_password": get_password_hash("password123"),
                    "is_active": True,
                    "is_verified": True,
                    "member_tier": user_data["member_tier"],
                    "created_at": datetime.utcnow() - timedelta(days=30),
                    "updated_at": datetime.utcnow()
                })
                created_count += 1

        print(f"Created {created_count} test users")

        # 4. Create system logs if table exists
        tables_result = db.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'system_logs'
        """)).fetchone()

        if tables_result:
            print("Creating system logs...")

            # Get admin ID from admins table
            admin_id_result = db.execute(text("SELECT id FROM admins WHERE email = :email"), {"email": admin_email}).fetchone()
            if admin_id_result:
                admin_id = admin_id_result[0]

                log_entries_data = [
                    {
                        "action": "User Login",
                        "details": "Administrator logged into system"
                    },
                    {
                        "action": "View User List",
                        "details": "Administrator viewed system user list"
                    },
                    {
                        "action": "System Monitoring",
                        "details": "Checked system running status"
                    }
                ]

                for log_data in log_entries_data:
                    db.execute(text("""
                        INSERT INTO system_logs (action, details, user_id, created_at)
                        VALUES (:action, :details, :user_id, :created_at)
                    """), {
                        "action": log_data["action"],
                        "details": log_data["details"],
                        "user_id": admin_id,
                        "created_at": datetime.utcnow() - timedelta(hours=1)
                    })

        # 5. Commit all changes
        db.commit()

        print("Admin data initialization completed successfully!")
        print(f"Admin account: {admin_email}")
        print(f"Admin password: {admin_password}")
        print("Test user password: password123")
        print("System is ready for admin portal usage!")

        return True

    except Exception as e:
        print(f"Initialization failed: {str(e)}")
        db.rollback()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    success = init_admin_data()
    if success:
        print("\nInitialization successful! You can now start the backend service and test the admin portal.")
    else:
        print("\nInitialization failed! Please check error messages and retry.")