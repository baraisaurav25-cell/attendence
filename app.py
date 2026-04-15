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
# AUTH SYSTEM
# =========================
def hash_pwd(p):
    return hashlib.sha256(p.encode()).hexdigest()

def load_users():
    if os.path.exists(USERS_FILE):
        return json.load(open(USERS_FILE))

    users = {
        "admin": {
            "password": hash_pwd("admin123"),
            "role": "admin",
            "sections": []
        }
    }

    json.dump(users, open(USERS_FILE, "w"), indent=2)
    return users

def save_users(users):
    json.dump(users, open(USERS_FILE, "w"), indent=2)

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

        for col in FIXED_COLS:
            if col not in df.columns:
                df[col] = ""

        return df

    return pd.DataFrame(columns=FIXED_COLS)

def save_section(df, sec):
    df.to_excel(section_file(sec), index=False)

# =========================
# LOGIN
# =========================
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
            st.error("Invalid credentials")

# =========================
# SECTION MANAGEMENT (FULL MOBILE SYSTEM)
# =========================
def sections_page():
    st.title("🗂️ Section Management")

    # CREATE SECTION
    st.subheader("➕ Create Section")

    sec = st.text_input("Section Name")

    if st.button("Create Section"):
        if sec.strip():
            df = pd.DataFrame(columns=FIXED_COLS)
            save_section(df, sec)
            st.success("Section created")
            st.rerun()

    st.divider()

    sections = list_sections()

    if not sections:
        st.info("No sections found")
        return

    sec_sel = st.selectbox("Select Section", sections)

    st.divider()

    # INPUT MODE
    st.subheader("📥 Add Students")

    mode = st.radio(
        "Input Method",
        [
            "📁 File Upload",
            "⌨️ Keyboard Paste",
            "✍️ Manual Entry"
        ]
    )

    old_df = load_section(sec_sel)

    # ---------------- FILE ----------------
    if mode == "📁 File Upload":
        file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])

        if file:
            if file.name.endswith(".csv"):
                new_df = pd.read_csv(file)
            else:
                new_df = pd.read_excel(file)

            if "ID" not in new_df.columns or "Name" not in new_df.columns:
                st.error("Need ID & Name columns")
                return

            new_df = new_df[["ID", "Name"]].dropna()

            merged = pd.concat([old_df, new_df], ignore_index=True)
            merged = merged.drop_duplicates(subset=["ID"])

            save_section(merged, sec_sel)

            st.success("Uploaded successfully!")
            st.rerun()

    # ---------------- PASTE ----------------
    elif mode == "⌨️ Keyboard Paste":

        st.code("2206001, Manna\n2206002, Asad")

        text = st.text_area("Paste Here")

        if st.button("Add Students"):
            try:
                rows = []

                for line in text.strip().split("\n"):
                    if "," in line:
                        sid, name = line.split(",", 1)
                        rows.append({"ID": sid.strip(), "Name": name.strip()})

                new_df = pd.DataFrame(rows)

                merged = pd.concat([old_df, new_df], ignore_index=True)
                merged = merged.drop_duplicates(subset=["ID"])

                save_section(merged, sec_sel)

                st.success("Students added!")
                st.rerun()

            except:
                st.error("Invalid format")

    # ---------------- MANUAL ----------------
    else:
        with st.form("single"):
            sid = st.text_input("Student ID")
            name = st.text_input("Student Name")

            if st.form_submit_button("Add"):
                new_df = pd.DataFrame([{"ID": sid, "Name": name}])

                merged = pd.concat([old_df, new_df], ignore_index=True)
                merged = merged.drop_duplicates(subset=["ID"])

                save_section(merged, sec_sel)

                st.success("Added!")
                st.rerun()

    st.divider()

    st.subheader("📄 Students List")

    st.dataframe(old_df, use_container_width=True)

# =========================
# ATTENDANCE SYSTEM
# =========================
def attendance_page():
    st.title("📋 Attendance")

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
        st.warning("No students")
        return

    date = st.date_input("Date")
    session = st.selectbox("Session", ["AM", "PM"])

    col = date.strftime("%Y-%m-%d") + "_" + session

    today = datetime.now().date()
    locked = (date != today) and (st.session_state.role != "admin")

    if col not in df.columns:
        df[col] = 0

    st.write(f"### {sec} → {col}")

    attendance = {}

    for _, r in df.iterrows():
        sid = r["ID"]
        name = r["Name"]

        val = int(pd.to_numeric(r.get(col, 0), errors="coerce") or 0)

        attendance[sid] = st.checkbox(
            f"{sid} - {name}",
            value=(val == 1),
            key=f"{sid}_{col}",
            disabled=locked
        )

    if locked:
        st.warning("🔒 Past attendance locked")

    if st.button("Save Attendance"):
        for sid, present in attendance.items():
            df.loc[df["ID"] == sid, col] = 1 if present else 0

        save_section(df, sec)
        st.success("Saved!")
        st.rerun()

# =========================
# REPORT SYSTEM
# =========================
def report_page():
    st.title("📊 Reports")

    sections = list_sections()

    if not sections:
        st.warning("No data")
        return

    sec = st.selectbox("Section", sections)
    df = load_section(sec)

    if df.empty:
        st.warning("No students")
        return

    date_cols = [c for c in df.columns if c not in FIXED_COLS]

    if date_cols:
        df["Total Present"] = df[date_cols].sum(axis=1)
        df["Total Class"] = len(date_cols)
        df["Attendance %"] = (df["Total Present"] / df["Total Class"] * 100).round(1)
    else:
        df["Attendance %"] = 0

    st.dataframe(df[["ID", "Name", "Attendance %"]])

    st.subheader("🏆 Top")
    st.dataframe(df.sort_values("Attendance %", ascending=False).head(5))

    st.subheader("⚠️ Low (<60%)")
    st.dataframe(df[df["Attendance %"] < 60])

# =========================
# MAIN APP
# =========================
if "user" not in st.session_state:
    login()
else:
    st.sidebar.title("Menu")

    menu = st.sidebar.radio(
        "Go to",
        ["Attendance", "Reports", "Sections"]
    )

    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    if menu == "Attendance":
        attendance_page()
    elif menu == "Reports":
        report_page()
    else:
        sections_page()
