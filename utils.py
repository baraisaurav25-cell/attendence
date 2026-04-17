"""
utils.py
--------
Generic helper utilities: hashing, JSON I/O, badge HTML.
"""

import hashlib
import json
import os

import streamlit as st


# ── Password hashing ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Return SHA-256 hex-digest of *password*."""
    return hashlib.sha256(password.encode()).hexdigest()


# ── JSON file helpers ─────────────────────────────────────────────────────────

def load_json(path: str, default):
    """
    Load JSON from *path*.
    Returns *default* if the file doesn't exist or is unreadable.
    """
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default


def save_json(path: str, data) -> None:
    """Persist *data* as formatted JSON to *path*."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Save error: {e}")


# ── UI badge helper ───────────────────────────────────────────────────────────

def pct_badge(pct: float) -> str:
    """
    Return an HTML badge string coloured by attendance percentage:
        green  ≥ 75 %
        yellow  60–74 %
        red    < 60 %
    """
    if pct >= 75:
        css_class = "badge-green"
    elif pct < 60:
        css_class = "badge-red"
    else:
        css_class = "badge-warn"
    return f"<span class='badge {css_class}'>{pct}%</span>"
