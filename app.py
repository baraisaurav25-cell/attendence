"""
app.py
------
Entry point for Smart Attendance.

Responsibilities:
  1. Streamlit page configuration
  2. Global CSS injection
  3. Top-level routing: login → admin panel / teacher dashboard / sub-pages
"""

import streamlit as st

# ── Page config (must be the very first Streamlit call) ───────────────────────
st.set_page_config(
    page_title="Smart Attendance",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Local imports come after set_page_config to avoid any Streamlit ordering issues
from ui.login_ui      import login_page
from ui.dashboard     import admin_panel, teacher_dashboard
from ui.attendance_ui import attendance_page
from ui.report_ui     import report_page


# ════════════════════════════════════════════════════════════════════════════════
#  GLOBAL CSS
# ════════════════════════════════════════════════════════════════════════════════

def _inject_css() -> None:
    """Inject the application-wide stylesheet."""
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Root variables ── */
:root {
    --bg:        #F9FAFB;
    --surface:   #FFFFFF;
    --border:    #E5E7EB;
    --border-2:  #D1D5DB;
    --text-1:    #111827;
    --text-2:    #374151;
    --text-3:    #6B7280;
    --primary:   #2563EB;
    --primary-h: #1D4ED8;
    --primary-bg:#EFF6FF;
    --success:   #16A34A;
    --success-bg:#F0FDF4;
    --danger:    #DC2626;
    --danger-bg: #FEF2F2;
    --warn:      #D97706;
    --warn-bg:   #FFFBEB;
    --radius:    10px;
    --shadow:    0 1px 3px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.05);
    --shadow-md: 0 4px 16px rgba(0,0,0,.08), 0 2px 4px rgba(0,0,0,.04);
}

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
    background-color: var(--bg);
    color: var(--text-1);
}
h1, h2, h3, h4 {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 700;
    color: var(--text-1);
    letter-spacing: -0.3px;
}
code, .mono { font-family: 'JetBrains Mono', monospace; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--surface);
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] * { color: var(--text-2) !important; }
[data-testid="stSidebar"] h3 {
    color: var(--text-1) !important;
    font-size: 1rem;
    font-weight: 700;
}
[data-testid="stSidebar"] .stButton > button {
    background: var(--bg);
    color: var(--text-2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    width: 100%;
    text-align: left;
    font-weight: 500;
    transition: background 0.15s;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: var(--primary-bg);
    border-color: var(--primary);
    color: var(--primary) !important;
}

/* ── Primary buttons ── */
.stButton > button[kind="primary"],
div[data-testid="stForm"] button[kind="primaryFormSubmit"] {
    background: var(--primary) !important;
    color: #fff !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: var(--radius) !important;
    padding: 0.5rem 1.25rem !important;
    box-shadow: 0 2px 8px rgba(37,99,235,0.25) !important;
    transition: background 0.15s, transform 0.1s !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--primary-h) !important;
    transform: translateY(-1px) !important;
}

/* ── Secondary buttons ── */
.stButton > button[kind="secondary"] {
    background: var(--surface) !important;
    color: var(--text-2) !important;
    border: 1px solid var(--border-2) !important;
    border-radius: var(--radius) !important;
    font-weight: 500 !important;
    transition: all 0.15s !important;
}
.stButton > button[kind="secondary"]:hover {
    background: var(--bg) !important;
    border-color: var(--primary) !important;
    color: var(--primary) !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    font-weight: 600 !important;
    color: var(--text-1) !important;
}
.streamlit-expanderContent {
    border: 1px solid var(--border) !important;
    border-top: none !important;
    border-radius: 0 0 var(--radius) var(--radius) !important;
    background: var(--surface) !important;
}

/* ── Metrics ── */
[data-testid="metric-container"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px 20px;
    box-shadow: var(--shadow);
}
[data-testid="metric-container"] label {
    color: var(--text-3) !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 1.8rem !important;
    font-weight: 800 !important;
    color: var(--text-1) !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    border: 1px solid var(--border-2) !important;
    border-radius: var(--radius) !important;
    background: var(--surface) !important;
    color: var(--text-1) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    transition: border-color 0.15s !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.12) !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface);
    border-bottom: 2px solid var(--border);
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    font-weight: 600 !important;
    color: var(--text-3) !important;
    padding: 0.6rem 1.2rem !important;
    border-radius: 0 !important;
    border-bottom: 2px solid transparent !important;
    margin-bottom: -2px;
}
.stTabs [aria-selected="true"] {
    color: var(--primary) !important;
    border-bottom-color: var(--primary) !important;
    background: transparent !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    overflow: hidden;
}

/* ── Alerts ── */
[data-testid="stAlert"] {
    border-radius: var(--radius) !important;
    border-left-width: 4px !important;
    font-weight: 500;
}

/* ── Divider ── */
hr { border-color: var(--border) !important; }

/* ── Badge helpers ── */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 99px;
    font-size: 0.78rem;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
}
.badge-green { background: var(--success-bg); color: var(--success); }
.badge-red   { background: var(--danger-bg);  color: var(--danger);  }
.badge-blue  { background: var(--primary-bg); color: var(--primary); }
.badge-warn  { background: var(--warn-bg);    color: var(--warn);    }

/* ── Card ── */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px 24px;
    margin-bottom: 14px;
    box-shadow: var(--shadow);
}

/* ── Page title area ── */
.page-header {
    padding: 8px 0 20px 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 24px;
}
.page-header h1 { font-size: 1.75rem; margin: 0; }
.page-header p  { color: var(--text-3); font-size: 0.9rem; margin: 4px 0 0 0; }

/* ── Login card ── */
.login-wrap {
    max-width: 420px;
    margin: 0 auto;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 36px 40px;
    box-shadow: var(--shadow-md);
}
.login-logo  { font-size: 2.2rem; text-align: center; margin-bottom: 4px; }
.login-title { text-align: center; font-size: 1.4rem; font-weight: 800; margin-bottom: 2px; }
.login-sub   { text-align: center; color: var(--text-3); font-size: 0.85rem; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
#  ROUTER
# ════════════════════════════════════════════════════════════════════════════════

def main() -> None:
    _inject_css()

    # Not logged in → show login screen
    if not st.session_state.get("user"):
        login_page()
        return

    role = st.session_state.get("role", "teacher")

    # Admin → admin panel (no sub-pages)
    if role == "admin":
        admin_panel()
        return

    # Teacher → route between sub-pages
    page    = st.session_state.get("page", "dashboard")
    section = st.session_state.get("section", "")

    if page == "attendance" and section:
        attendance_page(section)
    elif page == "report" and section:
        report_page(section)
    else:
        st.session_state.page = "dashboard"
        teacher_dashboard()


if __name__ == "__main__":
    main()
