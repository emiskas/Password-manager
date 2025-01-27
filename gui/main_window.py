import os
import sys

from components.password_table import PasswordTable
from cryptography.fernet import Fernet
from dialogs.master_password import (MasterPasswordCreationDialog,
                                     MasterPasswordDialog)
from dialogs.password import AddPasswordDialog
from dotenv import load_dotenv
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QDialog, QFileDialog, QLabel,
                             QMainWindow, QMessageBox, QPushButton,
                             QVBoxLayout, QWidget)

from modules.password_manager import (export_passwords, import_passwords,
                                      list_passwords)

# Load environment variables
load_dotenv()

# Get the encryption key
encryption_key = os.getenv("ENCRYPTION_KEY")
cipher = Fernet(encryption_key)

# Get the master password
stored_encrypted_password = os.getenv("ENCRYPTED_MASTER_PASSWORD")


class MainWindow(QMainWindow):
    """Main application window for the password manager."""

    def __init__(self):
        super().__init__()
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

        # Status label for feedback
        self.status_label = QLabel("Welcome to Password Manager")
        self.status_label.setAlignment(Qt.AlignCenter)

        # Add widgets to the layout
        layout.addWidget(self.status_label)
        layout.addWidget(self.add_password_btn)
        layout.addWidget(self.list_passwords_btn)
        layout.addWidget(self.export_passwords_btn)
        layout.addWidget(self.import_passwords_btn)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Connect buttons to their respective functions
        self.add_password_btn.clicked.connect(self.open_add_password_dialog)
        self.list_passwords_btn.clicked.connect(self.display_passwords)
        self.export_passwords_btn.clicked.connect(export_passwords)
        self.import_passwords_btn.clicked.connect(
            lambda: self.handle_import(encryption_key)
        )

    def open_add_password_dialog(self):
        """Open the dialog for adding a new password."""
        dialog = AddPasswordDialog()
        dialog.exec_()

    def display_passwords(self):
        """Display a table of stored passwords."""
        try:
            password_list = list_passwords()  # Get the list of strings

            if isinstance(password_list, str):  # Handle "No passwords stored yet."
                QMessageBox.information(self, "No Passwords", password_list)
                return

            # Create a dialog to display the password table
            dialog = QDialog(self)
            dialog.setWindowTitle("Stored Passwords")
            dialog.setGeometry(200, 200, 600, 400)

            # Add the PasswordTable to the dialog
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
            layout.setSpacing(0)  # Remove spacing between widgets
            table = PasswordTable(password_list, cipher)
            layout.addWidget(table)

            dialog.setLayout(layout)
            dialog.exec_()  # Show the dialog

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to retrieve passwords: {str(e)}"
            )

    def display_backup(self):
        """Show a dialog with backup files as buttons."""
        backup_dir = "backup"
        if not os.path.exists(backup_dir):
            QMessageBox.warning(self, "Error", "No backup directory found.")
            return None

        files, _ = QFileDialog.getOpenFileName(
            self, "Select Backup File", backup_dir, "Text Files (*.txt);;All Files (*)"
        )

        print(f"Selected file: {files}")  # Debugging: Print the selected file path
        return files

    def handle_import(self, encryption_key):
        """Handle the import process."""
        selected_file = self.display_backup()  # Get the selected file
        if not selected_file:  # If no file is selected, do nothing
            return

        result = import_passwords(selected_file, encryption_key)  # Call the import function
        QMessageBox.information(self, "Import Status", result)

    def handle_export(self):
        """Handle the export process."""
        result = export_passwords()  # Call the export function
        QMessageBox.information(self, "Export Status", result)


def is_windows_dark_mode():
    """Check if Windows is set to dark mode."""
    try:
        import winreg as reg  # Windows Registry module

        key = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        with reg.OpenKey(reg.HKEY_CURRENT_USER, key) as registry_key:
            value, _ = reg.QueryValueEx(registry_key, "AppsUseLightTheme")
            return value == 0  # 0 means dark mode, 1 means light mode
    except ImportError:
        return False  # Default to light mode if on a non-Windows system
    except Exception:
        return False  # Default to light mode in case of an error


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Check for dark mode on Windows
    dark_mode = is_windows_dark_mode()

    # Apply theme based on detection
    if dark_mode:
        app.setStyleSheet(
            """
            QMainWindow, QDialog {
                background-color: #2B2B2B;
                color: #EAEAEA;
            }
            QPushButton {
                background-color: #444444;
                color: #EAEAEA;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QLabel {
                color: #EAEAEA;
            }
            QLineEdit {
                background-color: #3B3B3B;
                color: #EAEAEA;
                border: 1px solid #555555;
                padding: 3px;
                border-radius: 3px;
            }
            QTableWidget {
                background-color: #3B3B3B;
                color: #EAEAEA;
                gridline-color: #555555;
            }
            QHeaderView::section {
                background-color: #444444;
                color: #EAEAEA;
                padding: 4px;
                border: 1px solid #555555;
            }
            """
        )
    else:
        app.setStyleSheet(
            """
            QMainWindow, QDialog {
                background-color: #f0f0f0;
                color: #000000;
            }
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #000000;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QLabel {
                color: #000000;
            }
            QLineEdit {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #cccccc;
                padding: 3px;
                border-radius: 3px;
            }
            QTableWidget {
                background-color: #ffffff;
                color: #000000;
                gridline-color: #cccccc;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                color: #000000;
                padding: 4px;
                border: 1px solid #dddddd;
            }
            """
        )

    # Your main application logic
    if not os.getenv("ENCRYPTED_MASTER_PASSWORD"):
        creation_dialog = MasterPasswordCreationDialog()
        if creation_dialog.exec_() == QDialog.Accepted:
            load_dotenv()  # Reload to fetch the saved master password
            stored_encrypted_password = os.getenv("ENCRYPTED_MASTER_PASSWORD")
        else:
            sys.exit(0)

    password_dialog = MasterPasswordDialog()
    if password_dialog.exec_() == QDialog.Accepted:
        main_window = MainWindow()
        main_window.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)
