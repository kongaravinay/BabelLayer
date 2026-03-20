"""
Password hashing with bcrypt.

bcrypt handles salting internally, so we just need hash + verify.
"""
import bcrypt


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())
