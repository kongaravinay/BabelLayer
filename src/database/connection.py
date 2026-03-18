"""
Database connection helpers.

Uses SQLAlchemy with scoped sessions. The context manager `db_session()`
is the primary way to interact with the database throughout the app.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
import logging

from config import DATABASE_URL
from database.models import Base

log = logging.getLogger(__name__)

_engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    # SQLite needs this to work across threads (PyQt uses multiple)
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)
_SessionFactory = sessionmaker(bind=_engine, autoflush=False)
_ScopedSession = scoped_session(_SessionFactory)


def create_tables():
    """Create all tables that don't yet exist."""
    Base.metadata.create_all(bind=_engine)
    log.info("Database tables created")


@contextmanager
def db_session():
    """Yield a transactional session that auto-commits on success, rolls back on error."""
    session = _ScopedSession()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def shutdown():
    """Call on app exit to release the connection pool."""
    _ScopedSession.remove()
