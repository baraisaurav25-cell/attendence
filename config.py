"""
config.py
---------
App-wide constants and one-time directory setup.
"""

import os

# ── Storage ──────────────────────────────────────────────────────────────────
DATA_DIR   = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")

# Columns that are always present in every section DataFrame.
FIXED_COLS = ["ID", "Name"]

# Ensure the data directory exists when this module is imported.
os.makedirs(DATA_DIR, exist_ok=True)
