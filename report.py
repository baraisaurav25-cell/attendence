"""
report.py
---------
Report generation helpers.
The core logic lives in attendance.py; this module re-exports what the
UI layers need so imports stay clean and the file is ready to grow.
"""

from attendance import build_report, to_excel_bytes

__all__ = ["build_report", "to_excel_bytes"]
