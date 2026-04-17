"""
ui/login_ui.py
--------------
Login and registration page.
"""

import streamlit as st

from auth import authenticate, register_user


def login_page() -> None:
    """Render the login / registration screen."""
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.4, 1])

    with mid:
        # Branding header (pure HTML, no interactive widgets inside)
        st.markdown("""
        <div class='login-wrap'>
            <div class='login-logo'>📘</div>
            <div class='login-title'>Smart Attendance</div>
            <div class='login-sub'>Manage classes · Track attendance · Generate reports</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        tab_login, tab_reg = st.tabs(["🔓 Login", "📝 Register"])

        with tab_login:
            _render_login_form()

        with tab_reg:
            _render_register_form()


# ── Internal form renderers ───────────────────────────────────────────────────

def _render_login_form() -> None:
    """Username / password login form."""
    username = st.text_input("Username", key="l_u", placeholder="Enter username")
    password = st.text_input("Password", type="password", key="l_p", placeholder="Enter password")

    if st.button("Login", type="primary", use_container_width=True):
        user_record = authenticate(username, password)
        if user_record:
            st.session_state.user = username
            st.session_state.role = user_record["role"]
            st.rerun()
        else:
            st.error("Invalid username or password.")


def _render_register_form() -> None:
    """New-account registration form (teachers only)."""
    username = st.text_input("Username", key="r_u", placeholder="Choose a username")
    password = st.text_input("Password", type="password", key="r_p", placeholder="Min. 4 characters")
    confirm  = st.text_input("Confirm",  type="password", key="r_p2", placeholder="Repeat password")

    if st.button("Create Account", type="primary", use_container_width=True):
        if password != confirm:
            st.error("Passwords do not match.")
            return

        ok, msg = register_user(username, password)
        if ok:
            st.success(msg + " Please log in.")
            st.rerun()
        else:
            st.error(msg)
