"""
JWT-based session management.

In a desktop app the "session" is just in-memory state — the JWT is
issued so we have a consistent auth token if we ever expose
an API, and to enforce expiration on long-running sessions.
"""
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
import logging

from config import JWT_SECRET, JWT_ALGO, JWT_TTL_HOURS

log = logging.getLogger(__name__)


class Session:
    """Tracks the logged-in user for the lifetime of the application."""

    def __init__(self):
        self.user: Optional[Dict] = None
        self._token: Optional[str] = None

    # -- public API -----------------------------------------------------------

    def login(self, user_id: int, username: str, is_admin: bool = False) -> str:
        """Start a session and return the signed JWT token."""
        payload = {
            "uid": user_id,
            "sub": username,
            "admin": is_admin,
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_TTL_HOURS),
        }
        self._token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)
        self.user = self._user_payload(user_id=user_id, username=username, is_admin=is_admin)
        log.info("Session started for %s", username)
        return self._token

    def logout(self) -> None:
        """End the active in-memory session."""
        if self.user:
            log.info("Session ended for %s", self.user["username"])
        self.user = None
        self._token = None

    @property
    def is_active(self) -> bool:
        return self.user is not None

    def verify_token(self, token: str) -> Optional[Dict]:
        """Validate a JWT and return claims when valid."""
        try:
            return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        except jwt.ExpiredSignatureError:
            log.warning("Token expired")
        except jwt.InvalidTokenError as exc:
            log.warning("Bad token: %s", exc)
        return None

    @staticmethod
    def _user_payload(*, user_id: int, username: str, is_admin: bool) -> Dict:
        return {
            "user_id": user_id,
            "username": username,
            "is_admin": is_admin,
        }


# Singleton — importable from anywhere
current_session = Session()
