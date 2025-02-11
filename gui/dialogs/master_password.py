import os
import sys
from pathlib import Path

from cryptography.fernet import Fernet
from dotenv import load_dotenv
from PyQt5.QtWidgets import (QDialog, QLabel, QLineEdit, QMessageBox,
                             QPushButton, QVBoxLayout)

from modules.password_manager import (generate_key, set_master_password,
                                      verify_master_password, get_env_path)

# Load environment variables using centralized .env path
load_dotenv(dotenv_path=get_env_path())

encryption_key = os.getenv("ENCRYPTION_KEY")

# Create an encryption key if not yet created
if not encryption_key:
    encryption_key = generate_key().decode()
    try:
        with open(get_env_path(), "a") as f:
            f.write(f"ENCRYPTION_KEY={encryption_key}\n")
        print("ENCRYPTION_KEY generated and saved.")

    except Exception as e:
        print(f"Failed to write ENCRYPTION_KEY to .env: {e}")

cipher = Fernet(encryption_key)


class MasterPasswordCreationDialog(QDialog):
    """Dialog to prompt the user to create a master password"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Master Password Creation")
        self.setGeometry(400, 300, 300, 150)

        layout = QVBoxLayout()

        # Label and input field for the master password
        self.label = QLabel("Choose a master password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)  # Hide text for security

        # Submit and Exit buttons
        self.submit_button = QPushButton("Submit")
        self.exit_button = QPushButton("Exit")

        # Add widgets to the layout
        layout.addWidget(self.label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.submit_button)
        layout.addWidget(self.exit_button)

        self.setLayout(layout)

        # Connect buttons to their respective functions
        self.submit_button.clicked.connect(self.create_master_password)
        self.exit_button.clicked.connect(self.reject)

    def create_master_password(self):
        """Save the master password and close the dialog."""
        master_password = self.password_input.text().strip()

        if not master_password:
            QMessageBox.warning(self, "Error", "Master password cannot be empty.")
            return

        try:
            set_master_password(master_password, encryption_key.encode())

            # Force reload .env and update global variable
            load_dotenv(override=True)

            # Explicitly fetch the updated stored_encrypted_pasword
            global stored_encrypted_password
            stored_encrypted_password = os.getenv("ENCRYPTED_MASTER_PASSWORD")

            QMessageBox.information(
                self, "Success", "Master password created successfully."
            )
            self.accept()  # Close the dialog
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to set master password: {str(e)}"
            )


class MasterPasswordDialog(QDialog):
    """Dialog to prompt the user for the master password."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Master Password")
        self.setGeometry(400, 300, 300, 150)

        layout = QVBoxLayout()

        # Label and input field for the master password
        self.label = QLabel("Enter your master password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)  # Hide text for security

        # Submit and Exit buttons
        self.submit_button = QPushButton("Submit")
        self.exit_button = QPushButton("Exit")

        # Add widgets to the layout
        layout.addWidget(self.label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.submit_button)
        layout.addWidget(self.exit_button)

        self.setLayout(layout)

        # Connect buttons to their respective functions
        self.submit_button.clicked.connect(self.validate_password)
        self.exit_button.clicked.connect(self.reject)

    def validate_password(self):
        """Validate the entered master password."""
        input_password = self.password_input.text()

        # Reload .env to get the latest master password
        load_dotenv(override=True)
        stored_encrypted_password = os.getenv("ENCRYPTED_MASTER_PASSWORD")

        if stored_encrypted_password is None:
            QMessageBox.critical(
                self, "Error", "Failed to load master password from .env"
            )
            return

        # Check if the entered master password is correct
        if verify_master_password(
            input_password,
            stored_encrypted_password.encode(),
            encryption_key.encode(),
        ):
            self.accept()  # Close the dialog and proceed to the main application
        else:
            QMessageBox.critical(self, "Error", "Incorrect master password.")
            self.password_input.clear()
