import streamlit as st
import pandas as pd
import os
import json
import hashlib

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
# USERS
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
    return os.path.join(DATA_DIR, f"{name}.xlsx")

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
    return [f.replace(".xlsx", "") for f in os.listdir(DATA_DIR) if f.endswith(".xlsx")]

# =========================
# LOGIN
# =========================
def login():
    st.title("🧬 Attendance System")

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
# LOGOUT
# =========================
def logout():
    st.session_state.clear()
    st.rerun()

# =========================
# STUDENT MODULE (FIXED)
# =========================
def student_page(sec):
    st.title(f"👨‍🎓 Students → {sec}")

    df = load_section(sec)

    mode = st.radio("Add Students", ["Manual", "Paste"])

    if mode == "Manual":
        with st.form("m"):
            sid = st.text_input("ID")
            name = st.text_input("Name")

            if st.form_submit_button("Add"):
                if sid and name:
                    if sid not in df["ID"].astype(str).values:
                        df = pd.concat([df, pd.DataFrame([{"ID": sid, "Name": name}])])
                        save_section(df, sec)
                        st.success("Added")
                        st.rerun()
                    else:
                        st.warning("ID exists")

    else:
        txt = st.text_area("Paste (ID, Name)")

        if st.button("Add"):
            rows = []
            for line in txt.split("\n"):
                if "," in line:
                    i, n = line.split(",", 1)
                    rows.append({"ID": i.strip(), "Name": n.strip()})

            if rows:
                new = pd.DataFrame(rows)
                existing = set(df["ID"].astype(str))
                new = new[~new["ID"].astype(str).isin(existing)]

                df = pd.concat([df, new], ignore_index=True)
                save_section(df, sec)
                st.success("Added")
                st.rerun()

    st.dataframe(df)

# =========================
# ATTENDANCE (FIXED CLICK NAME)
# =========================
def attendance_page(sec):
    st.title(f"📋 Attendance → {sec}")

    df = load_section(sec)

    if df.empty:
        st.warning("No students found")
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

    st.subheader("Click STUDENT NAME")

    for _, r in temp.iterrows():
        sid = str(r["ID"])
        name = r["Name"]
        percent = r["%"]

        color = "green" if percent >= 60 else "red"

        c1, c2, c3 = st.columns([4, 3, 2])

        with c1:
            if st.button(name, key=sid):
                cur = df.loc[df["ID"] == sid, col].values[0]
                df.loc[df["ID"] == sid, col] = 0 if int(cur or 0) == 1 else 1
                save_section(df, sec)
                st.rerun()

        with c2:
            st.write(sid)

        with c3:
            st.markdown(f"<b style='color:{color}'>{percent}%</b>", unsafe_allow_html=True)

        attendance[sid] = st.checkbox("", value=bool(df.loc[df["ID"] == sid, col].values[0] or 0), key=f"{sid}_{col}")

    if st.button("💾 Save Attendance"):
        for sid, v in attendance.items():
            df.loc[df["ID"] == sid, col] = 1 if v else 0

        save_section(df, sec)
        st.session_state.page = "dashboard"
        st.rerun()

# =========================
# REPORT
# =========================
def report_page(sec):
    st.title(f"📊 Report → {sec}")

    df = load_section(sec)

    cols = [c for c in df.columns if c not in FIXED_COLS]

    if cols:
        df["Total"] = df[cols].sum(axis=1)
        df["%"] = (df["Total"] / len(cols) * 100).round(1)
    else:
        df["%"] = 0

    st.dataframe(df)

    st.download_button(
        "⬇ Download Excel",
        df.to_csv(index=False).encode(),
        file_name=f"{sec}_report.csv"
    )

# =========================
# DASHBOARD (FIXED FLOW)
# =========================
def dashboard():
    st.title(f"🏠 Dashboard - {st.session_state.user}")

    users = load_users()
    user = st.session_state.user

    if st.session_state.role == "admin":
        sections = list_sections()
    else:
        sections = users[user].get("sections", [])

    st.sidebar.button("🚪 Logout", on_click=logout)

    st.subheader("Sections")

    new_sec = st.text_input("Create Section (User Allowed)")

    if st.button("Create"):
        if new_sec:
            df = pd.DataFrame(columns=FIXED_COLS)
            save_section(df, new_sec)
            st.success("Created")
            st.rerun()

    st.divider()

    for sec in sections:
        c1, c2, c3 = st.columns([4, 2, 2])

        with c1:
            st.write(sec)

        with c2:
            if st.button("Attendance", key=f"a_{sec}"):
                st.session_state.current_section = sec
                st.session_state.page = "attendance"
                st.rerun()

        with c3:
            if st.button("Report", key=f"r_{sec}"):
                st.session_state.current_section = sec
                st.session_state.page = "report"
                st.rerun()

# =========================
# ROUTER
# =========================
def main():
    if "page" not in st.session_state:
        st.session_state.page = "login"

    if st.session_state.page == "login":
        login()

    elif st.session_state.page == "dashboard":
        dashboard()

    elif st.session_state.page == "attendance":
        attendance_page(st.session_state.current_section)

    elif st.session_state.page == "report":
        report_page(st.session_state.current_section)

main()
