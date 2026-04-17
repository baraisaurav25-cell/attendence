"""
attendance.py
-------------
Pure business logic for attendance data:
  - identifying attendance columns
  - computing per-student percentages
  - building the summary report DataFrame
  - exporting to Excel bytes
"""

import io

import pandas as pd

from config import FIXED_COLS


# ── Column helpers ────────────────────────────────────────────────────────────

def get_attendance_cols(df: pd.DataFrame) -> list[str]:
    """Return column names that represent attendance sessions (not ID/Name)."""
    return [c for c in df.columns if c not in FIXED_COLS]


# ── Per-student calculations ──────────────────────────────────────────────────

def compute_attendance_pct(df: pd.DataFrame, student_id: str) -> float:
    """
    Calculate the attendance percentage for a single student.
    Returns 0.0 if there are no sessions or the student is not found.
    """
    cols = get_attendance_cols(df)
    if not cols:
        return 0.0

    row = df.loc[df["ID"] == student_id]
    if row.empty:
        return 0.0

    total_present = row[cols].sum(axis=1).values[0]
    return round(total_present / len(cols) * 100, 1)


# ── Summary report ────────────────────────────────────────────────────────────

def build_report(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a summary DataFrame with columns:
        ID, Name, Total Classes, Total Present, Total Absent, Attendance %
    """
    cols = get_attendance_cols(df)
    report = df[FIXED_COLS].copy()

    if cols:
        report["Total Classes"] = len(cols)
        report["Total Present"] = df[cols].sum(axis=1).astype(int)
        report["Total Absent"]  = report["Total Classes"] - report["Total Present"]
        report["Attendance %"]  = (report["Total Present"] / len(cols) * 100).round(1)
    else:
        report["Total Classes"] = 0
        report["Total Present"] = 0
        report["Total Absent"]  = 0
        report["Attendance %"]  = 0.0

    return report


# ── Export ────────────────────────────────────────────────────────────────────

def to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Report") -> bytes:
    """Serialise *df* to an in-memory Excel file and return the raw bytes."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return buf.getvalue()
