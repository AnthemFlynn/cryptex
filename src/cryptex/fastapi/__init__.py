"""FastAPI integration for Cryptex middleware."""

from .middleware import (
    CryptexMiddleware,
    CodenameMiddleware,  # Legacy alias
    FastAPIAppProtection,
    setup_cryptex_protection,
    setup_codename_protection,  # Legacy alias
    create_protected_app
)

__all__ = [
    "CryptexMiddleware",
    "CodenameMiddleware",  # Legacy alias
    "FastAPIAppProtection",
    "setup_cryptex_protection",
    "setup_codename_protection",  # Legacy alias
    "create_protected_app"
]