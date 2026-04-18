import streamlit as st
from auth import authenticate, register_user

def login_page():
    st.markdown("""<style>
    .block-container{padding-top:0!important}
    .hero{background:linear-gradient(135deg,#1a56db,#0e9f6e);padding:60px 24px 50px;text-align:center;border-radius:0 0 32px 32px;margin-bottom:28px}
    .hero h1{color:#fff;font-size:2rem;font-weight:800;margin:8px 0 4px}
    .hero p{color:rgba(255,255,255,.85);font-size:.9rem;margin:0}
    .pills{display:flex;justify-content:center;gap:8px;flex-wrap:wrap;margin-top:16px}
    .pill{background:rgba(255,255,255,.15);color:#fff;border:1px solid rgba(255,255,255,.3);border-radius:99px;padding:3px 12px;font-size:.75rem;font-weight:600}
    .srow{display:flex;max-width:420px;margin:0 auto 24px;background:#F9FAFB;border:1px solid #E5E7EB;border-radius:14px;overflow:hidden}
    .si{flex:1;text-align:center;padding:14px 6px;border-right:1px solid #E5E7EB}
    .si:last-child{border-right:none}
    .sn{font-size:1.3rem;font-weight:800;color:#1a56db;display:block}
    .sl{font-size:.68rem;color:#6B7280;font-weight:600;text-transform:uppercase;letter-spacing:.4px}
    .foot{text-align:center;color:#9CA3AF;font-size:.75rem;padding:12px 0 20px}
    .foot b{color:#1a56db}
    </style>
    <div class='hero'>
    <span style='font-size:3rem'>📘</span>
    <h1>BioTrack Attendance</h1>
    <p>Sylhet Agricultural University · Dept. of Biotechnology & GE</p>
    <div class='pills'>
    <span class='pill'>✅ Real-time</span>
    <span class='pill'>📊 Excel Reports</span>
    <span class='pill'>👥 Multi-Teacher</span>
    </div></div>
    <div class='srow'>
    <div class='si'><span class='sn'>AM/PM</span><span class='sl'>Sessions</span></div>
    <div class='si'><span class='sn'>100%</span><span class='sl'>Accurate</span></div>
    <div class='si'><span class='sn'>Free</span><span class='sl'>Forever</span></div>
    </div>""", unsafe_allow_html=True)

    _, mid, _ = st.columns([1,2,1])
    with mid:
        st.markdown("<h3 style='text-align:center;margin-bottom:12px'>Welcome Back 👋</h3>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔓 Login", "📝 Register"])
        with t1:
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
        with t2:
            u = st.text_input("Username", key="r_u", placeholder="Choose username")
            p = st.text_input("Password", type="password", key="r_p", placeholder="Min. 4 chars")
            p2= st.text_input("Confirm",  type="password", key="r_p2", placeholder="Repeat password")
            if st.button("📝 Create Account", type="primary", use_container_width=True):
                if p != p2: st.error("❌ Passwords do not match.")
                else:
                    ok, msg = register_user(u, p)
                    st.success("✅ "+msg+" Please log in.") if ok else st.error("❌ "+msg)

    st.markdown("<div class='foot'>Built with ❤️ for <b>BGE · SAU</b> · Powered by Streamlit</div>", unsafe_allow_html=True)
