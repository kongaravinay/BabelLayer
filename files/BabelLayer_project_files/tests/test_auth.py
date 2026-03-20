"""Tests for authentication."""
from auth.passwords import hash_password, verify_password


class TestPasswords:

    def test_hash_and_verify(self):
        pw = "secret123"
        hashed = hash_password(pw)
        assert verify_password(pw, hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("correct")
        assert not verify_password("wrong", hashed)

    def test_hash_is_unique(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        # bcrypt produces a different salt each time
        assert h1 != h2
