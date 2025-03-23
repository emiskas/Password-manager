from PyQt5.QtWidgets import (QDialog, QLabel, QLineEdit, QMessageBox,
                             QPushButton, QVBoxLayout)

from gui.dialogs.password_reset import PasswordResetDialog
from gui.dialogs.signup import SignUpDialog
from modules.auth import log_in


class LoginDialog(QDialog):
    """Dialog for user login using Supabase authentication."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.setGeometry(400, 200, 300, 150)

        layout = QVBoxLayout()

        self.email_label = QLabel("Email:")
        self.email_input = QLineEdit()

        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.authenticate_user)

        self.signup_button = QPushButton("Sign Up")
        self.signup_button.clicked.connect(self.open_signup_dialog)

        self.forgot_password_button = QPushButton("Forgot Password?")
        self.forgot_password_button.clicked.connect(self.open_reset_password_dialog)

        layout.addWidget(self.email_label)
        layout.addWidget(self.email_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        layout.addWidget(self.signup_button)
        layout.addWidget(self.forgot_password_button)

        self.setLayout(layout)

    def authenticate_user(self):
        """Authenticate the user with Supabase."""
        try:
            email = self.email_input.text().strip()
            password = self.password_input.text()

            # Validate inputs
            if not email or not password:
                QMessageBox.warning(
                    self, "Input Error", "Please enter email and password."
                )
                return

            # Password minimum length check
            if len(password) < 8:
                QMessageBox.warning(
                    self, "Input Error", "Password must be at least 8 characters."
                )
                return

            try:
                response = log_in(email, password)

            except TimeoutError:
                QMessageBox.critical(
                    self,
                    "Connection Error",
                    "Authentication service timed out. Please try again later.",
                )
                return

            except Exception as auth_error:
                QMessageBox.critical(
                    self, "Authentication Error", f"Login failed: {str(auth_error)}"
                )
                return

            if not isinstance(response, dict):
                QMessageBox.critical(
                    self,
                    "System Error",
                    "Invalid response from authentication service.",
                )
                return

            if response.get("success"):
                self.accept()  # Close the dialog and proceed

            else:
                error_message = response.get("message", "Unknown error occurred")
                QMessageBox.critical(self, "Login Failed", error_message)

                # Specific handling for different error types
                if "password" in error_message.lower():
                    self.password_input.clear()
                    self.password_input.setFocus()

                elif (
                    "not found" in error_message.lower()
                    or "email" in error_message.lower()
                ):
                    self.email_input.setFocus()

        except Exception as e:
            QMessageBox.critical(
                self, "System Error", f"An unexpected error occurred: {str(e)}"
            )

    def open_signup_dialog(self):
        """Open the SignUpDialog when the user clicks Sign Up."""
        try:
            signup_dialog = SignUpDialog()
            signup_dialog.exec_()

        except Exception as e:
            QMessageBox.critical(
                self, "Dialog Error", f"Failed to open signup dialog: {str(e)}"
            )

    def open_reset_password_dialog(self):
        """Open the Password Reset dialog."""
        try:
            reset_dialog = PasswordResetDialog()
            reset_dialog.exec_()
        except Exception as e:
            QMessageBox.critical(
                self, "Dialog Error", f"Failed to open password reset dialog: {str(e)}"
            )
