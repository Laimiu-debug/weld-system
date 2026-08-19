"""One-off empty-database bootstrap. Do not call this on every startup."""
import importlib
import pkgutil

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.core.database import Base, SessionLocal, engine


def import_all_models() -> None:
    """Register every model table on the shared SQLAlchemy metadata."""
    import app.models as models_package

    for module in pkgutil.iter_modules(models_package.__path__):
        if not module.name.startswith("_"):
            importlib.import_module(f"app.models.{module.name}")


def main() -> None:
    """Create and seed the schema only when the target database is empty."""
    import_all_models()
    if inspect(engine).get_table_names():
        raise RuntimeError(
            "Database is not empty; use `alembic upgrade head` instead"
        )

    Base.metadata.create_all(bind=engine)
    alembic_cfg = Config("alembic.ini")
    command.stamp(alembic_cfg, "head")

    from app.services.role_service import role_service

    db = SessionLocal()
    try:
        role_service.initialize_default_roles(db)
    finally:
        db.close()

    print("Schema created, seeded, and Alembic stamped at head.")


if __name__ == "__main__":
    main()
