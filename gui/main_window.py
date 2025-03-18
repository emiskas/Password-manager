import json
import sys
from io import BytesIO

import qrcode
from components.password_table import PasswordTable
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (QApplication, QDialog, QFileDialog, QLabel,
                             QMainWindow, QMessageBox, QPushButton,
                             QVBoxLayout, QWidget)

from gui.dialogs.login import LoginDialog
from gui.dialogs.password import AddPasswordDialog
from modules.auth import get_current_user, log_out
from modules.supabase_client import supabase
from modules.utils import export_passwords, import_passwords, list_passwords


class QRCodeDialog(QDialog):
    """Dialog to display QR Code dynamically."""

    def __init__(self, data):
        super().__init__()
        self.setWindowTitle("QR Code")
        self.setGeometry(300, 300, 300, 300)

        layout = QVBoxLayout()

        # Generate and display QR code
        self.qr_label = QLabel(self)
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.display_qr_code(data)

        layout.addWidget(self.qr_label)
        self.setLayout(layout)

    def display_qr_code(self, data):
        """Generate QR code and display it dynamically."""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=5,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        # Convert QR Code to an image in memory
        img = qr.make_image(fill="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        # Load the image into PyQt QLabel
        image = QImage()
        image.loadFromData(buffer.getvalue(), "PNG")
        pixmap = QPixmap.fromImage(image)

        self.qr_label.setPixmap(pixmap)


class MainWindow(QMainWindow):
    """Main application window for the password manager."""

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("Password Manager")
        self.setGeometry(100, 100, 400, 200)

        # Main layout
        central_widget = QWidget()
        layout = QVBoxLayout()

        # Buttons for adding and listing passwords
        self.add_password_btn = QPushButton("Add Password")
        self.list_passwords_btn = QPushButton("List Passwords")
        self.export_passwords_btn = QPushButton("Export Passwords")
        self.import_passwords_btn = QPushButton("Import Passwords")
        self.qr_button = QPushButton("Export via QR Code")
        self.logout_button = QPushButton("Log Out")

        # Status label for feedback
        self.status_label = QLabel("Welcome to Password Manager")
        self.status_label.setAlignment(Qt.AlignCenter)

        # Add widgets to the layout
        layout.addWidget(self.status_label)
        layout.addWidget(self.add_password_btn)
        layout.addWidget(self.list_passwords_btn)
        layout.addWidget(self.export_passwords_btn)
        layout.addWidget(self.import_passwords_btn)
        layout.addWidget(self.qr_button)
        layout.addWidget(self.logout_button)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Connect buttons to their respective functions
        self.add_password_btn.clicked.connect(self.open_add_password_dialog)
        self.list_passwords_btn.clicked.connect(self.display_passwords)
        self.export_passwords_btn.clicked.connect(self.handle_export)
        self.import_passwords_btn.clicked.connect(self.handle_import)
        self.qr_button.clicked.connect(self.show_qr_code)
        self.logout_button.clicked.connect(self.handle_logout)

    def handle_logout(self):
        """Logs out the user and returns to the login screen."""
        log_out()
        QMessageBox.information(self, "Logged Out", "You have been logged out.")
        self.close()
        main()  # Restart the app and show login dialog

    def show_qr_code(self):
        """Show QR Code dialog with stored passwords."""
        response = (
            supabase.table("passwords")
            .select("service_name, username, encrypted_password")
            .execute()
        )
        passwords = response.data if response.data else []
        qr_data = json.dumps(passwords)

        self.qr_dialog = QRCodeDialog(qr_data)
        self.qr_dialog.exec_()

    def open_add_password_dialog(self):
        """Open the dialog for adding a new password."""
        dialog = AddPasswordDialog(user_id=self.user_id)
        dialog.exec_()

    def display_passwords(self):
        """Display a table of stored passwords."""
        try:
            password_list = list_passwords()

            if not password_list:  # Empty list check
                QMessageBox.information(
                    self, "No Passwords", "No passwords stored yet."
                )
                return

            dialog = QDialog(self)
            dialog.setWindowTitle("Stored Passwords")
            dialog.setGeometry(200, 200, 600, 400)

            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            table = PasswordTable(
                password_list
            )  # Ensure PasswordTable handles dictionaries
            layout.addWidget(table)

            dialog.setLayout(layout)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to retrieve passwords: {str(e)}"
            )

    def handle_import(self):
        """Handle the import process."""
        selected_file, _ = QFileDialog.getOpenFileName(
            self, "Select Backup File", "backup", "Text Files (*.txt);;All Files (*)"
        )
        if not selected_file:
            return

        result = import_passwords(selected_file)
        QMessageBox.information(self, "Import Status", result)

    def handle_export(self):
        """Handle the export process with encryption option."""
        reply = QMessageBox.question(
            self,
            "Encrypt Export?",
            "Do you want to encrypt the exported passwords?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            result = export_passwords()
        else:
            result = export_passwords(decrypt=True)

        QMessageBox.information(self, "Export Status", result)

def main():
    """Application entry point."""
    app = QApplication(sys.argv)

    login_dialog = LoginDialog()
    if login_dialog.exec_() == QDialog.Accepted:
        user = get_current_user()
        if user:
            main_window = MainWindow(user.user.id)
            main_window.show()
            sys.exit(app.exec_())
        else:
            print("User authentication failed.")
            sys.exit(0)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
