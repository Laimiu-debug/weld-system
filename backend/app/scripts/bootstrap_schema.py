"""One-off empty-database bootstrap. Do not call this on every startup.

Creates tables from SQLAlchemy metadata, then stamps Alembic head so later
`alembic upgrade head` can apply incremental revisions.
"""
from alembic import command
from alembic.config import Config

from app.core.database import Base, engine
import app.models  # noqa: F401
from app.models import equipment, material, production, quality, role, wps  # noqa: F401


def main() -> None:
    Base.metadata.create_all(bind=engine)
    alembic_cfg = Config("alembic.ini")
    command.stamp(alembic_cfg, "head")
    print("Schema created and Alembic stamped at head.")


if __name__ == "__main__":
    main()
