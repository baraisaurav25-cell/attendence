import streamlit as st
from auth import authenticate, register_user

def login_page():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.block-container { padding-top: 0 !important; }

/* ── Page background ── */
section[data-testid="stMain"] {
    background: #F0F4FF;
}

/* ── Top bar ── */
.topbar {
    background: #1E40AF;
    padding: 14px 32px;
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 40px;
}
.topbar-icon { font-size: 1.6rem; }
.topbar-title {
    color: #fff;
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: -0.2px;
}
.topbar-sub {
    color: rgba(255,255,255,0.7);
    font-size: 0.78rem;
    margin-left: auto;
}

/* ── Card ── */
.login-card {
    background: #fff;
    border-radius: 16px;
    padding: 36px 40px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    max-width: 420px;
    margin: 0 auto;
}
.login-card-title {
    font-size: 1.3rem;
    font-weight: 700;
    color: #111827;
    margin-bottom: 4px;
}
.login-card-sub {
    font-size: 0.85rem;
    color: #6B7280;
    margin-bottom: 24px;
}

/* ── Info strips ── */
.info-strip {
    display: flex;
    gap: 10px;
    max-width: 420px;
    margin: 24px auto 0;
}
.info-item {
    flex: 1;
    background: #fff;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 14px 10px;
    text-align: center;
}
.info-icon { font-size: 1.3rem; display: block; margin-bottom: 4px; }
.info-label { font-size: 0.72rem; color: #6B7280; font-weight: 600; }

/* ── Footer ── */
.footer {
    text-align: center;
    color: #9CA3AF;
    font-size: 0.75rem;
    margin-top: 24px;
    padding-bottom: 24px;
}
.footer b { color: #1E40AF; }
</style>

<!-- Top bar -->
<div class='topbar'>
    <span class='topbar-icon'>📘</span>
    <span class='topbar-title'>BioTrack Attendance</span>
    <span class='topbar-sub'>Sylhet Agricultural University</span>
</div>
""", unsafe_allow_html=True)

    # ── Login Card ────────────────────────────────────────────────────────────
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown("""
<div class='login-card'>
    <div class='login-card-title'>Welcome back 👋</div>
    <div class='login-card-sub'>Sign in to manage your classes</div>
</div>
""", unsafe_allow_html=True)

        t1, t2 = st.tabs(["🔓 Sign In", "📝 Register"])

        with t1:
            u = st.text_input("Username", key="l_u", placeholder="Enter username")
            p = st.text_input("Password", type="password", key="l_p",
                              placeholder="Enter password")
            if st.button("Sign In →", type="primary", use_container_width=True):
                rec = authenticate(u, p)
                if rec:
                    st.session_state.user = u
                    st.session_state.role = rec["role"]
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password.")

        with t2:
            u  = st.text_input("Username", key="r_u", placeholder="Choose a username")
            p  = st.text_input("Password", type="password", key="r_p",
                               placeholder="Min. 4 characters")
            p2 = st.text_input("Confirm Password", type="password", key="r_p2",
                               placeholder="Repeat password")
            if st.button("Create Account →", type="primary", use_container_width=True):
                if p != p2:
                    st.error("❌ Passwords do not match.")
                else:
                    ok, msg = register_user(u, p)
                    if ok:
                        st.success("✅ " + msg + " Please sign in.")
                    else:
                        st.error("❌ " + msg)

        # Info strips
        st.markdown("""
<div class='info-strip'>
    <div class='info-item'>
        <span class='info-icon'>📋</span>
        <span class='info-label'>AM / PM Sessions</span>
    </div>
    <div class='info-item'>
        <span class='info-icon'>📊</span>
        <span class='info-label'>Excel Reports</span>
    </div>
    <div class='info-item'>
        <span class='info-icon'>👥</span>
        <span class='info-label'>Multi Teacher</span>
    </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div class='footer'>
    Built for <b>BGE · SAU</b> · Powered by Streamlit
</div>
""", unsafe_allow_html=True)
