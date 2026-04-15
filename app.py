import streamlit as st
import pandas as pd
import os
import json
import hashlib
import io
from datetime import datetime

# =========================
# CONFIGURATION
# =========================
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

USERS_FILE = os.path.join(DATA_DIR, "users.json")
FIXED_COLS = ["ID", "Name"]


# =========================
# UTILITIES
# =========================
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def load_json(path: str, default=None):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return default


def save_json(path: str, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# =========================
# USER MANAGEMENT
# =========================
def load_users():
    users = load_json(USERS_FILE)
    if users is None:
        users = {
            "admin": {
                "password": hash_password("admin123"),
                "role": "admin",
            }
        }
        save_json(USERS_FILE, users)
    return users


def save_users(users):
    save_json(USERS_FILE, users)


def register_user(username: str, password: str) -> bool:
    users = load_users()
    if username in users:
        return False
    users[username] = {
        "password": hash_password(password),
        "role": "teacher",
    }
    save_users(users)
    return True


def reset_password(username: str, new_password: str) -> bool:
    users = load_users()
    if username not in users:
        return False
    users[username]["password"] = hash_password(new_password)
    save_users(users)
    return True


def delete_user(username: str) -> bool:
    if username == "admin":
        return False
    users = load_users()
    if username not in users:
        return False
    # Delete all section files for this user
    prefix = f"{username}__"
    for f in os.listdir(DATA_DIR):
        if f.startswith(prefix) and f.endswith(".xlsx"):
            os.remove(os.path.join(DATA_DIR, f))
    del users[username]
    save_users(users)
    return True


# =========================
# SECTION DATA (per user)
# =========================
def section_path(user: str, section: str) -> str:
    safe_user = user.replace(" ", "_")
    safe_sec = section.replace(" ", "_")
    return os.path.join(DATA_DIR, f"{safe_user}__{safe_sec}.xlsx")


def load_section(user: str, section: str) -> pd.DataFrame:
    path = section_path(user, section)
    if os.path.exists(path):
        df = pd.read_excel(path, dtype={"ID": str})
    else:
        df = pd.DataFrame(columns=FIXED_COLS)

    for col in FIXED_COLS:
        if col not in df.columns:
            df[col] = ""
    return df


def save_section(user: str, section: str, df: pd.DataFrame):
    df.to_excel(section_path(user, section), index=False)


def list_sections(user: str) -> list:
    prefix = f"{user}__"
    sections = []
    for f in os.listdir(DATA_DIR):
        if f.startswith(prefix) and f.endswith(".xlsx"):
            sections.append(f.replace(prefix, "").replace(".xlsx", ""))
    return sections


# =========================
# STUDENT MANAGEMENT (generic, used by both teacher and admin)
# =========================
def manage_students(user: str, section: str, editable: bool = True):
    """Display and optionally edit students in a section."""
    st.subheader(f"👨‍🎓 Students in {section} (User: {user})")
    df = load_section(user, section)

    if editable:
        with st.expander("Add New Student"):
            mode = st.radio("Input Method", ["Manual", "Bulk Paste"], key=f"mode_{user}_{section}")
            if mode == "Manual":
                sid = st.text_input("Student ID", key=f"sid_{user}_{section}")
                name = st.text_input("Student Name", key=f"name_{user}_{section}")
                if st.button("Add Student", key=f"add_{user}_{section}"):
                    if sid and name:
                        if sid not in df["ID"].astype(str).values:
                            new_row = pd.DataFrame([{"ID": sid, "Name": name}])
                            df = pd.concat([df, new_row], ignore_index=True)
                            save_section(user, section, df)
                            st.success(f"Added {name}")
                            st.rerun()
                        else:
                            st.error("ID already exists")
                    else:
                        st.error("Both ID and Name required")
            else:
                bulk_text = st.text_area("Enter ID,Name per line", key=f"bulk_{user}_{section}")
                if st.button("Add Bulk", key=f"bulk_btn_{user}_{section}"):
                    new_rows = []
                    duplicates = []
                    for line in bulk_text.strip().split("\n"):
                        if "," in line:
                            sid, name = line.split(",", 1)
                            sid, name = sid.strip(), name.strip()
                            if sid and name:
                                if sid not in df["ID"].astype(str).values and sid not in [r["ID"] for r in new_rows]:
                                    new_rows.append({"ID": sid, "Name": name})
                                else:
                                    duplicates.append(sid)
                    if new_rows:
                        new_df = pd.DataFrame(new_rows)
                        df = pd.concat([df, new_df], ignore_index=True)
                        save_section(user, section, df)
                        st.success(f"Added {len(new_rows)} students")
                        if duplicates:
                            st.warning(f"Skipped duplicate IDs: {', '.join(duplicates)}")
                        st.rerun()
                    else:
                        st.error("No valid rows")

    # Display and edit existing students
    if not df.empty:
        st.write("**Current Students**")
        edited_df = st.data_editor(
            df[FIXED_COLS],
            use_container_width=True,
            key=f"editor_{user}_{section}",
            disabled=not editable
        )
        if editable and st.button("Save Student Changes", key=f"save_students_{user}_{section}"):
            save_section(user, section, edited_df)
            st.success("Student list updated")
            st.rerun()
    else:
        st.info("No students yet.")


# =========================
# ATTENDANCE PAGE (teacher view)
# =========================
def attendance_page(section: str):
    st.title(f"📋 Take Attendance – {section}")
    user = st.session_state.user
    df = load_section(user, section)

    if df.empty:
        st.warning("No students in this section. Please add students first.")
        if st.button("← Back to Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()
        return

    date = st.date_input("Date")
    session_type = st.selectbox("Session", ["AM", "PM"])
    col_name = f"{date}_{session_type}"

    if col_name not in df.columns:
        df[col_name] = 0

    att_cols = [c for c in df.columns if c not in FIXED_COLS]

    st.subheader("Mark Attendance")
    st.caption("Click on a student's button to toggle Present/Absent")

    for idx, row in df.iterrows():
        sid = row["ID"]
        name = row["Name"]
        present = bool(row.get(col_name, 0))

        if att_cols:
            total_present = df.loc[df["ID"] == sid, att_cols].sum(axis=1).values[0]
            percent = (total_present / len(att_cols)) * 100
        else:
            percent = 0.0

        col1, col2, col3 = st.columns([3, 1, 2])
        with col1:
            button_label = f"✅ {sid} - {name}" if present else f"❌ {sid} - {name}"
            if st.button(button_label, key=f"{sid}_{col_name}_{section}"):
                df.loc[df["ID"] == sid, col_name] = 0 if present else 1
                save_section(user, section, df)
                st.rerun()
        with col2:
            st.write(f"ID: {sid}")
        with col3:
            color = "green" if percent >= 60 else "red"
            st.markdown(f"<span style='color:{color}'>{percent:.1f}%</span>", unsafe_allow_html=True)

    col_save, col_back = st.columns(2)
    with col_save:
        if st.button("💾 Save All Changes", key=f"save_{section}"):
            save_section(user, section, df)
            st.success("Attendance saved! Returning to dashboard...")
            st.session_state.page = "dashboard"
            st.rerun()
    with col_back:
        if st.button("← Back to Dashboard", key=f"back_{section}"):
            st.session_state.page = "dashboard"
            st.rerun()


# =========================
# REPORT PAGE (teacher view)
# =========================
def report_page(section: str):
    st.title(f"📊 Attendance Report – {section}")
    user = st.session_state.user
    df = load_section(user, section)

    if df.empty:
        st.warning("No data available.")
        if st.button("← Back to Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()
        return

    att_cols = [c for c in df.columns if c not in FIXED_COLS]
    if att_cols:
        df["Total Present"] = df[att_cols].sum(axis=1)
        df["Attendance %"] = (df["Total Present"] / len(att_cols) * 100).round(1)
    else:
        df["Total Present"] = 0
        df["Attendance %"] = 0.0

    report_df = df[["ID", "Name", "Attendance %"]]
    st.dataframe(report_df, use_container_width=True)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        report_df.to_excel(writer, index=False, sheet_name="Report")
    excel_data = output.getvalue()

    st.download_button(
        label="📥 Download Report (Excel)",
        data=excel_data,
        file_name=f"{section}_attendance_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    if st.button("← Back to Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()


# =========================
# ADMIN PANEL
# =========================
def admin_panel():
    st.title("🔧 Admin Panel - User & Data Management")
    users = load_users()
    teacher_list = [u for u in users if u != "admin"]

    # User management section
    st.subheader("👥 Manage Teacher Accounts")
    col1, col2 = st.columns(2)
    with col1:
        with st.expander("Reset Password"):
            user_to_reset = st.selectbox("Select User", teacher_list, key="reset_user")
            new_pwd = st.text_input("New Password", type="password", key="new_pwd")
            if st.button("Reset Password"):
                if reset_password(user_to_reset, new_pwd):
                    st.success(f"Password for {user_to_reset} reset.")
                else:
                    st.error("Failed")
    with col2:
        with st.expander("Delete User"):
            user_to_delete = st.selectbox("Select User to Delete", teacher_list, key="del_user")
            if st.button("Delete User"):
                if delete_user(user_to_delete):
                    st.success(f"User {user_to_delete} deleted.")
                    st.rerun()
                else:
                    st.error("Cannot delete admin or user not found")

    st.subheader("📂 View & Edit Any User's Sections")
    selected_user = st.selectbox("Select a teacher", teacher_list, key="admin_user_select")
    if selected_user:
        sections = list_sections(selected_user)
        if not sections:
            st.info(f"No sections for {selected_user}")
        else:
            for sec in sections:
                with st.expander(f"📘 {sec} (User: {selected_user})"):
                    tab1, tab2 = st.tabs(["Students", "Attendance Report"])
                    with tab1:
                        manage_students(selected_user, sec, editable=True)
                    with tab2:
                        # Show attendance report for this section
                        df = load_section(selected_user, sec)
                        if not df.empty:
                            att_cols = [c for c in df.columns if c not in FIXED_COLS]
                            if att_cols:
                                df["Total Present"] = df[att_cols].sum(axis=1)
                                df["Attendance %"] = (df["Total Present"] / len(att_cols) * 100).round(1)
                            else:
                                df["Attendance %"] = 0.0
                            st.dataframe(df[["ID", "Name", "Attendance %"]])
                            # Download report
                            output = io.BytesIO()
                            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                                df[["ID", "Name", "Attendance %"]].to_excel(writer, index=False, sheet_name="Report")
                            st.download_button(
                                label=f"Download Report for {sec}",
                                data=output.getvalue(),
                                file_name=f"{selected_user}_{sec}_report.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"admin_dl_{selected_user}_{sec}"
                            )
                        else:
                            st.info("No students in this section")


# =========================
# TEACHER DASHBOARD
# =========================
def teacher_dashboard():
    st.sidebar.title(f"👤 {st.session_state.user}")
    if st.sidebar.button("🚪 Logout"):
        logout()

    # Create section
    st.subheader("➕ Create Section")
    sec_name = st.text_input("Section Name", key="new_sec_name")
    if st.button("Create Section", key="create_sec_btn") and sec_name.strip():
        user = st.session_state.user
        if sec_name in list_sections(user):
            st.error("Section already exists")
        else:
            save_section(user, sec_name, pd.DataFrame(columns=FIXED_COLS))
            st.success(f"Section '{sec_name}' created")
            st.rerun()

    sections = list_sections(st.session_state.user)
    if not sections:
        st.info("No sections yet. Create one above.")
        return

    for sec in sections:
        with st.expander(f"📘 {sec}", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📋 Take Attendance", key=f"att_{sec}"):
                    st.session_state.page = "attendance"
                    st.session_state.section = sec
                    st.rerun()
            with col2:
                if st.button("📊 View Report", key=f"rep_{sec}"):
                    st.session_state.page = "report"
                    st.session_state.section = sec
                    st.rerun()
            manage_students(st.session_state.user, sec, editable=True)


# =========================
# AUTHENTICATION
# =========================
def login():
    st.title("📘 Smart Attendance System")

    users = load_users()
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            if username in users and users[username]["password"] == hash_password(password):
                st.session_state.user = username
                st.session_state.role = users[username]["role"]
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        new_user = st.text_input("Username", key="reg_user")
        new_pass = st.text_input("Password", type="password", key="reg_pass")
        confirm_pass = st.text_input("Confirm Password", type="password")
        if st.button("Register"):
            if not new_user or not new_pass:
                st.error("Username and password required")
            elif new_pass != confirm_pass:
                st.error("Passwords do not match")
            elif register_user(new_user, new_pass):
                st.success("Account created! Please login.")
            else:
                st.error("Username already exists")


def logout():
    st.session_state.clear()
    st.rerun()


# =========================
# MAIN ROUTER
# =========================
def main():
    if "user" not in st.session_state:
        login()
        return

    if st.session_state.role == "admin":
        admin_panel()
        if st.sidebar.button("Logout"):
            logout()
    else:
        if "page" not in st.session_state:
            st.session_state.page = "dashboard"

        if st.session_state.page == "dashboard":
            teacher_dashboard()
        elif st.session_state.page == "attendance":
            attendance_page(st.session_state.section)
        elif st.session_state.page == "report":
            report_page(st.session_state.section)


if __name__ == "__main__":
    main()
