"""Helpers for one-off bootstrap scripts. Do not hardcode production passwords."""
import os
import sys

from app.core.config import LEAKED_PASSWORDS


def require_admin_initial_password() -> str:
    password = os.environ.get("ADMIN_INITIAL_PASSWORD")
    if not password:
        print(
            "ADMIN_INITIAL_PASSWORD is required. "
            "The previous default password was leaked and must be rotated.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    if password in LEAKED_PASSWORDS:
        print(
            "Refusing a leaked or weak ADMIN_INITIAL_PASSWORD. Choose a new unique value.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return password
