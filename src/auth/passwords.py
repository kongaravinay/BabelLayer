"""
Password hashing with bcrypt.

bcrypt handles salting internally, so we just need hash + verify.
"""
import bcrypt


def hash_password(plain_text_password: str) -> str:
    """Hash a plaintext password for storage."""
    return bcrypt.hashpw(plain_text_password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain_text_password: str, stored_hash: str) -> bool:
    """Check a plaintext password against a stored bcrypt hash."""
    return bcrypt.checkpw(plain_text_password.encode(), stored_hash.encode())
