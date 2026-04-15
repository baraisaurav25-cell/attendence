import streamlit as st
import pandas as pd
import os
import json
import hashlib
from datetime import datetime
import matplotlib.pyplot as plt

# ---------------------------------
# CONFIG
# ---------------------------------
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

USERS_FILE = os.path.join(DATA_DIR, "users.json")

FIXED_COLS = ["ID", "Name", "Total Present", "Total Absent", "Total Class", "Attendance %"]

# ---------------------------------
# AUTH
# ---------------------------------
def hash_pwd(p):
    return hashlib.sha256(p.encode()).hexdigest()

def load_users():
    if os.path.exists(USERS_FILE):
        return json.load(open(USERS_FILE))
    users = {"admin": {"password": hash_pwd("admin123"), "role": "admin", "sections": []}}
    json.dump(users, open(USERS_FILE, "w"))
    return users

def save_users(users):
    json.dump(users, open(USERS_FILE, "w"), indent=2)

# ---------------------------------
# FILE HELPERS
# ---------------------------------
def section_file(sec):
    safe = sec.replace(" ", "_")
    return os.path.join(DATA_DIR, f"{safe}.xlsx")

def list_all_sections():
    return [f[:-5].replace("_", " ") for f in os.listdir(DATA_DIR) if f.endswith(".xlsx")]

def load_section(section):
    path = section_file(section)

    if os.path.exists(path):
        df = pd.read_excel(path, dtype={"ID": str})

        for col in FIXED_COLS:
            if col not in df.columns:
                df[col] = 0

        # FIX dtype
        num_cols = ["Total Present", "Total Absent", "Total Class", "Attendance %"]
        for col in num_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        # date columns
        date_cols = [c for c in df.columns if c not in FIXED_COLS]
        for col in date_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        return df

    return pd.DataFrame(columns=FIXED_COLS)

def recalculate(df):
    date_cols = [c for c in df.columns if c not in FIXED_COLS]

    if not date_cols:
        df["Total Present"] = 0
        df["Total Absent"] = 0
        df["Total Class"] = 0
        df["Attendance %"] = 0.0
        return df

    vals = df[date_cols].apply(pd.to_numeric, errors="coerce").fillna(0)

    df["Total Present"] = vals.sum(axis=1)
    df["Total Class"] = len(date_cols)
    df["Total Absent"] = df["Total Class"] - df["Total Present"]
    df["Attendance %"] = (df["Total Present"] / df["Total Class"] * 100).round(1)

    return df

def save_section(df, section):
    df = recalculate(df)

    df["Total Present"] = df["Total Present"].astype(int)
    df["Total Absent"] = df["Total Absent"].astype(int)
    df["Total Class"] = df["Total Class"].astype(int)
    df["Attendance %"] = df["Attendance %"].astype(float)

    df.to_excel(section_file(section), index=False)

# ---------------------------------
# LOGIN
# ---------------------------------
def login():
    st.title("🧬 BioTrack Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        users = load_users()
        if u in users and users[u]["password"] == hash_pwd(p):
            st.session_state.user = u
            st.session_state.role = users[u]["role"]
            st.rerun()
        else:
            st.error("Wrong credentials")

# ---------------------------------
# ATTENDANCE PAGE
# ---------------------------------
def attendance_page():
    st.title("📋 Attendance Entry")

    users = load_users()
    current_user = st.session_state.user

    if st.session_state.role == "admin":
        sections = list_all_sections()
    else:
        sections = users[current_user].get("sections", [])

    if not sections:
        st.warning("No sections assigned")
        return

    section = st.selectbox("Section", sections)
    df = load_section(section)

    if df.empty:
        st.warning("No students found")
        return

    date = st.date_input("Date")
    session = st.selectbox("Session", ["AM", "PM", "Extra"])

    date_key = date.strftime("%Y-%m-%d") + "_" + session

    today = datetime.now().date()
    is_locked = (date != today) and (st.session_state.role != "admin")

    if date_key not in df.columns:
        df[date_key] = 0

    attendance_map = {}

    st.write(f"### Entry: {section} → {date_key}")

    for _, row in df.iterrows():
        sid = row["ID"]
        name = row["Name"]

        val = int(pd.to_numeric(row.get(date_key, 0), errors="coerce") or 0)

        attendance_map[sid] = st.checkbox(
            f"{sid} {name}",
            value=(val == 1),
            key=f"cb_{sid}_{date_key}",
            disabled=is_locked
        )

    if is_locked:
        st.warning("🔒 Past attendance locked (admin only)")

    if st.button("💾 Save Attendance"):
        for sid, present in attendance_map.items():
            df.loc[df["ID"] == sid, date_key] = 1 if present else 0

        save_section(df, section)

        st.success("Saved successfully!")
        st.rerun()

# ---------------------------------
# REPORT PAGE
# ---------------------------------
def report_page():
    st.title("📊 Reports")

    sections = list_all_sections()
    if not sections:
        st.warning("No data")
        return

    section = st.selectbox("Section", sections)
    df = load_section(section)

    if df.empty:
        st.warning("No data")
        return

    df = recalculate(df)

    st.dataframe(df[["ID", "Name", "Attendance %"]], use_container_width=True)

    # Chart
    st.subheader("📊 Attendance Distribution")

    fig, ax = plt.subplots()
    ax.hist(df["Attendance %"], bins=10)
    ax.set_xlabel("Attendance %")
    ax.set_ylabel("Students")

    st.pyplot(fig)

    # Top performers
    st.subheader("🏆 Top Performers")
    top = df.sort_values("Attendance %", ascending=False).head(5)
    st.dataframe(top[["ID", "Name", "Attendance %"]])

    # Low performers
    st.subheader("⚠️ Low Attendance")
    low = df[df["Attendance %"] < 60]
    st.dataframe(low[["ID", "Name", "Attendance %"]])

# ---------------------------------
# MAIN
# ---------------------------------
if "user" not in st.session_state:
    login()
else:
    st.sidebar.title("Menu")

    menu = st.sidebar.radio("Go to", ["Attendance", "Reports"])

    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    if menu == "Attendance":
        attendance_page()
    else:
        report_page()
