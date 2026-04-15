import streamlit as st
import pandas as pd
import os
import json
import hashlib
from datetime import datetime
from io import BytesIO

# ---------------------------------------------
#  CONFIGURATION
# ---------------------------------------------
USERS_FILE  = "biotrack_users.json"
REPORTS_DIR = "biotrack_reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

# ---------------------------------------------
#  PAGE CONFIG & CSS
# ---------------------------------------------
st.set_page_config(page_title="BioTrack", page_icon="🧬", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Share+Tech+Mono&display=swap');

html, body, [class*="css"] { font-family: 'Share Tech Mono', monospace; }
.main { background-color: #0D1117; }

h1, h2, h3 { font-family: 'Orbitron', sans-serif; color: #38BDF8; }

.pct-ok  { color: #22C55E; font-weight: bold; }
.pct-bad { color: #EF4444; font-weight: bold; }
.pct-mid { color: #FBBF24; font-weight: bold; }

.info-box {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 10px;
}
.section-badge {
    display: inline-block;
    background: #1D4ED8;
    color: white;
    border-radius: 4px;
    padding: 2px 10px;
    font-size: 0.82em;
    margin-left: 6px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------
#  USER / AUTH HELPERS
# ---------------------------------------------
def _hash(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()

DEFAULT_ADMIN = {"password": _hash("bge2024"), "role": "admin", "sections": []}

def load_users() -> dict:
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE) as f:
            return json.load(f)
    users = {"admin": DEFAULT_ADMIN}
    save_users(users)
    return users

def save_users(users: dict):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

# ---------------------------------------------
#  SECTION / EXCEL HELPERS
# ---------------------------------------------
FIXED_COLS = ["ID", "Name", "Total Present", "Total Absent", "Total Class", "Attendance %"]

def section_file(section: str) -> str:
    safe = section.replace(" ", "_").replace("/", "-")
    return os.path.join(REPORTS_DIR, f"{safe}.xlsx")

def load_section(section: str) -> pd.DataFrame:
    path = section_file(section)
    if os.path.exists(path):
        df = pd.read_excel(path, dtype={"ID": str})
        for col in FIXED_COLS:
            if col not in df.columns:
                df[col] = 0
        for col in ["Total Present", "Total Absent", "Total Class", "Attendance %"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        return df
    return pd.DataFrame(columns=FIXED_COLS)

def save_section(df: pd.DataFrame, section: str):
    df = recalculate(df)
    df.to_excel(section_file(section), index=False)

def recalculate(df: pd.DataFrame) -> pd.DataFrame:
    date_cols = [c for c in df.columns if c not in FIXED_COLS]
    n = len(date_cols)
    if n == 0:
        df["Total Present"] = 0
        df["Total Absent"]  = 0
        df["Total Class"]   = 0
        df["Attendance %"]  = 0.0
        return df

    for idx in df.index:
        vals = df.loc[idx, date_cols]
        present = int(pd.to_numeric(vals, errors="coerce").fillna(0).sum())
        df.at[idx, "Total Present"] = present
        df.at[idx, "Total Absent"]  = n - present
        df.at[idx, "Total Class"]   = n
        df.at[idx, "Attendance %"]  = round(present / n * 100, 1)
    return df

def list_all_sections() -> list:
    files = [f for f in os.listdir(REPORTS_DIR) if f.endswith(".xlsx")]
    return sorted([f[:-5].replace("_", " ") for f in files])

# ---------------------------------------------
#  SESSION STATE INIT
# ---------------------------------------------
for k, v in [("logged_in", False), ("username", ""), ("role", ""), ("page", "attendance")]:
    if k not in st.session_state:
        st.session_state[k] = v

# ---------------------------------------------
#  LOGIN PAGE
# ---------------------------------------------
def login_page():
    st.title("🧬 BioTrack — Smart Attendance")
    st.markdown("---")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.subheader("Login")
        user = st.text_input("Username")
        pwd  = st.text_input("Password", type="password")
        if st.button("🔓 Login", use_container_width=True):
            users = load_users()
            if user in users and users[user]["password"] == _hash(pwd):
                st.session_state.logged_in = True
                st.session_state.username  = user
                st.session_state.role      = users[user]["role"]
                st.rerun()
            else:
                st.error("Invalid username or password!")

# ---------------------------------------------
#  SIDEBAR NAV
# ---------------------------------------------
def sidebar():
    with st.sidebar:
        st.markdown("### 🧬 BioTrack")
        st.markdown(f"**User:** `{st.session_state.username}`  "
                    f"<span class='section-badge'>{st.session_state.role}</span>",
                    unsafe_allow_html=True)
        st.markdown("---")

        pages = ["📋 Attendance", "📊 Reports"]
        if st.session_state.role == "admin":
            pages += ["👥 Manage Users", "🗂️ Manage Sections"]

        choice = st.radio("Menu", pages, label_visibility="collapsed")
        st.markdown("---")

        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.username  = ""
            st.session_state.role      = ""
            st.session_state.page      = "attendance"
            st.rerun()
        return choice

# ---------------------------------------------
#  PAGE: ATTENDANCE
# ---------------------------------------------
def page_attendance():
    st.title("📋 Attendance Entry")
    users = load_users()
    u = st.session_state.username

    if st.session_state.role == "admin":
        available = list_all_sections()
    else:
        available = users[u].get("sections", [])

    if not available:
        st.warning("No sections assigned. Please contact Admin.")
        return

    c1, c2, c3, c4 = st.columns([2, 2, 2, 3])
    with c1:
        section = st.selectbox("Section", available)
    with c2:
        sel_date = st.date_input("Date", datetime.now())
    with c3:
        session  = st.selectbox("Session", ["AM", "PM", "Extra"])
    with c4:
        search   = st.text_input("🔍 Search ID / Name")

    date_key = f"{sel_date}_{session}"
    st.markdown(f"**Entry:** `{section}` → `{date_key}`")

    df = load_section(section)
    if df.empty:
        st.info("No students in this section. Add students via 'Manage Sections'.")
        return

    if date_key not in df.columns:
        df[date_key] = 0

    if search:
        mask = (df["ID"].str.contains(search, case=False, na=False) |
                df["Name"].str.contains(search, case=False, na=False))
        view_df = df[mask].copy()
    else:
        view_df = df.copy()

    attendance_map = {}
    with st.form("att_form"):
        st.markdown(f"**Total Students: {len(view_df)}**")
        header = st.columns([3, 1, 1])
        header[0].markdown("**Student**")
        header[1].markdown("**Present**")
        header[2].markdown("**Attendance %**")
        st.divider()

        for _, row in view_df.iterrows():
            sid = str(row["ID"])
            pct = float(row.get("Attendance %", 0))
            pct_class = "pct-ok" if pct >= 75 else ("pct-mid" if pct >= 60 else "pct-bad")

            try:
                cur_val = int(row[date_key])
            except:
                cur_val = 0
            default = cur_val == 1

            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"`{sid}` {row['Name']}")
            with col2:
                attendance_map[sid] = st.checkbox(
                    "✔", value=default,
                    key=f"cb_{sid}_{date_key}_{section}",
                    label_visibility="collapsed"
                )
            with col3:
                st.markdown(f"<span class='{pct_class}'>{pct}%</span>", unsafe_allow_html=True)

        submitted = st.form_submit_button("💾 Save Attendance", use_container_width=True)

    if submitted:
        df = load_section(section)
        if date_key not in df.columns:
            df[date_key] = 0
        for sid, present in attendance_map.items():
            df.loc[df["ID"] == sid, date_key] = 1 if present else 0
        save_section(df, section)
        st.success(f"✅ Attendance saved for {date_key}!")
        st.rerun()

# ---------------------------------------------
#  PAGE: REPORTS
# ---------------------------------------------
def page_reports():
    st.title("📊 Attendance Reports")
    users = load_users()
    u = st.session_state.username

    if st.session_state.role == "admin":
        available = list_all_sections()
    else:
        available = users[u].get("sections", [])

    if not available:
        st.warning("No sections available.")
        return

    section = st.selectbox("Select Section", available)
    df = load_section(section)

    if df.empty:
        st.info("No data available for this section.")
        return

    df = recalculate(df)
    total_s = len(df)
    good    = len(df[df["Attendance %"] >= 75])
    bad     = len(df[df["Attendance %"] < 60])

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Students", total_s)
    m2.metric("≥75% (Safe)", good)
    m3.metric("<60% (Danger)", bad)
    m4.metric("Total Classes", int(df["Total Class"].max()) if not df.empty else 0)

    st.divider()
    st.subheader("Overall Summary")
    display_cols = ["ID", "Name", "Total Class", "Total Present", "Total Absent", "Attendance %"]

    styled = df[display_cols].style.map(
        lambda v: "color: #22C55E" if isinstance(v, float) and v >= 75
        else ("color: #EF4444" if isinstance(v, float) and v < 60 else ""),
        subset=["Attendance %"]
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)

    st.divider()
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df[display_cols].to_excel(writer, sheet_name="Summary", index=False)
        df.to_excel(writer, sheet_name="Full Data", index=False)

    st.download_button(
        "⬇️ Download Excel Report",
        data=buf.getvalue(),
        file_name=f"BioTrack_{section}_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ---------------------------------------------
#  PAGE: MANAGE USERS
# ---------------------------------------------
def page_manage_users():
    st.title("👥 User Management")
    users = load_users()

    st.subheader("Current Users")
    rows = []
    for uname, info in users.items():
        rows.append({"Username": uname, "Role": info["role"],
                     "Sections": ", ".join(info.get("sections", []))})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Create New Teacher")
    with st.form("add_user_form"):
        new_user = st.text_input("Username")
        new_pwd  = st.text_input("Password", type="password")
        new_pwd2 = st.text_input("Confirm Password", type="password")
        all_secs = list_all_sections()
        assigned = st.multiselect("Assign Sections", all_secs)
        if st.form_submit_button("➕ Create Teacher"):
            if not new_user or not new_pwd:
                st.error("Fill all fields.")
            elif new_pwd != new_pwd2:
                st.error("Passwords do not match!")
            elif new_user in users:
                st.error("Username already exists!")
            else:
                users[new_user] = {"password": _hash(new_pwd),
                                   "role": "teacher", "sections": assigned}
                save_users(users)
                st.success(f"✅ `{new_user}` created!")
                st.rerun()

# ---------------------------------------------
#  PAGE: MANAGE SECTIONS (MOBILE OPTIMIZED)
# ---------------------------------------------
def page_manage_sections():
    st.title("🗂️ Section Management")

    st.subheader("Create New Section")
    with st.form("new_section_form"):
        sec_name = st.text_input("Section Name (e.g., BGE-2nd Year A)")
        if st.form_submit_button("➕ Create Section"):
            if not sec_name.strip():
                st.error("Name is required.")
            elif os.path.exists(section_file(sec_name)):
                st.warning("Section already exists.")
            else:
                empty = pd.DataFrame(columns=FIXED_COLS)
                save_section(empty, sec_name)
                st.success(f"✅ `{sec_name}` created!")
                st.rerun()

    st.divider()

    st.subheader("Add Students to Section")
    all_secs = list_all_sections()
    if not all_secs:
        st.info("Create a section first.")
        return

    # MOBILE OPTIMIZATION: Choice between single entry and bulk
    entry_mode = st.radio("Entry Method", ["Single Student (Mobile Friendly)", "Bulk Paste (CSV)"], horizontal=True)

    if entry_mode == "Single Student (Mobile Friendly)":
        with st.form("single_student_form", clear_on_submit=True):
            target_sec = st.selectbox("Select Section", all_secs)
            s_id = st.text_input("Student ID")
            s_name = st.text_input("Student Name")
            if st.form_submit_button("➕ Add Student", use_container_width=True):
                if s_id and s_name:
                    df = load_section(target_sec)
                    if s_id in df["ID"].values:
                        st.error("ID already exists.")
                    else:
                        new_row = {"ID": s_id, "Name": s_name, "Total Present": 0, "Total Absent": 0, "Total Class": 0, "Attendance %": 0.0}
                        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                        save_section(df, target_sec)
                        st.success(f"Added {s_name} successfully!")
                else:
                    st.error("Fill both ID and Name.")

    else:
        with st.form("bulk_students_form"):
            target_sec = st.selectbox("Select Section", all_secs)
            st.caption("CSV Format: ID,Name (One per line)")
            raw = st.text_area("Paste List Here", placeholder="2206001,John Doe\n2206002,Jane Smith")
            if st.form_submit_button("➕ Add Bulk", use_container_width=True):
                df = load_section(target_sec)
                added = 0
                for line in raw.strip().splitlines():
                    parts = [p.strip() for p in line.split(",", 1)]
                    if len(parts) == 2:
                        sid, name = parts
                        if sid not in df["ID"].values:
                            new_row = {"ID": sid, "Name": name, "Total Present": 0, "Total Absent": 0, "Total Class": 0, "Attendance %": 0.0}
                            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                            added += 1
                save_section(df, target_sec)
                st.success(f"Added {added} students!")
                st.rerun()

    st.divider()
    st.subheader("Manage Existing Students")
    view_sec = st.selectbox("View Section", all_secs)
    df = load_section(view_sec)
    if not df.empty:
        st.dataframe(df[["ID", "Name", "Attendance %"]], use_container_width=True, hide_index=True)
        with st.form("delete_student_form"):
            del_id = st.text_input("Enter ID to Delete")
            if st.form_submit_button("🗑️ Delete Student", type="primary"):
                if del_id in df["ID"].values:
                    df = df[df["ID"] != del_id]
                    save_section(df, view_sec)
                    st.success(f"Deleted {del_id}")
                    st.rerun()

    st.divider()
    st.subheader("Delete Section ⚠️")
    with st.form("del_sec_form"):
        ds = st.selectbox("Section", all_secs)
        confirm = st.text_input("Type 'DELETE' to confirm")
        if st.form_submit_button("🗑️ Delete Section", type="primary"):
            if confirm == "DELETE":
                os.remove(section_file(ds))
                st.success("Section deleted.")
                st.rerun()

# ---------------------------------------------
#  MAIN ROUTER
# ---------------------------------------------
if not st.session_state.logged_in:
    login_page()
    st.stop()

choice = sidebar()
if "Attendance" in choice:
    page_attendance()
elif "Reports" in choice:
    page_reports()
elif "Users" in choice:
    page_manage_users()
elif "Sections" in choice:
    page_manage_sections()
