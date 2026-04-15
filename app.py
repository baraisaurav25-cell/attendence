import streamlit as st
import pandas as pd
import os
import json
import hashlib
from datetime import datetime

# ---------------------------------
# CONFIG
# ---------------------------------
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

USERS_FILE = os.path.join(DATA_DIR, "users.json")

# ---------------------------------
# AUTH
# ---------------------------------
def hash_pwd(p):
    return hashlib.sha256(p.encode()).hexdigest()

def load_users():
    if os.path.exists(USERS_FILE):
        return json.load(open(USERS_FILE))
    users = {"admin": {"password": hash_pwd("admin123"), "role": "admin"}}
    json.dump(users, open(USERS_FILE, "w"))
    return users

# ---------------------------------
# FILE HELPERS
# ---------------------------------
def section_file(sec):
    return os.path.join(DATA_DIR, f"{sec}.xlsx")

def load_data(sec):
    path = section_file(sec)
    if os.path.exists(path):
        return pd.read_excel(path, dtype=str)
    return pd.DataFrame(columns=["ID", "Name", "Date", "Session", "Present"])

def save_data(df, sec):
    df.to_excel(section_file(sec), index=False)

# ---------------------------------
# LOGIN
# ---------------------------------
def login():
    st.title("🔐 Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        users = load_users()
        if u in users and users[u]["password"] == hash_pwd(p):
            st.session_state.user = u
            st.session_state.role = users[u]["role"]
            st.rerun()
        else:
            st.error("Wrong login")

# ---------------------------------
# ATTENDANCE
# ---------------------------------
def attendance():
    st.title("📋 Attendance")

    sec = st.text_input("Section Name")

    if not sec:
        return

    df = load_data(sec)

    date = st.date_input("Date")
    session = st.selectbox("Session", ["AM", "PM"])

    today = datetime.today().date()

    # FILTER
    day_df = df[(df["Date"] == str(date)) & (df["Session"] == session)]

    st.write("### Students")

    students = df[["ID", "Name"]].drop_duplicates()

    attendance_map = {}

    for _, row in students.iterrows():
        sid = row["ID"]

        existing = day_df[day_df["ID"] == sid]

        default = False
        if not existing.empty:
            default = existing.iloc[0]["Present"] == "1"

        # LOCK LOGIC
        locked = (date != today) and (st.session_state.role != "admin")

        attendance_map[sid] = st.checkbox(
            f"{row['Name']} ({sid})",
            value=default,
            disabled=locked
        )

    if st.button("Save Attendance"):
        # REMOVE OLD ENTRY FOR THIS DATE
        df = df[~((df["Date"] == str(date)) & (df["Session"] == session))]

        new_rows = []
        for _, row in students.iterrows():
            sid = row["ID"]
            new_rows.append({
                "ID": sid,
                "Name": row["Name"],
                "Date": str(date),
                "Session": session,
                "Present": "1" if attendance_map[sid] else "0"
            })

        df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)

        save_data(df, sec)

        st.success("Saved!")

# ---------------------------------
# REPORT
# ---------------------------------
def report():
    st.title("📊 Report")

    sec = st.text_input("Section")

    if not sec:
        return

    df = load_data(sec)

    if df.empty:
        st.info("No data")
        return

    # CALCULATE
    total = df.groupby("ID")["Present"].count()
    present = df[df["Present"] == "1"].groupby("ID")["Present"].count()

    result = pd.DataFrame({
        "Total Class": total,
        "Present": present
    }).fillna(0)

    result["Attendance %"] = (result["Present"] / result["Total Class"] * 100).round(1)

    st.dataframe(result)

# ---------------------------------
# MAIN
# ---------------------------------
if "user" not in st.session_state:
    login()
else:
    menu = st.sidebar.radio("Menu", ["Attendance", "Report"])

    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    if menu == "Attendance":
        attendance()
    else:
        report()
