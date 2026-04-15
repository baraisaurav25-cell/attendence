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
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Mono', monospace;
    background-color: #F7F5F2;
    color: #1A1A2E;
}
h1, h2, h3 { font-family: 'Syne', sans-serif; font-weight: 800; }

/* Save button — always prominent */
div[data-testid="stForm"] button[kind="primaryFormSubmit"],
button.save-btn {
    background: #0F4C81 !important;
    color: white !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 0.6rem 1.4rem !important;
    border-radius: 6px !important;
    border: none !important;
}

/* Generic primary button */
.stButton > button[kind="primary"] {
    background: #0F4C81;
    color: white;
    font-weight: 700;
    border-radius: 6px;
    border: none;
}

/* Save All Changes — standout style */
.stButton > button[data-testid*="save"],
.stButton > button:has(span:contains("💾")) {
    background: #0F4C81 !important;
    color: #FFFFFF !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 800 !important;
    font-size: 1.05rem !important;
    letter-spacing: 0.5px;
    border: 2px solid #0F4C81 !important;
    border-radius: 8px !important;
    padding: 0.65rem 1.6rem !important;
    box-shadow: 0 4px 14px rgba(15,76,129,0.35) !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    opacity: 0.88;
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(15,76,129,0.45) !important;
}

/* Present / Absent toggle buttons */
button[data-present="true"] { background: #16A34A !important; color: white !important; border-radius: 6px !important; }
button[data-present="false"]{ background: #DC2626 !important; color: white !important; border-radius: 6px !important; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #1A1A2E;
    color: #E2E8F0;
}
[data-testid="stSidebar"] * { color: #E2E8F0 !important; }
[data-testid="stSidebar"] .stButton > button {
    background: #2D2D4E;
    color: #E2E8F0;
    border: 1px solid #3D3D60;
    border-radius: 6px;
    width: 100%;
    text-align: left;
}

/* Section expander */
.streamlit-expanderHeader {
    background: #EEF2FF;
    border-radius: 8px;
    font-family: 'Syne', sans-serif;
    font-weight: 700;
}

/* Badge spans */
.badge-green { background:#DCFCE7; color:#15803D; padding:2px 10px; border-radius:99px; font-size:0.82em; font-weight:600; }
.badge-red   { background:#FEE2E2; color:#B91C1C; padding:2px 10px; border-radius:99px; font-size:0.82em; font-weight:600; }
.badge-blue  { background:#DBEAFE; color:#1D4ED8; padding:2px 10px; border-radius:99px; font-size:0.82em; font-weight:600; }

/* Card */
.card {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

/* Metric overrides */
[data-testid="metric-container"] {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 14px;
}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════
#  UTILITIES  (safe, never crash)
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
    # Remove all section files belonging to this user
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
def _safe_name(s: str) -> str:
    """Sanitise for filesystem."""
    return s.strip().replace(" ", "_").replace("/", "-").replace("\\", "-")


def section_path(user: str, section: str) -> str:
    return os.path.join(DATA_DIR, f"{_safe_name(user)}__{_safe_name(section)}.xlsx")


def load_section(user: str, section: str) -> pd.DataFrame:
    path = section_path(user, section)
    try:
        if os.path.exists(path):
            df = pd.read_excel(path, dtype={"ID": str})
            for col in FIXED_COLS:
                if col not in df.columns:
                    df[col] = ""
            # Coerce attendance columns to int safely
            att_cols = [c for c in df.columns if c not in FIXED_COLS]
            for c in att_cols:
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
    prefix = f"{_safe_name(user)}__"
    result = []
    try:
        for fname in sorted(os.listdir(DATA_DIR)):
            if fname.startswith(prefix) and fname.endswith(".xlsx"):
                result.append(fname[len(prefix):-5].replace("_", " "))
    except OSError:
        pass
    return result


def create_section(user: str, section: str) -> tuple[bool, str]:
    section = section.strip()
    if not section:
        return False, "Section name cannot be empty."
    existing = list_sections(user)
    if section in existing:
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
    total = row[cols].sum(axis=1).values[0]
    return round(total / len(cols) * 100, 1)


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


# ════════════════════════════════════════════
#  SHARED: STUDENT MANAGER WIDGET
# ════════════════════════════════════════════
def student_manager(user: str, section: str, editable: bool = True):
    df = load_section(user, section)
    key_pfx = f"{user}__{section}"

    if editable:
        mode = st.radio("Add Method", ["Manual", "Bulk (CSV paste)"],
                        horizontal=True, key=f"mode_{key_pfx}")
        if mode == "Manual":
            c1, c2, c3 = st.columns([2, 3, 1])
            sid  = c1.text_input("Student ID",   key=f"sid_{key_pfx}")
            name = c2.text_input("Student Name", key=f"sname_{key_pfx}")
            if c3.button("➕ Add", key=f"add_{key_pfx}"):
                sid, name = sid.strip(), name.strip()
                if not sid or not name:
                    st.error("Both ID and Name are required.")
                elif sid in df["ID"].astype(str).values:
                    st.error(f"ID '{sid}' already exists.")
                else:
                    new_row = pd.DataFrame([{"ID": sid, "Name": name}])
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_section(user, section, df)
                    st.success(f"Added: {name}")
                    st.rerun()
        else:
            bulk = st.text_area("Paste  ID,Name  (one per line)",
                                placeholder="2206001,Rahim Uddin\n2206002,Fatima Islam",
                                key=f"bulk_{key_pfx}")
            if st.button("➕ Add All", key=f"bulk_btn_{key_pfx}"):
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
                    st.success(f"Added {len(added)} student(s).")
                    if skipped:
                        st.warning(f"Skipped (duplicate/empty): {', '.join(skipped)}")
                    st.rerun()
                else:
                    st.error("No valid rows found.")

    # Display list
    if df.empty:
        st.info("No students yet.")
        return

    st.markdown(f"**{len(df)} student(s)**")
    edited = st.data_editor(
        df[FIXED_COLS].reset_index(drop=True),
        use_container_width=True,
        key=f"editor_{key_pfx}",
        disabled=not editable,
        hide_index=True,
    )
    if editable:
        if st.button("💾 Save Student Changes", key=f"save_stu_{key_pfx}", type="primary"):
            # Merge edits back, preserve attendance columns
            att = [c for c in df.columns if c not in FIXED_COLS]
            if att:
                merged = edited.merge(df[["ID"] + att], on="ID", how="left")
            else:
                merged = edited
            save_section(user, section, merged)
            st.success("✅ Student list saved.")
            st.rerun()

    # Delete individual student
    with st.expander("🗑️ Remove a student"):
        del_id = st.text_input("Enter Student ID to remove", key=f"del_stu_{key_pfx}")
        if st.button("Remove", key=f"del_stu_btn_{key_pfx}"):
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
    st.title(f"📋 Attendance — {section}")

    df = load_section(user, section)
    if df.empty:
        st.warning("No students in this section. Add students first.")
        if st.button("← Back"):
            st.session_state.page = "dashboard"
            st.rerun()
        return

    c1, c2 = st.columns(2)
    date         = c1.date_input("Date", datetime.now())
    session_type = c2.selectbox("Session", ["AM", "PM", "Extra"])
    col_name = f"{date}_{session_type}"

    # Ensure column exists
    if col_name not in df.columns:
        df[col_name] = 0

    # Live stats
    cols = att_cols(df)
    n_present_today = int(df[col_name].sum())
    n_total = len(df)
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Students", n_total)
    m2.metric("Present Today",  n_present_today)
    m3.metric("Absent Today",   n_total - n_present_today)

    st.markdown("---")
    st.markdown("#### Toggle Present / Absent")

    # Build sorted copy; use df directly (not a filtered copy) to avoid index drift
    changed = False
    for idx in df.index:
        sid   = str(df.at[idx, "ID"])
        name  = str(df.at[idx, "Name"])
        pct   = compute_pct(df, sid)
        present = int(df.at[idx, col_name]) == 1

        badge_html = (
            f"<span class='badge-green'>{pct}%</span>" if pct >= 75
            else f"<span class='badge-red'>{pct}%</span>" if pct < 60
            else f"<span class='badge-blue'>{pct}%</span>"
        )

        r1, r2, r3 = st.columns([3, 1, 1])
        r1.markdown(f"**{name}** `{sid}`")
        r3.markdown(badge_html, unsafe_allow_html=True)

        btn_label = "✅ Present" if present else "❌ Absent"
        btn_type  = "primary" if not present else "secondary"
        if r2.button(btn_label, key=f"tog_{sid}_{col_name}", type=btn_type):
            df.at[idx, col_name] = 0 if present else 1
            changed = True

    st.markdown("---")
    col_save, col_back = st.columns([2, 1])
    with col_save:
        if st.button("💾 Save All Changes", key="save_all_att", type="primary", use_container_width=True):
            save_section(user, section, df)
            st.success("✅ Attendance saved successfully!")
            st.session_state.page = "dashboard"
            st.rerun()
    with col_back:
        if st.button("← Back to Dashboard", key="back_att", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()

    if changed:
        save_section(user, section, df)
        st.rerun()


# ════════════════════════════════════════════
#  PAGE: REPORT (fixed: applymap → map)
# ════════════════════════════════════════════
def report_page(section: str):
    user = st.session_state.user
    st.title(f"📊 Report — {section}")

    df = load_section(user, section)
    if df.empty:
        st.warning("No data.")
        if st.button("← Back"):
            st.session_state.page = "dashboard"
            st.rerun()
        return

    report = build_report(df)

    # Color the % column
    def color_pct(val):
        if isinstance(val, float):
            if val >= 75:  return "color:#15803D; font-weight:700"
            if val < 60:   return "color:#B91C1C; font-weight:700"
            return "color:#B45309; font-weight:700"
        return ""

    # FIX: applymap → map (pandas 2.1+ compatibility)
    styled = report.style.map(color_pct, subset=["Attendance %"])
    st.dataframe(styled, use_container_width=True, hide_index=True)

    # Summary metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Students", len(report))
    m2.metric("≥75% Attendance", int((report["Attendance %"] >= 75).sum()))
    m3.metric("<60% (At Risk)",  int((report["Attendance %"] < 60).sum()))

    st.markdown("---")
    st.download_button(
        "📥 Download Excel Report",
        data=excel_bytes(report),
        file_name=f"{section}_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True,
    )

    if st.button("← Back to Dashboard", use_container_width=True):
        st.session_state.page = "dashboard"
        st.rerun()


# ════════════════════════════════════════════
#  PAGE: TEACHER DASHBOARD
# ════════════════════════════════════════════
def teacher_dashboard():
    user = st.session_state.user
    st.title("📘 My Dashboard")

    # ── Sidebar ──
    with st.sidebar:
        st.markdown(f"### 👤 {user}")
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # ── Create section ──
    with st.expander("➕ Create New Section", expanded=False):
        sec_name = st.text_input("Section Name", placeholder="e.g. BGE-3rd Year B")
        if st.button("💾 Create Section", type="primary"):
            ok, msg = create_section(user, sec_name)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    sections = list_sections(user)
    if not sections:
        st.info("No sections yet. Create one above.")
        return

    st.markdown("---")
    st.markdown(f"### My Sections ({len(sections)})")

    for sec in sections:
        with st.expander(f"📘 {sec}", expanded=False):
            df = load_section(user, sec)
            report = build_report(df)

            # Quick stats
            n = len(report)
            good = int((report["Attendance %"] >= 75).sum()) if n else 0
            risk = int((report["Attendance %"] < 60).sum()) if n else 0
            total_cls = int(report["Total Classes"].max()) if n else 0

            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Students",    n)
            s2.metric("Classes",     total_cls)
            s3.metric("≥75%",        good)
            s4.metric("At Risk <60%", risk)

            btn1, btn2, btn3 = st.columns([2, 2, 1])
            with btn1:
                if st.button("📋 Take Attendance", key=f"att_{sec}", use_container_width=True, type="primary"):
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

            # Confirmation dialog for delete
            if st.session_state.get(f"confirm_del_{sec}"):
                st.warning(f"Delete **{sec}** and all its data?")
                y, n_ = st.columns(2)
                if y.button("Yes, delete", key=f"yes_del_{sec}", type="primary"):
                    delete_section(user, sec)
                    del st.session_state[f"confirm_del_{sec}"]
                    st.success(f"Section '{sec}' deleted.")
                    st.rerun()
                if n_.button("Cancel", key=f"no_del_{sec}"):
                    del st.session_state[f"confirm_del_{sec}"]
                    st.rerun()

            st.markdown("##### 👨‍🎓 Students")
            student_manager(user, sec, editable=True)


# ════════════════════════════════════════════
#  PAGE: ADMIN PANEL
# ════════════════════════════════════════════
def admin_panel():
    st.title("🔧 Admin Panel")

    with st.sidebar:
        st.markdown("### 🔧 Admin")
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    users = load_users()
    teachers = [u for u in users if u != "admin"]

    tab_users, tab_data = st.tabs(["👥 User Management", "📂 All Data"])

    # ── TAB 1: User management ──
    with tab_users:
        # Create teacher
        st.subheader("➕ Create Teacher Account")
        c1, c2, c3 = st.columns(3)
        new_u = c1.text_input("Username")
        new_p = c2.text_input("Password", type="password")
        new_p2= c3.text_input("Confirm",  type="password")
        if st.button("💾 Create Teacher", type="primary"):
            if new_p != new_p2:
                st.error("Passwords do not match.")
            else:
                ok, msg = register_user(new_u, new_p)
                st.success(msg) if ok else st.error(msg)
                if ok:
                    st.rerun()

        st.markdown("---")

        # List teachers
        st.subheader("Current Teachers")
        if not teachers:
            st.info("No teacher accounts yet.")
        else:
            for t in teachers:
                with st.expander(f"👤 {t}"):
                    secs = list_sections(t)
                    st.markdown(f"**Sections:** {', '.join(secs) if secs else 'None'}")

                    r1, r2 = st.columns(2)
                    # Reset password
                    with r1:
                        new_pwd = st.text_input("New Password", type="password", key=f"rpwd_{t}")
                        if st.button("🔑 Reset Password", key=f"reset_{t}", type="primary"):
                            ok, msg = reset_password(t, new_pwd)
                            st.success(msg) if ok else st.error(msg)

                    # Delete user
                    with r2:
                        st.markdown("&nbsp;", unsafe_allow_html=True)
                        if st.button("🗑️ Delete User", key=f"deluser_{t}"):
                            st.session_state[f"confirm_delusr_{t}"] = True

                    if st.session_state.get(f"confirm_delusr_{t}"):
                        st.warning(f"Delete **{t}** and ALL their data?")
                        y, n_ = st.columns(2)
                        if y.button("Yes, delete", key=f"yes_delusr_{t}", type="primary"):
                            ok, msg = delete_user(t)
                            st.success(msg) if ok else st.error(msg)
                            del st.session_state[f"confirm_delusr_{t}"]
                            st.rerun()
                        if n_.button("Cancel", key=f"no_delusr_{t}"):
                            del st.session_state[f"confirm_delusr_{t}"]
                            st.rerun()

    # ── TAB 2: View all data ──
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
                df = load_section(sel_teacher, sel_sec)

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
    st.markdown("<br>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown("## 📘 Smart Attendance System")
        st.markdown("---")
        tab_login, tab_reg = st.tabs(["Login", "Register"])

        with tab_login:
            uname = st.text_input("Username", key="l_u")
            pwd   = st.text_input("Password", type="password", key="l_p")
            if st.button("🔓 Login", type="primary", use_container_width=True):
                users = load_users()
                if uname in users and users[uname]["password"] == hp(pwd):
                    st.session_state.user = uname
                    st.session_state.role = users[uname]["role"]
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

        with tab_reg:
            ru = st.text_input("Username", key="r_u")
            rp = st.text_input("Password", type="password", key="r_p")
            rp2= st.text_input("Confirm",  type="password", key="r_p2")
            if st.button("📝 Register", type="primary", use_container_width=True):
                if rp != rp2:
                    st.error("Passwords do not match.")
                else:
                    ok, msg = register_user(ru, rp)
                    st.success(msg) if ok else st.error(msg)


# ════════════════════════════════════════════
#  MAIN ROUTER
# ════════════════════════════════════════════
def main():
    # Guard: must be logged in
    if "user" not in st.session_state or not st.session_state.get("user"):
        login_page()
        return

    role = st.session_state.get("role", "teacher")

    if role == "admin":
        admin_panel()
        return

    # Teacher routes
    page = st.session_state.get("page", "dashboard")
    if page == "attendance":
        sec = st.session_state.get("section", "")
        if sec:
            attendance_page(sec)
        else:
            st.session_state.page = "dashboard"
            st.rerun()
    elif page == "report":
        sec = st.session_state.get("section", "")
        if sec:
            report_page(sec)
        else:
            st.session_state.page = "dashboard"
            st.rerun()
    else:
        teacher_dashboard()


if __name__ == "__main__":
    main()
