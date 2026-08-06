"""Configuration for fleet-intelligence.

This module provides a small Settings dataclass and a helper to load
configuration from environment variables with sensible defaults.

Usage:
    from config.settings import settings
    print(settings.DATABASE_URL)
"""

import os
from dataclasses import dataclass
from typing import List, Optional


def _bool_env(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def _int_env(name: str, default: int = 0) -> int:
    v = os.getenv(name)
    try:
        return int(v) if v is not None else default
    except (ValueError, TypeError):
        return default


@dataclass
class Settings:
    SECRET_KEY: str = "change-me"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = "sqlite:///./fleet.db"
    REDIS_URL: Optional[str] = None
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    ALLOWED_HOSTS: List[str] = None
    ITEMS_PER_PAGE: int = 50


def load_settings() -> Settings:
    """Load settings from environment variables and return a Settings instance."""
    allowed = os.getenv("ALLOWED_HOSTS", "")
    allowed_list = [h.strip() for h in allowed.split(",") if h.strip()] if allowed else []

    return Settings(
        SECRET_KEY=os.getenv("SECRET_KEY", "change-me"),
        DEBUG=_bool_env("DEBUG", False),
        LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
        DATABASE_URL=os.getenv("DATABASE_URL", "sqlite:///./fleet.db"),
        REDIS_URL=os.getenv("REDIS_URL"),
        API_HOST=os.getenv("API_HOST", "0.0.0.0"),
        API_PORT=_int_env("API_PORT", 8000),
        ALLOWED_HOSTS=allowed_list,
        ITEMS_PER_PAGE=_int_env("ITEMS_PER_PAGE", 50),
    )


# module-level default
settings = load_settings()


__all__ = ["Settings", "settings", "load_settings"]
