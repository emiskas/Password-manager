from PyQt5.QtWidgets import (QDialog, QLabel, QLineEdit, QMessageBox,
                             QPushButton, QVBoxLayout)

from modules.auth import request_password_reset, verify_otp_and_reset_password


class PasswordResetDialog(QDialog):
    """Dialog for password reset using Supabase OTP verification."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reset Password")
        self.setGeometry(400, 200, 300, 200)

        layout = QVBoxLayout()

        # Email input
        self.email_label = QLabel("Enter your email:")
        self.email_input = QLineEdit()

        self.send_otp_button = QPushButton("Send OTP")
        self.send_otp_button.clicked.connect(self.send_reset_email)

        # OTP input
        self.otp_label = QLabel("Enter OTP:")
        self.otp_input = QLineEdit()

        # New password input
        self.new_password_label = QLabel("Enter new password:")
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.Password)

        # Reset button
        self.reset_button = QPushButton("Reset Password")
        self.reset_button.clicked.connect(self.reset_password)

        # Add widgets to layout
        layout.addWidget(self.email_label)
        layout.addWidget(self.email_input)
        layout.addWidget(self.send_otp_button)
        layout.addWidget(self.otp_label)
        layout.addWidget(self.otp_input)
        layout.addWidget(self.new_password_label)
        layout.addWidget(self.new_password_input)
        layout.addWidget(self.reset_button)

        self.setLayout(layout)

    def send_reset_email(self):
        """Request an OTP from Supabase."""
        email = self.email_input.text()

        if not email:
            QMessageBox.warning(self, "Input Error", "Please enter your email.")
            return

        response = request_password_reset(email)
        QMessageBox.information(self, "Password Reset", response["message"])

    def reset_password(self):
        """Verify OTP and reset the password."""
        email = self.email_input.text()
        otp = self.otp_input.text()
        new_password = self.new_password_input.text()

        if not email or not otp or not new_password:
            QMessageBox.warning(self, "Input Error", "All fields are required.")
            return

        response = verify_otp_and_reset_password(email, otp, new_password)

        if response["success"]:
            QMessageBox.information(self, "Success", response["message"])
            self.close()  # Close the dialog after success
        else:
            QMessageBox.critical(self, "Error", response["message"])
