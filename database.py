"""
database.py
-----------
All file-system operations for section data (per-teacher Excel files).
Each section is stored as:  data/<safe_user>__<url-encoded-section>.xlsx
"""

import os
import urllib.parse

import pandas as pd
import streamlit as st

from config import DATA_DIR, FIXED_COLS


# ── Internal path helpers ─────────────────────────────────────────────────────

def _safe_username(username: str) -> str:
    """Sanitise a username so it is safe to use as a filename component."""
    return username.strip().replace(" ", "_").replace("/", "-").replace("\\", "-")


def section_path(user: str, section: str) -> str:
    """Return the absolute file path for a given user+section pair."""
    safe_sec = urllib.parse.quote(section.strip(), safe="")
    return os.path.join(DATA_DIR, f"{_safe_username(user)}__{safe_sec}.xlsx")


# ── Section CRUD ──────────────────────────────────────────────────────────────

def load_section(user: str, section: str) -> pd.DataFrame:
    """
    Load a section's DataFrame from disk.
    Returns an empty DataFrame (with FIXED_COLS) if the file doesn't exist.
    Attendance columns are coerced to int (0/1).
    """
    path = section_path(user, section)
    try:
        if os.path.exists(path):
            df = pd.read_excel(path, dtype={"ID": str})

            # Guarantee fixed columns are present
            for col in FIXED_COLS:
                if col not in df.columns:
                    df[col] = ""

            # Coerce attendance columns to int
            att_cols = [c for c in df.columns if c not in FIXED_COLS]
            for col in att_cols:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

            return df
    except Exception as e:
        st.warning(f"Could not load section '{section}': {e}")

    return pd.DataFrame(columns=FIXED_COLS)


def save_section(user: str, section: str, df: pd.DataFrame) -> None:
    """
    Persist *df* to disk for the given user+section.
    Strips whitespace from IDs and removes duplicate IDs before saving.
    """
    try:
        df = df.copy()
        df["ID"] = df["ID"].astype(str).str.strip()
        df = df.drop_duplicates(subset=["ID"], keep="last")
        df.to_excel(section_path(user, section), index=False)
    except Exception as e:
        st.error(f"Could not save section: {e}")


def list_sections(user: str) -> list[str]:
    """Return all section names that belong to *user*, sorted alphabetically."""
    prefix = f"{_safe_username(user)}__"
    result = []
    try:
        for fname in sorted(os.listdir(DATA_DIR)):
            if fname.startswith(prefix) and fname.endswith(".xlsx"):
                encoded = fname[len(prefix):-5]          # strip prefix + ".xlsx"
                result.append(urllib.parse.unquote(encoded))
    except OSError:
        pass
    return result


def create_section(user: str, section: str) -> tuple[bool, str]:
    """
    Create a new empty section for *user*.
    Returns (True, success_msg) or (False, error_msg).
    """
    section = section.strip()
    if not section:
        return False, "Section name cannot be empty."
    if section in list_sections(user):
        return False, "Section already exists."
    save_section(user, section, pd.DataFrame(columns=FIXED_COLS))
    return True, f"Section '{section}' created."


def delete_section(user: str, section: str) -> None:
    """Delete the Excel file for the given user+section (no-op if missing)."""
    path = section_path(user, section)
    if os.path.exists(path):
        os.remove(path)
