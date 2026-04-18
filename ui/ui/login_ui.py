"""
ui/login_ui.py
--------------
Login and registration page — styled landing UI.
"""

import streamlit as st
from auth import authenticate, register_user


def login_page() -> None:
    """Render the login / registration screen."""

    # ── Hero banner ──────────────────────────────────────────────────────────
    st.markdown("""
    <style>
    /* Hide default streamlit header padding */
    .block-container { padding-top: 0 !important; }

    /* ── Hero section ── */
    .hero {
        background: linear-gradient(135deg, #1a56db 0%, #0e9f6e 100%);
        padding: 56px 24px 48px 24px;
        text-align: center;
        border-radius: 0 0 32px 32px;
        margin-bottom: 32px;
        position: relative;
        overflow: hidden;
    }
    .hero::before {
        content: '';
        position: absolute;
        top: -60px; right: -60px;
        width: 220px; height: 220px;
        background: rgba(255,255,255,0.07);
        border-radius: 50%;
    }
    .hero::after {
        content: '';
        position: absolute;
        bottom: -80px; left: -40px;
        width: 280px; height: 280px;
        background: rgba(255,255,255,0.05);
        border-radius: 50%;
    }
    .hero-icon {
        font-size: 3.5rem;
        margin-bottom: 10px;
        filter: drop-shadow(0 4px 12px rgba(0,0,0,0.2));
    }
    .hero-title {
        font-size: 2rem;
        font-weight: 800;
        color: #ffffff;
        margin: 0 0 8px 0;
        letter-spacing: -0.5px;
        text-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    .hero-sub {
        font-size: 0.95rem;
        color: rgba(255,255,255,0.85);
        margin: 0;
        font-weight: 400;
    }

    /* ── Feature pills ── */
    .pills {
        display: flex;
        justify-content: center;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 20px;
    }
    .pill {
        background: rgba(255,255,255,0.15);
        color: #fff;
        border: 1px solid rgba(255,255,255,0.25);
        border-radius: 99px;
        padding: 4px 14px;
        font-size: 0.78rem;
        font-weight: 600;
        backdrop-filter: blur(4px);
    }

    /* ── Login card ── */
    .card-wrap {
        max-width: 440px;
        margin: 0 auto 40px auto;
        background: #ffffff;
        border: 1px solid #E5E7EB;
        border-radius: 20px;
        padding: 32px 36px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.08), 0 2px 8px rgba(0,0,0,0.04);
    }
    .card-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 20px;
        text-align: center;
    }

    /* ── Stats row ── */
    .stats-row {
        display: flex;
        justify-content: center;
        gap: 0;
        max-width: 440px;
        margin: 0 auto 28px auto;
        background: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        overflow: hidden;
    }
    .stat-item {
        flex: 1;
        text-align: center;
        padding: 16px 8px;
        border-right: 1px solid #E5E7EB;
    }
    .stat-item:last-child { border-right: none; }
    .stat-num {
        font-size: 1.5rem;
        font-weight: 800;
        color: #1a56db;
        display: block;
    }
    .stat-label {
        font-size: 0.72rem;
        color: #6B7280;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }

    /* ── Footer ── */
    .footer {
        text-align: center;
        color: #9CA3AF;
        font-size: 0.78rem;
        margin-top: 8px;
        padding-bottom: 24px;
    }
    .footer span { color: #1a56db; font-weight: 600; }
    </style>

    <!-- Hero -->
    <div class='hero'>
        <div class='hero-icon'>📘</div>
        <h1 class='hero-title'>BioTrack Attendance</h1>
        <p class='hero-sub'>Sylhet Agricultural University · Dept. of Biotechnology & GE</p>
        <div class='pills'>
            <span class='pill'>✅ Real-time Tracking</span>
            <span class='pill'>📊 Excel Reports</span>
            <span class='pill'>👥 Multi-Teacher</span>
        </div>
    </div>

    <!-- Stats -->
    <div class='stats-row'>
        <div class='stat-item'>
            <span class='stat-num'>AM/PM</span>
            <span class='stat-label'>Sessions</span>
        </div>
        <div class='stat-item'>
            <span class='stat-num'>100%</span>
            <span class='stat-label'>Accurate</span>
        </div>
        <div class='stat-item'>
            <span class='stat-num'>Free</span>
            <span class='stat-label'>Forever</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Login / Register card ─────────────────────────────────────────────────
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown("<div class='card-title'>Welcome Back 👋</div>",
                    unsafe_allow_html=True)

        tab_login, tab_reg = st.tabs(["🔓 Login", "📝 Register"])

        with tab_login:
            _render_login_form()

        with tab_reg:
            _render_register_form()

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class='footer'>
        Built with ❤️ for <span>BGE · SAU</span> &nbsp;·&nbsp; Powered by Streamlit
    </div>
    """, unsafe_allow_html=True)


# ── Internal form renderers ───────────────────────────────────────────────────

def _render_login_form() -> None:
    username = st.text_input("Username", key="l_u", placeholder="Enter username")
    password = st.text_input("Password", type="password", key="l_p",
                             placeholder="Enter password")

    if st.button("🔓 Login", type="primary", use_container_width=True):
        user_record = authenticate(username, password)
        if user_record:
            st.session_state.user = username
            st.session_state.role = user_record["role"]
            st.rerun()
        else:
            st.error("❌ Invalid username or password.")


def _render_register_form() -> None:
    username = st.text_input("Username", key="r_u", placeholder="Choose a username")
    password = st.text_input("Password", type="password", key="r_p",
                             placeholder="Min. 4 characters")
    confirm  = st.text_input("Confirm",  type="password", key="r_p2",
                             placeholder="Repeat password")

    if st.button("📝 Create Account", type="primary", use_container_width=True):
        if password != confirm:
            st.error("❌ Passwords do not match.")
            return
        ok, msg = register_user(username, password)
        if ok:
            st.success("✅ " + msg + " Please log in.")
            st.rerun()
        else:
            st.error("❌ " + msg)
