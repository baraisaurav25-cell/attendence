from datetime import datetime
import streamlit as st
from attendance import build_report, to_excel_bytes
from database import load_section

def report_page(section: str) -> None:
    user = st.session_state.user
    df = load_section(user, section)
    st.markdown(f"""
    <div class='page-header'>
        <h1>📊 Report — {section}</h1>
        <p>Attendance summary for all students</p>
    </div>
    """, unsafe_allow_html=True)
    if df.empty:
        st.warning("No data available.")
        if st.button("← Back", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
        return
    report = build_report(df)
    def color_pct(val):
        if not isinstance(val, float): return ""
        if val >= 75: return "color:#16A34A; font-weight:700"
        if val < 60: return "color:#DC2626; font-weight:700"
        return "color:#D97706; font-weight:700"
    st.dataframe(
        report.style.map(color_pct, subset=["Attendance %"]),
        use_container_width=True, hide_index=True
    )
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Students", len(report))
    m2.metric("≥ 75% Attendance", int((report["Attendance %"] >= 75).sum()))
    m3.metric("< 60% (At Risk)", int((report["Attendance %"] < 60).sum()))
    st.markdown("---")
    col_dl, col_back = st.columns([3, 1])
    with col_dl:
        st.download_button(
            "📥 Download Excel Report",
            data=to_excel_bytes(report),
            file_name=f"{section}_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary", use_container_width=True,
        )
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
