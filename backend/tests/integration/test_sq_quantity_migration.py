"""Exercise the quantity migration on a temporary table in a local QA schema."""
import importlib.util
import os
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import text
from test_foundation_integrity import sessions

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LOCAL_DB_TESTS") != "1", reason="local PostgreSQL opt-in"
)


def test_unknown_quantity_migration_and_safe_downgrade(sessions):
    path = Path(__file__).parents[2] / "alembic/versions/allow_unknown_part_quantity.py"
    spec = importlib.util.spec_from_file_location("quantity_migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    with sessions.kw["bind"].begin() as connection:
        connection.execute(
            text("CREATE TEMP TABLE parts (quantity integer NOT NULL) ON COMMIT DROP")
        )
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
            connection.execute(
                text("INSERT INTO pg_temp.parts(quantity) VALUES (NULL)")
            )
            with pytest.raises(RuntimeError, match="人工补齐"):
                migration.downgrade()
            connection.execute(text("UPDATE pg_temp.parts SET quantity=2"))
            migration.downgrade()
        assert connection.execute(
            text(
                "SELECT attnotnull FROM pg_attribute WHERE attrelid='pg_temp.parts'::regclass AND attname='quantity'"
            )
        ).scalar()


def test_treatment_plan_migration_preserves_saved_plans(sessions):
    path = Path(__file__).parents[2] / "alembic/versions/add_sequence_treatment_plan.py"
    spec = importlib.util.spec_from_file_location("treatment_migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    with sessions.kw["bind"].begin() as connection:
        connection.execute(
            text("CREATE TEMP TABLE weld_requirements (id integer) ON COMMIT DROP")
        )
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
            connection.execute(
                text(
                    'INSERT INTO pg_temp.weld_requirements VALUES (1, \'[{"code":"H1"}]\'::jsonb)'
                )
            )
            with pytest.raises(RuntimeError, match="不能直接降级"):
                migration.downgrade()
            connection.execute(
                text("UPDATE pg_temp.weld_requirements SET treatment_plan='[]'::jsonb")
            )
            migration.downgrade()
        assert not connection.execute(
            text(
                "SELECT 1 FROM pg_attribute WHERE attrelid='pg_temp.weld_requirements'::regclass AND attname='treatment_plan' AND NOT attisdropped"
            )
        ).first()
