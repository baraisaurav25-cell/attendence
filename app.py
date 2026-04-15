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

def safe_load_json(path, default):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return default

def safe_save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# =========================
# USER SYSTEM
# =========================
def load_users():
    users = safe_load_json(USERS_FILE, None)

    if users is None:
        users = {
            "admin": {
                "password": hash_pwd("admin123"),
                "role": "admin",
                "sections": []
            }
        }
        safe_save_json(USERS_FILE, users)

    return users

def save_users(users):
    safe_save_json(USERS_FILE, users)

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
def section_file(name):
    return os.path.join(DATA_DIR, f"{name.replace(' ', '_')}.xlsx")

def list_sections():
    return [f[:-5].replace("_", " ") for f in os.listdir(DATA_DIR) if f.endswith(".xlsx")]

def load_section(name):
    path = section_file(name)

    if os.path.exists(path):
        df = pd.read_excel(path, dtype={"ID": str})
    else:
        df = pd.DataFrame(columns=FIXED_COLS)

    for c in FIXED_COLS:
        if c not in df.columns:
            df[c] = ""

    return df

def save_section(df, name):
    df.to_excel(section_file(name), index=False)

# =========================
# AUTH UI
# =========================
def login_page():
    st.title("🧬 BioTrack System")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login"):
            users = load_users()

            if u in users and users[u]["password"] == hash_pwd(p):
                st.session_state.user = u
                st.session_state.role = users[u]["role"]
                st.session_state.page = "home"
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        ru = st.text_input("New Username")
        rp = st.text_input("New Password", type="password")

        if st.button("Create Account"):
            if register_user(ru, rp):
                st.success("Account created")
            else:
                st.error("User already exists")

# =========================
# SECTIONS + STUDENTS
# =========================
def sections_page():
    st.title("🗂️ Section Management")

    # create section
    sec = st.text_input("New Section Name")

    if st.button("Create Section"):
        if sec.strip():
            save_section(pd.DataFrame(columns=FIXED_COLS), sec)
            st.success("Section created")
            st.rerun()

    st.divider()

    sections = list_sections()
    if not sections:
        st.warning("No sections found")
        return

    sec_sel = st.selectbox("Select Section", sections)
    df = load_section(sec_sel)

    st.divider()
    st.subheader("📥 Add Students")

    mode = st.radio("Input Method", ["Manual", "Paste", "Upload"])

    # -------- MANUAL --------
    if mode == "Manual":
        with st.form("m"):
            sid = st.text_input("Student ID")
            name = st.text_input("Student Name")

            if st.form_submit_button("Add"):
                if sid and name:
                    new = pd.DataFrame([{"ID": sid, "Name": name}])
                    df = pd.concat([df, new], ignore_index=True)
                    df = df.drop_duplicates(subset=["ID"])
                    save_section(df, sec_sel)
                    st.success("Added")
                    st.rerun()

    # -------- PASTE --------
    elif mode == "Paste":
        st.info("Format: ID, Name per line")

        txt = st.text_area("Paste here")

        if st.button("Add"):
            rows = []
            for line in txt.split("\n"):
                if "," in line:
                    i, n = line.split(",", 1)
                    rows.append({"ID": i.strip(), "Name": n.strip()})

            if rows:
                new = pd.DataFrame(rows)
                df = pd.concat([df, new], ignore_index=True)
                df = df.drop_duplicates(subset=["ID"])
                save_section(df, sec_sel)
                st.success("Added")
                st.rerun()

    # -------- UPLOAD --------
    else:
        f = st.file_uploader("CSV/XLSX", type=["csv", "xlsx"])

        if f:
            new = pd.read_csv(f) if f.name.endswith(".csv") else pd.read_excel(f)

            if "ID" not in new.columns or "Name" not in new.columns:
                st.error("Need ID & Name columns")
                return

            new = new[["ID", "Name"]].dropna()

            df = pd.concat([df, new], ignore_index=True)
            df = df.drop_duplicates(subset=["ID"])

            save_section(df, sec_sel)
            st.success("Uploaded")
            st.rerun()

    st.divider()
    st.subheader("📄 Students")
    st.dataframe(df, use_container_width=True)

# =========================
# ATTENDANCE
# =========================
def attendance_page():
    st.title("📋 Attendance")

    user = st.session_state.user
    users = load_users()

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
        st.warning("No students")
        return

    date = st.date_input("Date")
    session = st.selectbox("Session", ["AM", "PM"])
    col = f"{date}_{session}"

    if col not in df.columns:
        df[col] = 0

    date_cols = [c for c in df.columns if c not in FIXED_COLS]

    temp = df.copy()
    if date_cols:
        temp["%"] = (temp[date_cols].sum(axis=1) / len(date_cols) * 100).round(1)
    else:
        temp["%"] = 0

    attendance = {}

    st.subheader("Click ID to toggle attendance")

    for _, r in temp.iterrows():
        sid = str(r["ID"])
        name = r["Name"]
        percent = r["%"]

        color = "green" if percent >= 60 else "red"

        c1, c2, c3, c4 = st.columns([2, 4, 2, 2])

        with c1:
            if st.button(sid, key=f"id_{sid}_{col}"):
                current = df.loc[df["ID"] == sid, col].values[0]
                df.loc[df["ID"] == sid, col] = 0 if int(current or 0) == 1 else 1
                save_section(df, sec)
                st.rerun()

        with c2:
            st.write(name)

        with c3:
            st.markdown(
                f"<b style='color:{color}'>{percent}%</b>",
                unsafe_allow_html=True
            )

        with c4:
            val = int(df.loc[df["ID"] == sid, col].values[0] or 0)
            attendance[sid] = st.checkbox("", value=bool(val), key=f"chk_{sid}_{col}")

    if st.button("Save Attendance"):
        for sid, val in attendance.items():
            df.loc[df["ID"] == sid, col] = 1 if val else 0

        save_section(df, sec)
        st.success("Saved")
        st.session_state.page = "home"
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

    cols = [c for c in df.columns if c not in FIXED_COLS]

    if cols:
        df["Total"] = df[cols].sum(axis=1)
        df["%"] = (df["Total"] / len(cols) * 100).round(1)
    else:
        df["%"] = 0

    st.dataframe(df[["ID", "Name", "%"]])

# =========================
# MAIN
# =========================
def main_app():
    st.sidebar.title("Menu")

    menu = st.sidebar.radio("Go", ["Attendance", "Reports", "Sections"])

    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    if menu == "Attendance":
        attendance_page()
    elif menu == "Reports":
        report_page()
    else:
        sections_page()

# =========================
# ENTRY
# =========================
if "page" not in st.session_state:
    st.session_state.page = "login"

if st.session_state.page == "login":
    login_page()
else:
    main_app()
