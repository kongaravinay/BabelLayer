"""
Login dialog — shown before the main window opens.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import logging

from database import db_session
from database.models import User
from auth import verify_password, current_session
from datetime import datetime, timezone

log = logging.getLogger(__name__)


class LoginDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_info = None   # populated on successful login
        self._build()

    def _build(self):
        self.setWindowTitle("BabelLayer — Sign In")
        self.setFixedSize(380, 280)

        layout = QVBoxLayout()
        layout.setSpacing(12)

        # Branding
        brand = QLabel("BabelLayer")
        brand.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(brand)

        sub = QLabel("Data Translation & Integration")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color: #64748b;")
        layout.addWidget(sub)
        layout.addSpacing(12)

        # Fields
        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.username.returnPressed.connect(self._on_login)
        layout.addWidget(self.username)

        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setPlaceholderText("Password")
        self.password.returnPressed.connect(self._on_login)
        layout.addWidget(self.password)

        layout.addSpacing(6)

        # Buttons
        btns = QHBoxLayout()
        login_btn = QPushButton("Sign In")
        login_btn.setDefault(True)
        login_btn.clicked.connect(self._on_login)
        btns.addWidget(login_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background: #94a3b8;")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

        hint = QLabel("Default: admin / admin123")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(hint)

        self.setLayout(layout)

    def _on_login(self):
        name = self.username.text().strip()
        pw = self.password.text()

        if not name or not pw:
            QMessageBox.warning(self, "Missing Input", "Enter both username and password.")
            return

        try:
            with db_session() as s:
                user = s.query(User).filter_by(username=name).first()

                if not user or not verify_password(pw, user.password_hash):
                    QMessageBox.warning(self, "Login Failed", "Invalid credentials.")
                    return

                if not user.is_active:
                    QMessageBox.warning(self, "Disabled", "Account is disabled.")
                    return

                user.last_login = datetime.now(timezone.utc)

                current_session.login(user.id, user.username, user.is_admin)

                self.user_info = {
                    "id": user.id,
                    "username": user.username,
                    "full_name": user.full_name,
                    "email": user.email,
                    "is_admin": user.is_admin,
                }
                log.info("Login: %s", name)
                self.accept()

        except Exception as exc:
            log.error("Login error: %s", exc)
            QMessageBox.critical(self, "Error", f"Login failed:\n{exc}")
