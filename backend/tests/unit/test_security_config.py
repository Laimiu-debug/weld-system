"""Production secret rejection and JWT signature enforcement."""
import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.security import create_access_token, verify_token


def _production_kwargs(**overrides):
    values = {
        "DEVELOPMENT": False,
        "DEBUG": False,
        "SECRET_KEY": "a-sufficiently-long-unique-production-secret-key-32",
        "DATABASE_PASSWORD": "unique-db-pass-not-leaked",
        "REDIS_PASSWORD": "unique-redis-pass-not-leaked",
        "DATABASE_URL": "postgresql://weld_user:unique-db-pass-not-leaked@postgres:5432/weld_db",
        "REDIS_URL": "redis://:unique-redis-pass-not-leaked@redis:6379/0",
    }
    values.update(overrides)
    return values


class TestProductionSecrets:
    def test_production_rejects_default_jwt_secret(self):
        with pytest.raises(ValidationError):
            Settings(
                _env_file=None,
                **_production_kwargs(
                    SECRET_KEY="dev-secret-key-for-testing-purposes-change-in-production"
                ),
            )

    def test_production_rejects_short_jwt_secret(self):
        with pytest.raises(ValidationError):
            Settings(_env_file=None, **_production_kwargs(SECRET_KEY="too-short"))

    def test_production_rejects_leaked_database_password(self):
        with pytest.raises(ValidationError):
            Settings(
                _env_file=None,
                **_production_kwargs(
                    DATABASE_PASSWORD="WeldDB@2024#Secure!Pass",
                    DATABASE_URL="postgresql://weld_user:WeldDB@2024#Secure!Pass@postgres:5432/weld_db",
                ),
            )

    def test_production_rejects_missing_redis_password(self):
        with pytest.raises(ValidationError):
            Settings(_env_file=None, **_production_kwargs(REDIS_PASSWORD=None))

    def test_production_accepts_strong_secrets(self):
        settings = Settings(_env_file=None, **_production_kwargs())
        assert settings.DEVELOPMENT is False
        assert len(settings.SECRET_KEY) >= 32


class TestVerifyToken:
    def test_signed_token_roundtrip(self):
        token = create_access_token(subject="42")
        assert verify_token(token, token_type="access") == "42"

    def test_unsigned_or_forged_token_is_rejected(self):
        forged = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiIzIiwidHlwZSI6ImFjY2VzcyJ9."
            "development-signature-for-testing-only"
        )
        assert verify_token(forged, token_type="access") is None
