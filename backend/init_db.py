"""
Initialize database tables for the welding system backend.
"""
from app.core.database import engine, Base
from app.models.user import User
from app.models.role import Role, Permission
from app.models.wps import WPS, WPSRevision
from app.models.pqr import PQR, PQRTestSpecimen

def create_tables():
    """创建所有数据库表."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    # Initialize default roles and permissions
    print("Initializing default roles and permissions...")
    from app.services.role_service import role_service
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        role_service.initialize_default_roles(db)
        print("Default roles and permissions initialized successfully!")
    except Exception as e:
        print(f"Error initializing roles and permissions: {e}")
        db.rollback()
    finally:
        db.close()

    print("Database tables created successfully!")

if __name__ == "__main__":
    create_tables()