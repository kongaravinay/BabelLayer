"""
Bootstrap script — creates tables and seeds the default admin user.

Usage:
    python src/database/init_db.py
"""
import sys
from pathlib import Path

# Allow running this script directly from the command line
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.connection import create_tables, db_session
from database.models import User
from auth.passwords import hash_password
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


def seed_admin():
    with db_session() as s:
        if s.query(User).filter_by(username="admin").first():
            log.info("Admin user already exists — skipping")
            return

        admin = User(
            username="admin",
            email="admin@babellayer.local",
            password_hash=hash_password("admin123"),
            full_name="System Administrator",
            is_active=True,
            role="admin",
        )
        s.add(admin)
        log.info("Created default admin  (admin / admin123)")


if __name__ == "__main__":
    log.info("Initializing BabelLayer database…")
    create_tables()
    seed_admin()
    log.info("Done ✓")
