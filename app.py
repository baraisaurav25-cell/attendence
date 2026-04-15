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
# USERS SYSTEM
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
# SECTION SYSTEM (USER ISOLATED)
# =========================
def section_path(user, section):
    safe_user = user.replace(" ", "_")
    safe_sec = section.replace(" ", "_")
    return os.path.join(DATA_DIR, f"{safe_user}__{safe_sec}.xlsx")


def load_section(user, section):
    path = section_path(user, section)

    if os.path.exists(path):
        df = pd.read_excel(path, dtype={"ID": str})
    else:
        df = pd.DataFrame(columns=FIXED_COLS)

    for c in FIXED_COLS:
        if c not in df.columns:
            df[c] = ""

    return df


def save_section(user, section, df):
    df.to_excel(section_path(user, section), index=False)


def list_sections(user):
    prefix = f"{user}__"
    sections = []

    for f in os.listdir(DATA_DIR):
        if f.startswith(prefix) and f.endswith(".xlsx"):
            sections.append(f.replace(prefix, "").replace(".xlsx", ""))

    return sections


# =========================
# AUTH
# =========================
def login():
    st.title("📘 Smart Attendance System")

    users = load_users()

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in users and users[u]["password"] == hash_pwd(p):
            st.session_state.user = u
            st.session_state.role = users[u]["role"]
            st.rerun()
        else:
            st.error("Invalid credentials")


def logout():
    st.session_state.clear()
    st.rerun()


# =========================
# SECTION CREATE
# =========================
def create_section():
    st.subheader("➕ Create Section")

    sec = st.text_input("Section Name")

    if st.button("Create"):
        if sec.strip():
            user = st.session_state.user
            df = pd.DataFrame(columns=FIXED_COLS)
            save_section(user, sec, df)
            st.success("Section created")
            st.rerun()


# =========================
# STUDENTS
# =========================
def student_module(section):
    st.subheader("👨‍🎓 Students")

    user = st.session_state.user
    df = load_section(user, section)

    mode = st.radio("Add Students", ["Manual", "Bulk Paste"])

    if mode == "Manual":
        sid = st.text_input("ID")
        name = st.text_input("Name")

        if st.button("Add Student"):
            if sid and name:
                if sid not in df["ID"].astype(str).values:
                    df = pd.concat([df, pd.DataFrame([{"ID": sid, "Name": name}])])
                    save_section(user, section, df)
                    st.success("Added")
                    st.rerun()

    else:
        txt = st.text_area("ID, Name per line")

        if st.button("Add Bulk"):
            rows = []
            for line in txt.split("\n"):
                if "," in line:
                    i, n = line.split(",", 1)
                    rows.append({"ID": i.strip(), "Name": n.strip()})

            new_df = pd.DataFrame(rows)
            df = pd.concat([df, new_df]).drop_duplicates(subset=["ID"])

            save_section(user, section, df)
            st.success("Added")
            st.rerun()

    st.dataframe(df)


# =========================
# ATTENDANCE
# =========================
def attendance_page(section):
    st.title(f"📋 Attendance - {section}")

    user = st.session_state.user
    df = load_section(user, section)

    if df.empty:
        st.warning("No students")
        return

    date = st.date_input("Date")
    session = st.selectbox("Session", ["AM", "PM"])

    col = f"{date}_{session}"

    if col not in df.columns:
        df[col] = 0

    # correct percentage (based on actual sessions)
    session_cols = [c for c in df.columns if c not in FIXED_COLS]

    for i, row in df.iterrows():
        sid = row["ID"]
        name = row["Name"]

        present = bool(row.get(col, 0))

        c1, c2, c3 = st.columns([4, 2, 2])

        with c1:
            if st.button(f"{sid} - {name}", key=f"{sid}_{col}"):
                df.loc[df["ID"] == sid, col] = 0 if present else 1
                save_section(user, section, df)
                st.rerun()

        with c2:
            st.write(sid)

        with c3:
            percent = (df.loc[df["ID"] == sid, session_cols].sum(axis=1).values[0] /
                       len(session_cols) * 100) if session_cols else 0

            color = "green" if percent >= 60 else "red"
            st.markdown(f"<span style='color:{color}'>{percent:.1f}%</span>", unsafe_allow_html=True)

    if st.button("Save"):
        save_section(user, section, df)
        st.success("Saved")
        st.rerun()


# =========================
# REPORT
# =========================
def report_page(section):
    st.title(f"📊 Report - {section}")

    user = st.session_state.user
    df = load_section(user, section)

    if df.empty:
        st.warning("No data")
        return

    session_cols = [c for c in df.columns if c not in FIXED_COLS]

    if session_cols:
        df["Total"] = df[session_cols].sum(axis=1)
        df["Percent"] = (df["Total"] / len(session_cols) * 100).round(1)
    else:
        df["Percent"] = 0

    st.dataframe(df[["ID", "Name", "Percent"]])

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download Excel",
        csv,
        file_name=f"{section}_report.csv"
    )


# =========================
# DASHBOARD
# =========================
def dashboard():
    st.sidebar.title(f"User: {st.session_state.user}")
    st.sidebar.button("Logout", on_click=logout)

    user = st.session_state.user

    create_section()

    st.divider()

    sections = list_sections(user)

    if not sections:
        st.info("No sections yet")
        return

    for sec in sections:
        st.write(f"📘 {sec}")

        if st.button(f"Attendance - {sec}", key=f"a_{sec}"):
            st.session_state.page = "attendance"
            st.session_state.section = sec
            st.rerun()

        if st.button(f"Report - {sec}", key=f"r_{sec}"):
            st.session_state.page = "report"
            st.session_state.section = sec
            st.rerun()

        student_module(sec)


# =========================
# ROUTER
# =========================
def main():
    if "user" not in st.session_state:
        login()
        return

    if "page" not in st.session_state:
        st.session_state.page = "dashboard"

    if st.session_state.page == "dashboard":
        dashboard()

    elif st.session_state.page == "attendance":
        attendance_page(st.session_state.section)

    elif st.session_state.page == "report":
        report_page(st.session_state.section)


main()
