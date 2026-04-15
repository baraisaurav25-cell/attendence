import streamlit as st
import pandas as pd
import os
import json
import hashlib
from datetime import date

# =========================
# CONFIG
# =========================
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

USERS_FILE = os.path.join(DATA_DIR, "users.json")
FIXED_COLS = ["ID", "Name"]

# =========================
# UTIL
# =========================
def hash_pwd(p):
    return hashlib.sha256(p.encode()).hexdigest()

def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# =========================
# USERS + SECTIONS DB
# =========================
def load_users():
    users = load_json(USERS_FILE, None)

    if users is None:
        users = {
            "admin": {
                "password": hash_pwd("admin123"),
                "role": "admin",
                "sections": []
            }
        }
        save_json(USERS_FILE, users)

    return users

def save_users(users):
    save_json(USERS_FILE, users)

def register_user(u, p):
    users = load_users()

    if u in users:
        return False

    users[u] = {
        "password": hash_pwd(p),
        "role": "teacher",
        "sections": []
    }

    save_users(users)
    return True

# =========================
# SECTION DB
# =========================
def section_path(name):
    return os.path.join(DATA_DIR, f"{name.replace(' ', '_')}.xlsx")

def load_section(name):
    path = section_path(name)

    if os.path.exists(path):
        df = pd.read_excel(path, dtype={"ID": str})
    else:
        df = pd.DataFrame(columns=FIXED_COLS)

    for c in FIXED_COLS:
        if c not in df.columns:
            df[c] = ""

    return df

def save_section(df, name):
    df.to_excel(section_path(name), index=False)

def list_sections():
    return [f[:-5].replace("_", " ") for f in os.listdir(DATA_DIR) if f.endswith(".xlsx")]

# =========================
# LOGIN
# =========================
def login():
    st.title("🧬 Smart Attendance System")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        users = load_users()

        if u in users and users[u]["password"] == hash_pwd(p):
            st.session_state.user = u
            st.session_state.role = users[u]["role"]
            st.session_state.page = "dashboard"
            st.rerun()
        else:
            st.error("Invalid login")

# =========================
# ADMIN PANEL
# =========================
def admin_panel():
    st.title("👨‍💼 Admin Panel")

    users = load_users()

    # ---------- USERS ----------
    st.subheader("Users")

    for u, data in users.items():
        st.write(f"👤 {u} ({data['role']})")

    st.divider()

    # ---------- APPROVE SECTION ----------
    st.subheader("Assign Sections to Teachers")

    teachers = [u for u in users if users[u]["role"] == "teacher"]

    if teachers:
        teacher = st.selectbox("Teacher", teachers)

        all_sections = list_sections()

        selected = st.multiselect("Assign Sections", all_sections)

        if st.button("Save Assignment"):
            users[teacher]["sections"] = selected
            save_users(users)
            st.success("Assigned")
            st.rerun()

# =========================
# TEACHER DASHBOARD
# =========================
def dashboard():
    st.title(f"🏠 Dashboard - {st.session_state.user}")

    users = load_users()
    user = st.session_state.user

    sections = users[user].get("sections", [])

    # ---------- TEACHER CAN REQUEST SECTION ----------
    st.subheader("➕ Create Section Request")

    new_sec = st.text_input("New Section Name")

    if st.button("Request Section"):
        if new_sec.strip():
            if new_sec not in list_sections():
                save_section(pd.DataFrame(columns=FIXED_COLS), new_sec)
                st.success("Section created (pending admin assignment)")
            else:
                st.warning("Already exists")

    st.divider()

    if not sections:
        st.warning("No approved sections yet (wait for admin)")
        return

    st.subheader("Your Sections")

    for sec in sections:
        if st.button(f"📘 {sec}", key=sec):
            st.session_state.selected_section = sec
            st.session_state.page = "attendance"
            st.rerun()

    st.divider()

    if st.button("📊 My Reports"):
        st.session_state.page = "reports"
        st.rerun()

# =========================
# ATTENDANCE
# =========================
def attendance_page():
    sec = st.session_state.selected_section
    st.title(f"📋 Attendance → {sec}")

    df = load_section(sec)

    if df.empty:
        st.warning("No students")
        return

    d = st.date_input("Date")
    session = st.selectbox("Session", ["AM", "PM"])

    col = f"{d}_{session}"

    if col not in df.columns:
        df[col] = 0

    date_cols = [c for c in df.columns if c not in FIXED_COLS]

    temp = df.copy()
    temp["%"] = (temp[date_cols].sum(axis=1) / len(date_cols) * 100).round(1) if date_cols else 0

    attendance = {}

    for _, r in temp.iterrows():
        sid = str(r["ID"])
        name = r["Name"]
        percent = r["%"]

        color = "green" if percent >= 60 else "red"

        c1, c2, c3 = st.columns([2, 5, 2])

        with c1:
            if st.button(sid, key=f"{sid}_{col}"):
                cur = df.loc[df["ID"] == sid, col].values[0]
                df.loc[df["ID"] == sid, col] = 0 if int(cur or 0) == 1 else 1
                save_section(df, sec)
                st.rerun()

        with c2:
            st.write(name)

        with c3:
            st.markdown(f"<b style='color:{color}'>{percent}%</b>", unsafe_allow_html=True)

        attendance[sid] = st.checkbox("", value=bool(df.loc[df["ID"] == sid, col].values[0] or 0), key=sid)

    if st.button("💾 Save Attendance"):
        for sid, val in attendance.items():
            df.loc[df["ID"] == sid, col] = 1 if val else 0

        save_section(df, sec)

        st.session_state.page = "dashboard"
        st.rerun()

# =========================
# REPORT
# =========================
def report_page():
    st.title("📊 My Reports")

    users = load_users()
    user = st.session_state.user

    sections = users[user].get("sections", [])

    if not sections:
        st.warning("No sections assigned")
        return

    for sec in sections:
        st.subheader(f"📘 {sec}")

        df = load_section(sec)

        cols = [c for c in df.columns if c not in FIXED_COLS]

        if cols:
            df["Total"] = df[cols].sum(axis=1)
            df["%"] = (df["Total"] / len(cols) * 100).round(1)
        else:
            df["%"] = 0

        st.dataframe(df[["ID", "Name", "%"]])

        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "⬇ Download Report",
            csv,
            file_name=f"{sec}_report.csv",
            mime="text/csv"
        )

# =========================
# MAIN ROUTER
# =========================
def main():
    if "page" not in st.session_state:
        st.session_state.page = "login"

    if st.session_state.page == "login":
        login()

    elif st.session_state.page == "dashboard":
        if st.session_state.role == "admin":
            admin_panel()
        else:
            dashboard()

    elif st.session_state.page == "attendance":
        attendance_page()

    elif st.session_state.page == "reports":
        report_page()

main()
