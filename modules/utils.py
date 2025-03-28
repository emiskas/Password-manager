import base64
import datetime
import os
from pathlib import Path

from Crypto.Cipher import AES
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from modules.supabase_client import supabase

# TODO: Use the same convention when returning or printing function outputs

# Constants
SALT_SIZE = 16
KEY_SIZE = 32  # AES-256
ITERATIONS = 100000


def derive_key(user_password: str, salt: bytes) -> bytes:
    """Derives a 256-bit AES encryption key from the user's login password."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=ITERATIONS,
    )
    return kdf.derive(user_password.encode())


def encrypt_password(plain_password, user_key):
    """Encrypt the password using AES-256."""
    salt = os.urandom(SALT_SIZE)
    key = derive_key(user_key, salt)

    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(plain_password.encode())

    # Store salt, nonce, tag, and ciphertext, then base64 encode it
    encrypted_data = base64.b64encode(salt + cipher.nonce + tag + ciphertext).decode()

    return encrypted_data


def decrypt_password(encrypted_password, user_key):
    """Decrypt the AES-encrypted password."""
    try:
        encrypted_data = base64.b64decode(encrypted_password)

        salt = encrypted_data[:SALT_SIZE]
        nonce = encrypted_data[SALT_SIZE : SALT_SIZE + 16]
        tag = encrypted_data[SALT_SIZE + 16 : SALT_SIZE + 32]
        ciphertext = encrypted_data[SALT_SIZE + 32 :]

        key = derive_key(user_key, salt)

        cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
        decrypted_password = cipher.decrypt_and_verify(ciphertext, tag)

        return decrypted_password.decode()

    except ValueError as e:
        return {"success": False, "message": "Decryption failed: Invalid key or data."}

    except Exception as e:
        return {
            "success": False,
            "message": f"Unexpected error during decryption: {str(e)}",
        }


def get_env_path():
    """
    Resolve the path to the .env file.

    Returns:
        Path: Path object pointing to the .env file.
    """
    return Path(__file__).parent.parent / ".env"


def get_user_id():
    """Retrieve the user ID of the currently logged-in user."""
    try:
        user_response = supabase.auth.get_user()
        user = getattr(user_response, "user", None)

        if not user or not getattr(user, "id", None):
            return {"success": False, "message": "User ID not found."}

        return user.id

    except Exception as e:
        return {"success": False, "message": f"Error retrieving user: {str(e)}"}


def add_password(service_name, username, plain_password):
    """Add a new password entry to Supabase."""
    user_id_response = get_user_id()

    if isinstance(user_id_response, dict):  # Check if it returned an error
        return user_id_response["message"]

    user_id = user_id_response  # Extract actual user ID

    # Fetch user's encryption key
    response = (
        supabase.table("user_keys")
        .select("encryption_salt")
        .eq("user_id", user_id)
        .single()
        .execute()
    )

    if not response.get("data"):
        return "Error: Encryption key not found for this user."

    user_key = response["data"].get("encryption_salt")

    # Encrypt the password
    encrypted_password = encrypt_password(plain_password, user_key)

    try:
        insert_response = (
            supabase.table("passwords")
            .insert(
                {
                    "user_id": user_id,
                    "service_name": service_name,
                    "username": username,
                    "encrypted_password": encrypted_password,
                }
            )
            .execute()
        )

        if "data" in insert_response:
            return "Password added successfully"
        else:
            return "Failed to add password"

    except Exception as e:
        return f"Database error: {str(e)}"


def retrieve_password(service_name):
    """Retrieve and decrypt a password from Supabase."""
    user_id_response = get_user_id()

    if isinstance(user_id_response, dict):  # Handle errors first
        return user_id_response["message"]

    user_id = user_id_response

    key_response = (
        supabase.table("user_keys")
        .select("encryption_salt")
        .eq("user_id", user_id)
        .single()
        .execute()
    )

    if not key_response.get("data"):
        return "Error: Encryption key not found."

    user_key = key_response["data"].get("encryption_salt")

    response = (
        supabase.table("passwords")
        .select("service_name, username, encrypted_password")
        .eq("user_id", user_id)
        .eq("service_name", service_name)
        .execute()
    )

    if not response.get("data"):
        return f"No entry found for service: {service_name}"

    entry = response["data"][0]

    decrypted_password = decrypt_password(entry["encrypted_password"], user_key)

    if "Error" in decrypted_password:
        return decrypted_password  # Directly return the decryption error

    return {
        "success": True,
        "service": entry["service_name"],
        "username": entry["username"],
        "password": decrypted_password,
    }


def list_passwords():
    """List all stored passwords from Supabase for the logged-in user."""
    user_id = get_user_id()

    if not user_id:
        return "Error: No authenticated user found."

    response = (
        supabase.table("passwords")
        .select("service_name, username")
        .eq("user_id", user_id)
        .execute()
    )

    if response.data:
        return response.data
    else:
        return []


def generate_password(length=16):
    import random
    import string

    characters = string.ascii_letters + string.digits + string.punctuation
    return "".join(random.choice(characters) for i in range(0, length))


def is_base64(s):
    """Checks if a string is valid Base64"""
    try:
        base64.b64decode(s, validate=True)
        return True
    except Exception:
        return False


def export_passwords(decrypt=None):
    """Export passwords from Supabase to a local file."""
    user_id = get_user_id()

    if not user_id:
        return "Error: No authenticated user found."

    response = (
        supabase.table("passwords")
        .select("service_name, username, encrypted_password")
        .eq("user_id", user_id)
        .execute()
    )

    if not response.data:
        return "No passwords found in Supabase."

    backup_dir = os.path.join(os.getcwd(), "backup")
    os.makedirs(backup_dir, exist_ok=True)

    today = datetime.datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(backup_dir, f"{today}.txt")

    if decrypt:

        # Fetch user's encryption key
        key_response = (
            supabase.table("user_keys")
            .select("encryption_salt")
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        user_key = key_response.data["encryption_salt"]

        try:
            with open(path, "w") as f:
                for entry in response.data:
                    decrypted_password = decrypt_password(
                        entry["encrypted_password"], user_key
                    )

                    f.write(
                        f"Service: {entry["service_name"]}, Username: {entry["username"]}, Password: {decrypted_password}\n"
                    )

            return f"Passwords exported successfully to {path}"
        except Exception as e:
            return f"Error exporting passwords: {str(e)}"

    try:
        with open(path, "w") as f:
            for entry in response.data:
                f.write(
                    f"Service: {entry["service_name"]}, Username: {entry["username"]}, Password: {entry["encrypted_password"]}\n"
                )

        return f"Passwords exported successfully to {path}"
    except Exception as e:
        return f"Error exporting passwords: {str(e)}"


def import_passwords(path):
    """Import passwords from a local file to Supabase."""
    if not os.path.exists(path):
        return "Error: File not found."

    try:
        with open(path, "r") as f:
            lines = f.readlines()
            for line in lines:
                parts = line.strip().split(", ")
                if len(parts) != 3:
                    print(f"Skipping invalid line: {line.strip()}")
                    continue

                service = parts[0].split(": ")[1]
                username = parts[1].split(": ")[1]
                password = parts[2].split(": ")[1]

                if is_base64(password):
                    user_id = get_user_id()

                    # Fetch user's encryption key
                    key_response = (
                        supabase.table("user_keys")
                        .select("encryption_salt")
                        .eq("user_id", user_id)
                        .single()
                        .execute()
                    )
                    user_key = key_response.data["encryption_salt"]
                    password = decrypt_password(password, user_key)

                # Insert into Supabase
                add_password(service, username, password)
        return f"Successfully imported accounts from: {path}"
    except Exception as e:
        return f"Error importing passwords: {str(e)}"
