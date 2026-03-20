"""
Bootstrap script — creates tables and seeds the default admin user.

Usage:
    python src/database/init_db.py
"""
import sys
from pathlib import Path
import logging
import os

# Allow running this script directly from the command line
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.connection import create_tables, db_session
from database.models import User
from auth.passwords import hash_password

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_EMAIL = "admin@babellayer.local"
DEFAULT_ADMIN_PASSWORD = os.getenv("BABEL_ADMIN_BOOTSTRAP_PASSWORD", "admin123")


def ensure_default_admin() -> None:
    """Create the default admin account if it does not already exist."""
    if DEFAULT_ADMIN_PASSWORD == "admin123":
        log.warning(
            "Using default bootstrap admin password. "
            "Set BABEL_ADMIN_BOOTSTRAP_PASSWORD before running init_db in shared environments."
        )

    with db_session() as s:
        if s.query(User).filter_by(username=DEFAULT_ADMIN_USERNAME).first():
            log.info("Admin user already exists — skipping")
            return

        admin = User(
            username=DEFAULT_ADMIN_USERNAME,
            email=DEFAULT_ADMIN_EMAIL,
            password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
            full_name="System Administrator",
            is_active=True,
            role="admin",
        )
        s.add(admin)
        log.info("Created default admin  (%s / %s)", DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD)


def initialize_database() -> None:
    """Create database tables and seed required starter data."""
    log.info("Initializing BabelLayer database...")
    create_tables()
    ensure_default_admin()
    log.info("Done")


if __name__ == "__main__":
    initialize_database()
