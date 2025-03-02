from PyQt5.QtWidgets import (QDialog, QLabel, QLineEdit, QMessageBox,
                             QPushButton, QVBoxLayout)

from modules.auth import log_in
from gui.dialogs.signup import SignUpDialog


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

        layout.addWidget(self.email_label)
        layout.addWidget(self.email_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        layout.addWidget(self.signup_button)

        self.setLayout(layout)

    def authenticate_user(self):
        """Authenticate the user with Supabase."""
        email = self.email_input.text()
        password = self.password_input.text()

        if not email or not password:
            QMessageBox.warning(self, "Input Error", "Please enter email and password.")
            return

        response = log_in(email, password)

        if response["success"]:
            self.accept()  # Close the dialog and proceed
        else:
            QMessageBox.critical(self, "Login Failed", response["message"])

    def open_signup_dialog(self):
        """Open the SignUpDialog when the user clicks Sign Up."""
        signup_dialog = SignUpDialog()
        if signup_dialog.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "Success", "Account created! Please log in.")
