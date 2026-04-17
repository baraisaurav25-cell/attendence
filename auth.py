"""
auth.py
-------
User account management: loading, saving, registration, password reset,
and deletion.  All user data lives in a single JSON file.
"""

import os

from config import DATA_DIR, USERS_FILE
from utils import hash_password, load_json, save_json
from database import list_sections, section_path


# ── User file I/O ─────────────────────────────────────────────────────────────

def load_users() -> dict:
    """
    Load the users dictionary from disk.
    If the file is missing or empty, bootstrap it with a default admin account.
    """
    users = load_json(USERS_FILE, None)
    if not users:
        users = {"admin": {"password": hash_password("admin123"), "role": "admin"}}
        save_json(USERS_FILE, users)
    return users


def save_users(users: dict) -> None:
    """Persist the users dictionary to disk."""
    save_json(USERS_FILE, users)


# ── Account operations ────────────────────────────────────────────────────────

def register_user(username: str, password: str) -> tuple[bool, str]:
    """
    Create a new teacher account.
    Returns (True, success_msg) or (False, error_msg).
    """
    username = username.strip()
    if not username or not password:
        return False, "Username and password required."

    users = load_users()
    if username in users:
        return False, "Username already exists."

    users[username] = {"password": hash_password(password), "role": "teacher"}
    save_users(users)
    return True, "Account created!"


def reset_password(username: str, new_password: str) -> tuple[bool, str]:
    """
    Change the password for an existing user.
    Returns (True, success_msg) or (False, error_msg).
    """
    if len(new_password) < 4:
        return False, "Password must be ≥ 4 characters."

    users = load_users()
    if username not in users:
        return False, "User not found."

    users[username]["password"] = hash_password(new_password)
    save_users(users)
    return True, f"Password reset for '{username}'."


def delete_user(username: str) -> tuple[bool, str]:
    """
    Delete a teacher account and all their section files.
    The 'admin' account cannot be deleted.
    Returns (True, success_msg) or (False, error_msg).
    """
    if username == "admin":
        return False, "Cannot delete admin."

    users = load_users()
    if username not in users:
        return False, "User not found."

    # Remove all Excel section files owned by this user
    for section in list_sections(username):
        path = section_path(username, section)
        try:
            os.remove(path)
        except OSError:
            pass

    del users[username]
    save_users(users)
    return True, f"User '{username}' deleted."


def authenticate(username: str, password: str) -> dict | None:
    """
    Verify credentials.
    Returns the user record dict on success, or None on failure.
    """
    users = load_users()
    user = users.get(username)
    if user and user["password"] == hash_password(password):
        return user
    return None
