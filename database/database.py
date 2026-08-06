"""database/database.py

Basic SQLAlchemy setup for the project.

- Reads DATABASE_URL from environment (defaults to SQLite file ./fleet.db)
- Exposes `engine`, `SessionLocal`, `Base`, `get_session()` and `init_db()` utilities

Adjust DATABASE_URL and models import as needed for your project.
"""
from __future__ import annotations

import os
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Read database URL from environment or default to a local SQLite file
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fleet.db")

# SQLAlchemy engine and session factory
# echo=True can be enabled for SQL logging while debugging
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for models
Base = declarative_base()


def get_session() -> Iterator[SessionLocal]:
    """Yield a SQLAlchemy session and ensure it's closed after use.

    Use with dependency-injection frameworks or as a context manager:

        with get_session() as session:
            ...

    or in FastAPI dependencies:

        def db_dep():
            with get_session() as db:
                yield db
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(import_models: bool = True) -> None:
    """Create database tables for all imported models.

    If your models are defined in other modules, ensure they are imported
    before calling init_db(). Example:

        # in your app startup
        import app.models  # registers models with Base
        init_db()
    """
    if import_models:
        # If you have a central models module, import it here so models are registered with Base
        # Example: from app import models
        try:
            # attempt to import a common models package used in this repo
            import models  # noqa: F401
        except Exception:
            # it's fine if there's no top-level models module; user can import manually
            pass

    Base.metadata.create_all(bind=engine)


# Convenience: allow running this module directly to init the DB
if __name__ == "__main__":
    print(f"Initializing database: {DATABASE_URL}")
    init_db()
