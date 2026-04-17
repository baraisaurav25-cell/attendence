"""
ui/attendance_ui.py
-------------------
Attendance entry page: teachers mark present/absent per student per session.
"""

from datetime import datetime

import streamlit as st

from attendance import compute_attendance_pct, get_attendance_cols
from database import load_section, save_section
from utils import pct_badge


def attendance_page(section: str) -> None:
    """Full attendance entry page for *section*."""
    user = st.session_state.user
    df   = load_section(user, section)

    _render_header(section)

    if df.empty:
        st.warning("No students in this section. Add students first.")
        _back_button()
        return

    col_name = _render_session_picker()

    # Ensure the column exists in the DataFrame
    if col_name not in df.columns:
        df[col_name] = 0

    _render_summary_metrics(df, col_name)
    st.markdown("---")
    st.markdown("#### Toggle Attendance")

    df = _render_attendance_toggles(df, col_name, user, section)

    st.markdown("---")
    _render_save_back_buttons(user, section, df)


# ── Section renderers ─────────────────────────────────────────────────────────

def _render_header(section: str) -> None:
    st.markdown(f"""
    <div class='page-header'>
        <h1>📋 Attendance — {section}</h1>
        <p>Mark attendance for today's session</p>
    </div>
    """, unsafe_allow_html=True)


def _render_session_picker() -> str:
    """Render date + session selectors and return the resulting column name."""
    c1, c2 = st.columns(2)
    date         = c1.date_input("Date", datetime.now())
    session_type = c2.selectbox("Session", ["AM", "PM", "Extra"])
    return f"{date}_{session_type}"


def _render_summary_metrics(df, col_name: str) -> None:
    """Show Present / Absent / Total counts."""
    n_present = int(df[col_name].sum())
    n_total   = len(df)

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Students", n_total)
    m2.metric("Present",        n_present)
    m3.metric("Absent",         n_total - n_present)


def _render_attendance_toggles(df, col_name: str, user: str, section: str):
    """
    Render a toggle button row for each student.
    Saves immediately on toggle and reruns.
    Returns (possibly unmodified) df.
    """
    for idx in df.index:
        sid     = str(df.at[idx, "ID"])
        name    = str(df.at[idx, "Name"])
        pct     = compute_attendance_pct(df, sid)
        present = int(df.at[idx, col_name]) == 1

        r1, r2, r3 = st.columns([4, 2, 1])
        r1.markdown(
            f"**{name}** &nbsp; <code style='font-size:0.8rem;color:var(--text-3)'>{sid}</code>",
            unsafe_allow_html=True,
        )
        r3.markdown(pct_badge(pct), unsafe_allow_html=True)

        btn_label = "✅ Present" if present else "❌ Absent"
        btn_type  = "secondary" if present else "primary"

        if r2.button(btn_label, key=f"tog_{sid}_{col_name}", type=btn_type):
            df.at[idx, col_name] = 0 if present else 1
            save_section(user, section, df)
            st.rerun()

    return df


def _render_save_back_buttons(user: str, section: str, df) -> None:
    col_save, col_back = st.columns([3, 1])

    with col_save:
        if st.button("💾 Save All Changes", key="save_all_att",
                     type="primary", use_container_width=True):
            save_section(user, section, df)
            st.success("✅ Attendance saved successfully!")
            st.session_state.page = "dashboard"
            st.rerun()

    with col_back:
        _back_button()


def _back_button() -> None:
    if st.button("← Back", key="back_att", use_container_width=True):
        st.session_state.page = "dashboard"
        st.rerun()
