import streamlit as st
import pandas as pd
import os
import json
import hashlib
import io
from datetime import datetime

# ════════════════════════════════════════════
#  CONFIG
# ════════════════════════════════════════════
DATA_DIR   = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
FIXED_COLS = ["ID", "Name"]
os.makedirs(DATA_DIR, exist_ok=True)

# ════════════════════════════════════════════
#  PAGE CONFIG & CSS
# ════════════════════════════════════════════
st.set_page_config(
    page_title="Smart Attendance",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
code, .mono {
    font-family: 'JetBrains Mono', monospace;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--surface);
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] * {
    color: var(--text-2) !important;
}
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
.page-header h1 {
    font-size: 1.75rem;
    margin: 0;
}
.page-header p {
    color: var(--text-3);
    font-size: 0.9rem;
    margin: 4px 0 0 0;
}

/* ── Login card centering ── */
.login-wrap {
    max-width: 420px;
    margin: 0 auto;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 36px 40px;
    box-shadow: var(--shadow-md);
}
.login-logo {
    font-size: 2.2rem;
    text-align: center;
    margin-bottom: 4px;
}
.login-title {
    text-align: center;
    font-size: 1.4rem;
    font-weight: 800;
    margin-bottom: 2px;
}
.login-sub {
    text-align: center;
    color: var(--text-3);
    font-size: 0.85rem;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════
#  UTILITIES
# ════════════════════════════════════════════
def hp(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()


def _load_json(path: str, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default


def _save_json(path: str, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Save error: {e}")


# ════════════════════════════════════════════
#  USER MANAGEMENT
# ════════════════════════════════════════════
def load_users() -> dict:
    users = _load_json(USERS_FILE, None)
    if not users:
        users = {"admin": {"password": hp("admin123"), "role": "admin"}}
        _save_json(USERS_FILE, users)
    return users


def save_users(users: dict):
    _save_json(USERS_FILE, users)


def register_user(username: str, password: str) -> tuple[bool, str]:
    username = username.strip()
    if not username or not password:
        return False, "Username and password required."
    users = load_users()
    if username in users:
        return False, "Username already exists."
    users[username] = {"password": hp(password), "role": "teacher"}
    save_users(users)
    return True, "Account created!"


def reset_password(username: str, new_pwd: str) -> tuple[bool, str]:
    if len(new_pwd) < 4:
        return False, "Password must be ≥ 4 characters."
    users = load_users()
    if username not in users:
        return False, "User not found."
    users[username]["password"] = hp(new_pwd)
    save_users(users)
    return True, f"Password reset for {username}."


def delete_user(username: str) -> tuple[bool, str]:
    if username == "admin":
        return False, "Cannot delete admin."
    users = load_users()
    if username not in users:
        return False, "User not found."
    prefix = f"{username}__"
    for fname in os.listdir(DATA_DIR):
        if fname.startswith(prefix) and fname.endswith(".xlsx"):
            try:
                os.remove(os.path.join(DATA_DIR, fname))
            except OSError:
                pass
    del users[username]
    save_users(users)
    return True, f"User '{username}' deleted."


# ════════════════════════════════════════════
#  SECTION FILE HELPERS
# ════════════════════════════════════════════
import urllib.parse

def _safe_user(s: str) -> str:
    return s.strip().replace(" ", "_").replace("/", "-").replace("\\", "-")


def section_path(user: str, section: str) -> str:
    safe_sec = urllib.parse.quote(section.strip(), safe="")
    return os.path.join(DATA_DIR, f"{_safe_user(user)}__{safe_sec}.xlsx")


def load_section(user: str, section: str) -> pd.DataFrame:
    path = section_path(user, section)
    try:
        if os.path.exists(path):
            df = pd.read_excel(path, dtype={"ID": str})
            for col in FIXED_COLS:
                if col not in df.columns:
                    df[col] = ""
            att_cols_list = [c for c in df.columns if c not in FIXED_COLS]
            for c in att_cols_list:
                df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
            return df
    except Exception as e:
        st.warning(f"Could not load section '{section}': {e}")
    return pd.DataFrame(columns=FIXED_COLS)


def save_section(user: str, section: str, df: pd.DataFrame):
    try:
        df = df.copy()
        df["ID"] = df["ID"].astype(str).str.strip()
        df = df.drop_duplicates(subset=["ID"], keep="last")
        df.to_excel(section_path(user, section), index=False)
    except Exception as e:
        st.error(f"Could not save section: {e}")


def list_sections(user: str) -> list[str]:
    prefix = f"{_safe_user(user)}__"
    result = []
    try:
        for fname in sorted(os.listdir(DATA_DIR)):
            if fname.startswith(prefix) and fname.endswith(".xlsx"):
                encoded = fname[len(prefix):-5]
                result.append(urllib.parse.unquote(encoded))
    except OSError:
        pass
    return result


def create_section(user: str, section: str) -> tuple[bool, str]:
    section = section.strip()
    if not section:
        return False, "Section name cannot be empty."
    if section in list_sections(user):
        return False, "Section already exists."
    save_section(user, section, pd.DataFrame(columns=FIXED_COLS))
    return True, f"Section '{section}' created."


def delete_section(user: str, section: str):
    path = section_path(user, section)
    if os.path.exists(path):
        os.remove(path)


# ════════════════════════════════════════════
#  ATTENDANCE HELPERS
# ════════════════════════════════════════════
def att_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in FIXED_COLS]


def compute_pct(df: pd.DataFrame, sid: str) -> float:
    cols = att_cols(df)
    if not cols:
        return 0.0
    row = df.loc[df["ID"] == sid]
    if row.empty:
        return 0.0
    return round(row[cols].sum(axis=1).values[0] / len(cols) * 100, 1)


def build_report(df: pd.DataFrame) -> pd.DataFrame:
    cols = att_cols(df)
    out = df[FIXED_COLS].copy()
    if cols:
        out["Total Classes"] = len(cols)
        out["Total Present"] = df[cols].sum(axis=1).astype(int)
        out["Total Absent"]  = out["Total Classes"] - out["Total Present"]
        out["Attendance %"]  = (out["Total Present"] / len(cols) * 100).round(1)
    else:
        out["Total Classes"] = 0
        out["Total Present"] = 0
        out["Total Absent"]  = 0
        out["Attendance %"]  = 0.0
    return out


def excel_bytes(df: pd.DataFrame, sheet: str = "Report") -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name=sheet)
    return buf.getvalue()


def pct_badge(pct: float) -> str:
    if pct >= 75:
        cls = "badge-green"
    elif pct < 60:
        cls = "badge-red"
    else:
        cls = "badge-warn"
    return f"<span class='badge {cls}'>{pct}%</span>"


# ════════════════════════════════════════════
#  SHARED: STUDENT MANAGER WIDGET
# ════════════════════════════════════════════
def student_manager(user: str, section: str, editable: bool = True):
    df = load_section(user, section)
    kp = f"{user}__{section}"

    if editable:
        mode = st.radio(
            "Add Method", ["Manual Entry", "Bulk Paste (CSV)"],
            horizontal=True, key=f"mode_{kp}"
        )

        if mode == "Manual Entry":
            c1, c2, c3 = st.columns([2, 3, 1])
            sid  = c1.text_input("Student ID",   key=f"sid_{kp}", placeholder="e.g. 2206001")
            name = c2.text_input("Student Name", key=f"sname_{kp}", placeholder="e.g. Rahim Uddin")
            c3.markdown("<br>", unsafe_allow_html=True)
            if c3.button("➕ Add", key=f"add_{kp}", type="primary"):
                sid, name = sid.strip(), name.strip()
                if not sid or not name:
                    st.error("Both ID and Name are required.")
                elif sid in df["ID"].astype(str).values:
                    st.error(f"ID '{sid}' already exists.")
                else:
                    df = pd.concat(
                        [df, pd.DataFrame([{"ID": sid, "Name": name}])],
                        ignore_index=True
                    )
                    save_section(user, section, df)
                    st.success(f"✅ Added: {name}")
                    st.rerun()
        else:
            bulk = st.text_area(
                "Paste  ID,Name  (one per line)",
                placeholder="2206001,Rahim Uddin\n2206002,Fatima Islam",
                key=f"bulk_{kp}", height=130
            )
            if st.button("➕ Add All", key=f"bulk_btn_{kp}", type="primary"):
                added, skipped = [], []
                existing_ids = set(df["ID"].astype(str).values)
                for line in bulk.strip().splitlines():
                    parts = line.split(",", 1)
                    if len(parts) == 2:
                        s, n = parts[0].strip(), parts[1].strip()
                        if s and n and s not in existing_ids:
                            added.append({"ID": s, "Name": n})
                            existing_ids.add(s)
                        else:
                            skipped.append(s)
                if added:
                    df = pd.concat([df, pd.DataFrame(added)], ignore_index=True)
                    save_section(user, section, df)
                    st.success(f"✅ Added {len(added)} student(s).")
                    if skipped:
                        st.warning(f"Skipped (duplicate/empty): {', '.join(skipped)}")
                    st.rerun()
                else:
                    st.error("No valid rows found.")

    # Student list
    if df.empty:
        st.info("No students yet. Add students above.")
        return

    st.markdown(f"<p style='color:var(--text-3);font-size:0.85rem;font-weight:600;'>{len(df)} STUDENT(S)</p>", unsafe_allow_html=True)
    edited = st.data_editor(
        df[FIXED_COLS].reset_index(drop=True),
        use_container_width=True,
        key=f"editor_{kp}",
        disabled=not editable,
        hide_index=True,
    )

    if editable:
        col_save, col_del = st.columns([3, 2])
        with col_save:
            if st.button("💾 Save Changes", key=f"save_stu_{kp}", type="primary", use_container_width=True):
                att = [c for c in df.columns if c not in FIXED_COLS]
                merged = edited.copy()
                if att:
                    for col in att:
                        merged[col] = df[col].values
                save_section(user, section, merged)
                st.success("✅ Student list saved.")
                st.rerun()

        with col_del:
            with st.expander("🗑️ Remove a Student"):
                del_id = st.text_input("Student ID to remove", key=f"del_stu_{kp}", placeholder="Enter ID")
                if st.button("Remove", key=f"del_stu_btn_{kp}"):
                    del_id = del_id.strip()
                    if del_id in df["ID"].astype(str).values:
                        df = df[df["ID"].astype(str) != del_id].reset_index(drop=True)
                        save_section(user, section, df)
                        st.success(f"Removed ID: {del_id}")
                        st.rerun()
                    else:
                        st.error("ID not found.")


# ════════════════════════════════════════════
#  PAGE: ATTENDANCE ENTRY
# ════════════════════════════════════════════
def attendance_page(section: str):
    user = st.session_state.user
    df   = load_section(user, section)

    st.markdown(f"""
    <div class='page-header'>
        <h1>📋 Attendance — {section}</h1>
        <p>Mark attendance for today's session</p>
    </div>
    """, unsafe_allow_html=True)

    if df.empty:
        st.warning("No students in this section. Add students first.")
        if st.button("← Back to Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()
        return

    c1, c2 = st.columns(2)
    date         = c1.date_input("Date", datetime.now())
    session_type = c2.selectbox("Session", ["AM", "PM", "Extra"])
    col_name     = f"{date}_{session_type}"

    if col_name not in df.columns:
        df[col_name] = 0

    n_present = int(df[col_name].sum())
    n_total   = len(df)

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Students", n_total)
    m2.metric("Present",  n_present)
    m3.metric("Absent",   n_total - n_present)

    st.markdown("---")
    st.markdown("#### Toggle Attendance")

    for idx in df.index:
        sid     = str(df.at[idx, "ID"])
        name    = str(df.at[idx, "Name"])
        pct     = compute_pct(df, sid)
        present = int(df.at[idx, col_name]) == 1

        r1, r2, r3 = st.columns([4, 2, 1])
        r1.markdown(f"**{name}** &nbsp; <code style='font-size:0.8rem;color:var(--text-3)'>{sid}</code>", unsafe_allow_html=True)
        r3.markdown(pct_badge(pct), unsafe_allow_html=True)

        btn_label = "✅ Present" if present else "❌ Absent"
        btn_type  = "secondary" if present else "primary"
        if r2.button(btn_label, key=f"tog_{sid}_{col_name}", type=btn_type):
            df.at[idx, col_name] = 0 if present else 1
            save_section(user, section, df)
            st.rerun()

    st.markdown("---")
    col_save, col_back = st.columns([3, 1])
    with col_save:
        if st.button("💾 Save All Changes", key="save_all_att", type="primary", use_container_width=True):
            save_section(user, section, df)
            st.success("✅ Attendance saved successfully!")
            st.session_state.page = "dashboard"
            st.rerun()
    with col_back:
        if st.button("← Back", key="back_att", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()


# ════════════════════════════════════════════
#  PAGE: REPORT
# ════════════════════════════════════════════
def report_page(section: str):
    user = st.session_state.user

    st.markdown(f"""
    <div class='page-header'>
        <h1>📊 Report — {section}</h1>
        <p>Attendance summary for all students</p>
    </div>
    """, unsafe_allow_html=True)

    df = load_section(user, section)
    if df.empty:
        st.warning("No data available.")
        if st.button("← Back"):
            st.session_state.page = "dashboard"
            st.rerun()
        return

    report = build_report(df)

    def color_pct(val):
        if not isinstance(val, float):
            return ""
        if val >= 75:  return "color:#16A34A; font-weight:700"
        if val < 60:   return "color:#DC2626; font-weight:700"
        return "color:#D97706; font-weight:700"

    styled = report.style.map(color_pct, subset=["Attendance %"])
    st.dataframe(styled, use_container_width=True, hide_index=True)

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Students",  len(report))
    m2.metric("≥ 75% Attendance", int((report["Attendance %"] >= 75).sum()))
    m3.metric("< 60% (At Risk)",  int((report["Attendance %"] < 60).sum()))

    st.markdown("---")
    col_dl, col_back = st.columns([3, 1])
    with col_dl:
        st.download_button(
            "📥 Download Excel Report",
            data=excel_bytes(report),
            file_name=f"{section}_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True,
        )
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()


# ════════════════════════════════════════════
#  PAGE: TEACHER DASHBOARD
# ════════════════════════════════════════════
def teacher_dashboard():
    user = st.session_state.user

    with st.sidebar:
        st.markdown(f"### 👤 {user}")
        st.caption("Teacher Account")
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    st.markdown(f"""
    <div class='page-header'>
        <h1>📘 My Dashboard</h1>
        <p>Manage your sections and take attendance</p>
    </div>
    """, unsafe_allow_html=True)

    # Create section
    with st.expander("➕ Create New Section", expanded=False):
        sec_name = st.text_input("Section Name", placeholder="e.g. BGE-3rd Year B", key="new_sec_name")
        if st.button("Create Section", type="primary"):
            ok, msg = create_section(user, sec_name)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    sections = list_sections(user)
    if not sections:
        st.info("No sections yet. Create one above to get started.")
        return

    st.markdown(f"### My Sections &nbsp; <span class='badge badge-blue'>{len(sections)}</span>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    for sec in sections:
        with st.expander(f"📘 {sec}", expanded=False):
            df     = load_section(user, sec)
            report = build_report(df)
            n      = len(report)
            good   = int((report["Attendance %"] >= 75).sum()) if n else 0
            risk   = int((report["Attendance %"] < 60).sum())  if n else 0
            total_cls = int(report["Total Classes"].max())      if n else 0

            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Students",     n)
            s2.metric("Classes",      total_cls)
            s3.metric("≥ 75%",        good)
            s4.metric("< 60% Risk",   risk)

            btn1, btn2, btn3 = st.columns([3, 3, 1])
            with btn1:
                if st.button("📋 Take Attendance", key=f"att_{sec}",
                             use_container_width=True, type="primary"):
                    st.session_state.page    = "attendance"
                    st.session_state.section = sec
                    st.rerun()
            with btn2:
                if st.button("📊 View Report", key=f"rep_{sec}", use_container_width=True):
                    st.session_state.page    = "report"
                    st.session_state.section = sec
                    st.rerun()
            with btn3:
                if st.button("🗑️", key=f"del_sec_{sec}", help="Delete this section"):
                    st.session_state[f"confirm_del_{sec}"] = True

            if st.session_state.get(f"confirm_del_{sec}"):
                st.warning(f"Delete **{sec}** and all its data? This cannot be undone.")
                y, n_ = st.columns(2)
                if y.button("Yes, delete", key=f"yes_del_{sec}", type="primary"):
                    delete_section(user, sec)
                    del st.session_state[f"confirm_del_{sec}"]
                    st.success(f"Section '{sec}' deleted.")
                    st.rerun()
                if n_.button("Cancel", key=f"no_del_{sec}"):
                    del st.session_state[f"confirm_del_{sec}"]
                    st.rerun()

            st.markdown("---")
            st.markdown("##### 👨‍🎓 Students")
            student_manager(user, sec, editable=True)


# ════════════════════════════════════════════
#  PAGE: ADMIN PANEL
# ════════════════════════════════════════════
def admin_panel():
    with st.sidebar:
        st.markdown("### 🔧 Admin")
        st.caption("Administrator Account")
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    st.markdown("""
    <div class='page-header'>
        <h1>🔧 Admin Panel</h1>
        <p>Manage teacher accounts and view all data</p>
    </div>
    """, unsafe_allow_html=True)

    users    = load_users()
    teachers = [u for u in users if u != "admin"]

    tab_users, tab_data = st.tabs(["👥 User Management", "📂 All Data"])

    # ── TAB 1: User Management ──
    with tab_users:
        st.subheader("➕ Create Teacher Account")
        c1, c2, c3 = st.columns(3)
        new_u  = c1.text_input("Username",         key="new_teacher_u", placeholder="Username")
        new_p  = c2.text_input("Password",          key="new_teacher_p", type="password", placeholder="Password")
        new_p2 = c3.text_input("Confirm Password",  key="new_teacher_p2", type="password", placeholder="Confirm")

        if st.button("💾 Create Teacher Account", type="primary"):
            if new_p != new_p2:
                st.error("Passwords do not match.")
            else:
                ok, msg = register_user(new_u, new_p)
                if ok:
                    st.success(msg)
                    for k in ["new_teacher_u", "new_teacher_p", "new_teacher_p2"]:
                        st.session_state.pop(k, None)
                    st.rerun()
                else:
                    st.error(msg)

        st.markdown("---")
        st.subheader("Current Teachers")

        if not teachers:
            st.info("No teacher accounts yet.")
        else:
            for t in teachers:
                with st.expander(f"👤 {t}"):
                    secs = list_sections(t)
                    st.markdown(
                        f"**Sections:** {', '.join(secs) if secs else 'None'}"
                    )
                    st.markdown("<br>", unsafe_allow_html=True)

                    r1, r2 = st.columns(2)
                    with r1:
                        new_pwd = st.text_input(
                            "New Password", type="password",
                            key=f"rpwd_{t}", placeholder="Min. 4 characters"
                        )
                        if st.button("🔑 Reset Password", key=f"reset_{t}", type="primary"):
                            ok, msg = reset_password(t, new_pwd)
                            st.success(msg) if ok else st.error(msg)

                    with r2:
                        st.markdown("&nbsp;", unsafe_allow_html=True)
                        if st.button("🗑️ Delete User", key=f"deluser_{t}"):
                            st.session_state[f"confirm_delusr_{t}"] = True

                    if st.session_state.get(f"confirm_delusr_{t}"):
                        st.warning(f"Delete **{t}** and ALL their data? This cannot be undone.")
                        y, n_ = st.columns(2)
                        if y.button("Yes, delete", key=f"yes_delusr_{t}", type="primary"):
                            ok, msg = delete_user(t)
                            st.success(msg) if ok else st.error(msg)
                            del st.session_state[f"confirm_delusr_{t}"]
                            st.rerun()
                        if n_.button("Cancel", key=f"no_delusr_{t}"):
                            del st.session_state[f"confirm_delusr_{t}"]
                            st.rerun()

    # ── TAB 2: All Data ──
    with tab_data:
        if not teachers:
            st.info("No teachers yet.")
        else:
            sel_teacher = st.selectbox("Select Teacher", teachers)
            secs = list_sections(sel_teacher)
            if not secs:
                st.info("No sections for this teacher.")
            else:
                sel_sec = st.selectbox("Select Section", secs)
                df      = load_section(sel_teacher, sel_sec)

                sub1, sub2 = st.tabs(["Students", "Attendance Report"])
                with sub1:
                    student_manager(sel_teacher, sel_sec, editable=True)
                with sub2:
                    if df.empty:
                        st.info("No data.")
                    else:
                        report = build_report(df)
                        st.dataframe(report, use_container_width=True, hide_index=True)
                        st.download_button(
                            "📥 Download Report",
                            data=excel_bytes(report),
                            file_name=f"{sel_teacher}_{sel_sec}_report.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            type="primary",
                        )


# ════════════════════════════════════════════
#  PAGE: LOGIN / REGISTER
# ════════════════════════════════════════════
def login_page():
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        st.markdown("""
        <div class='login-wrap'>
            <div class='login-logo'>📘</div>
            <div class='login-title'>Smart Attendance</div>
            <div class='login-sub'>Manage classes, track attendance, generate reports</div>
        </div>
        """, unsafe_allow_html=True)

        # Re-render inputs outside the HTML div (Streamlit needs to own them)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        tab_login, tab_reg = st.tabs(["🔓 Login", "📝 Register"])

        with tab_login:
            uname = st.text_input("Username", key="l_u", placeholder="Enter username")
            pwd   = st.text_input("Password", type="password", key="l_p", placeholder="Enter password")
            if st.button("Login", type="primary", use_container_width=True):
                users = load_users()
                if uname in users and users[uname]["password"] == hp(pwd):
                    st.session_state.user = uname
                    st.session_state.role = users[uname]["role"]
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

        with tab_reg:
            ru  = st.text_input("Username", key="r_u", placeholder="Choose a username")
            rp  = st.text_input("Password", type="password", key="r_p", placeholder="Min. 4 characters")
            rp2 = st.text_input("Confirm",  type="password", key="r_p2", placeholder="Repeat password")
            if st.button("Create Account", type="primary", use_container_width=True):
                if rp != rp2:
                    st.error("Passwords do not match.")
                else:
                    ok, msg = register_user(ru, rp)
                    if ok:
                        st.success(msg + " Please log in.")
                        st.rerun()
                    else:
                        st.error(msg)


# ════════════════════════════════════════════
#  MAIN ROUTER
# ════════════════════════════════════════════
def main():
    if not st.session_state.get("user"):
        login_page()
        return

    role = st.session_state.get("role", "teacher")

    if role == "admin":
        admin_panel()
        return

    page = st.session_state.get("page", "dashboard")
    sec  = st.session_state.get("section", "")

    if page == "attendance" and sec:
        attendance_page(sec)
    elif page == "report" and sec:
        report_page(sec)
    else:
        st.session_state.page = "dashboard"
        teacher_dashboard()


if __name__ == "__main__":
    main()
