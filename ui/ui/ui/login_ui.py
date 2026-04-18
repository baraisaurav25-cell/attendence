import streamlit as st
from auth import authenticate, register_user

def login_page() -> None:
    st.markdown("""
    <style>
    .block-container { padding-top: 0 !important; }
    .hero {
        background: linear-gradient(135deg, #1a56db 0%, #0e9f6e 100%);
        padding: 56px 24px 48px 24px;
        text-align: center;
        border-radius: 0 0 32px 32px;
        margin-bottom: 32px;
    }
    .hero-icon  { font-size: 3.5rem; margin-bottom: 10px; }
    .hero-title { font-size: 2rem; font-weight: 800; color: #fff; margin: 0 0 8px 0; }
    .hero-sub   { font-size: 0.95rem; color: rgba(255,255,255,0.85); margin: 0; }
    .pills { display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; margin-top: 20px; }
    .pill {
        background: rgba(255,255,255,0.15);
        color: #fff;
        border: 1px solid rgba(255,255,255,0.25);
        border-radius: 99px;
        padding: 4px 14px;
        font-size: 0.78rem; font-weight: 600;
    }
    .stats-row {
        display: flex; justify-content: center;
        max-width: 440px; margin: 0 auto 28px auto;
        background: #F9FAFB; border: 1px solid #E5E7EB;
        border-radius: 16px; overflow: hidden;
    }
    .stat-item {
        flex: 1; text-align: center; padding: 16px 8px;
        border-right: 1px solid #E5E7EB;
    }
    .stat-item:last-child { border-right: none; }
    .stat-num   { font-size: 1.5rem; font-weight: 800; color: #1a56db; display: block; }
    .stat-label { font-size: 0.72rem; color: #6B7280; font-weight: 600;
                  text-transform: uppercase; letter-spacing: 0.4px; }
    .footer { text-align: center; color: #9CA3AF; font-size: 0.78rem; padding-bottom: 24px; }
    .footer span { color: #1a56db; font-weight: 600; }
    </style>

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

    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown("<h3 style='text-align:center;margin-bottom:16px'>Welcome Back 👋</h3>",
                    unsafe_allow_html=True)
        tab_login, tab_reg = st.tabs(["🔓 Login", "📝 Register"])
        with tab_login:
            _login_form()
        with tab_reg:
            _register_form()

    st.markdown("""
    <div class='footer'>
        Built with ❤️ for <span>BGE · SAU</span> · Powered by Streamlit
    </div>
    """, unsafe_allow_html=True)

def _login_form():
    u = st.text_input("Username", key="l_u", placeholder="Enter username")
    p = st.text_input("Password", type="password", key="l_p", placeholder="Enter password")
    if st.button("🔓 Login", type="primary", use_container_width=True):
        rec = authenticate(u, p)
        if rec:
            st.session_state.user = u
            st.session_state.role = rec["role"]
            st.rerun()
        else:
            st.error("❌ Invalid username or password.")

def _register_form():
    u  = st.text_input("Username", key="r_u", placeholder="Choose a username")
    p  = st.text_input("Password", type="password", key="r_p", placeholder="Min. 4 characters")
    p2 = st.text_input("Confirm",  type="password", key="r_p2", placeholder="Repeat password")
    if st.button("📝 Create Account", type="primary", use_container_width=True):
        if p != p2:
            st.error("❌ Passwords do not match.")
            return
        ok, msg = register_user(u, p)
        if ok:
            st.success("✅ " + msg + " Please log in.")
            st.rerun()
        else:
            st.error("❌ " + msg)
