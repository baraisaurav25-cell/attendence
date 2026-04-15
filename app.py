import streamlit as st
import pandas as pd
import os
import json
import hashlib
from datetime import datetime

# =========================
# CONFIG
# =========================
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

USERS_FILE = os.path.join(DATA_DIR, "users.json")
FIXED_COLS = ["ID", "Name"]

# =========================
# UTILS
# =========================
def hash_pwd(p):
    return hashlib.sha256(p.encode()).hexdigest()

def safe_json_load(path, default):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return default

def safe_json_save(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# =========================
# USERS SYSTEM
# =========================
def load_users():
    users = safe_json_load(USERS_FILE, None)
    if users is None:
        users = {
            "admin": {
                "password": hash_pwd("admin123"),
                "role": "admin",
                "sections": []
            }
        }
        safe_json_save(USERS_FILE, users)
    return users

def save_users(users):
    safe_json_save(USERS_FILE, users)

def register_user(username, password):
    users = load_users()
    if username in users:
        return False
    users[username] = {
        "password": hash_pwd(password),
        "role": "teacher",
        "sections": []
    }
    save_users(users)
    return True

# =========================
# FILE SYSTEM
# =========================
def section_file(sec):
    return os.path.join(DATA_DIR, f"{sec.replace(' ', '_')}.xlsx")

def list_sections():
    return [f[:-5].replace("_", " ") for f in os.listdir(DATA_DIR) if f.endswith(".xlsx")]

def load_section(sec):
    path = section_file(sec)
    if os.path.exists(path):
        df = pd.read_excel(path, dtype={"ID": str})
    else:
        df = pd.DataFrame(columns=FIXED_COLS)

    for col in FIXED_COLS:
        if col not in df.columns:
            df[col] = ""

    return df

def save_section(df, sec):
    df.to_excel(section_file(sec), index=False)

# =========================
# AUTH
# =========================
def login_page():
    st.title("🧬 BioTrack Login")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        u = st.text_input("Username", key="login_u")
        p = st.text_input("Password", type="password", key="login_p")

        if st.button("Login"):
            users = load_users()

            if u in users and users[u]["password"] == hash_pwd(p):
                st.session_state.user = u
                st.session_state.role = users[u]["role"]
                st.session_state.page = "main"
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        ru = st.text_input("New Username")
        rp = st.text_input("New Password", type="password")

        if st.button("Create Account"):
            if register_user(ru, rp):
                st.success("Account created! Now login.")
            else:
                st.error("Username already exists")

# =========================
# SECTION
# =========================
def list_sections_ui():
    st.title("🗂️ Sections")

    sec = st.text_input("New Section Name")
    if st.button("Create Section"):
        if sec.strip():
            save_section(pd.DataFrame(columns=FIXED_COLS), sec)
            st.success("Created!")
            st.rerun()

    sections = list_sections()
    if not sections:
        st.info("No sections")
        return None

    return st.selectbox("Select Section", sections)

# =========================
# ATTENDANCE
# =========================
def attendance_page():
    st.title("📋 Attendance System")

    users = load_users()
    user = st.session_state.user

    if st.session_state.role == "admin":
        sections = list_sections()
    else:
        sections = users[user].get("sections", [])

    if not sections:
        st.warning("No section assigned")
        return

    sec = st.selectbox("Section", sections)
    df = load_section(sec)

    if df.empty:
        st.warning("No students found")
        return

    date = st.date_input("Date")
    session = st.selectbox("Session", ["AM", "PM"])

    col = f"{date}_{session}"

    if col not in df.columns:
        df[col] = 0

    # attendance percent calculation
    date_cols = [c for c in df.columns if c not in FIXED_COLS]
    temp_df = df.copy()

    if date_cols:
        temp_df["Percent"] = (temp_df[date_cols].sum(axis=1) / len(date_cols) * 100).round(1)
    else:
        temp_df["Percent"] = 0

    st.subheader(f"{sec} Attendance")

    attendance_state = {}

    for i, row in temp_df.iterrows():
        sid = str(row["ID"])
        name = row["Name"]
        percent = row["Percent"]

        color = "green" if percent >= 60 else "red"

        col1, col2, col3, col4 = st.columns([2, 4, 2, 2])

        with col1:
            if st.button(sid, key=f"btn_{sid}_{col}"):
                current = int(df.loc[df["ID"] == sid, col].values[0] or 0)
                df.loc[df["ID"] == sid, col] = 0 if current == 1 else 1
                save_section(df, sec)
                st.rerun()

        with col2:
            st.write(f"{name}")

        with col3:
            st.markdown(f"<span style='color:{color}; font-weight:bold'>{percent}%</span>", unsafe_allow_html=True)

        with col4:
            val = int(df.loc[df["ID"] == sid, col].values[0] or 0)
            attendance_state[sid] = st.checkbox("Present", value=bool(val), key=f"chk_{sid}_{col}")

    if st.button("💾 Save Attendance"):
        for sid, present in attendance_state.items():
            df.loc[df["ID"] == sid, col] = 1 if present else 0

        save_section(df, sec)
        st.success("Saved!")
        st.session_state.page = "main"
        st.rerun()

# =========================
# REPORT
# =========================
def report_page():
    st.title("📊 Reports")

    sec = st.selectbox("Section", list_sections())
    df = load_section(sec)

    if df.empty:
        st.warning("No data")
        return

    date_cols = [c for c in df.columns if c not in FIXED_COLS]

    if date_cols:
        df["Total"] = df[date_cols].sum(axis=1)
        df["Percent"] = (df["Total"] / len(date_cols) * 100).round(1)
    else:
        df["Percent"] = 0

    st.dataframe(df[["ID", "Name", "Percent"]])

# =========================
# MAIN
# =========================
def main_app():
    st.sidebar.title("Menu")

    menu = st.sidebar.radio("Go to", ["Attendance", "Reports", "Sections"])

    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    if menu == "Attendance":
        attendance_page()
    elif menu == "Reports":
        report_page()
    else:
        list_sections_ui()

# =========================
# APP ENTRY
# =========================
if "page" not in st.session_state:
    st.session_state.page = "login"

if st.session_state.page == "login":
    login_page()
else:
    main_app()
