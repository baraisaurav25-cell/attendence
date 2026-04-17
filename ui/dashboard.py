"""
ui/dashboard.py
---------------
Two top-level pages:
  • teacher_dashboard() — section management + student management
  • admin_panel()       — user management + cross-teacher data view
Both pages include the shared student_manager() widget.
"""

import streamlit as st
import pandas as pd

from attendance import build_report, to_excel_bytes
from auth import load_users, register_user, reset_password, delete_user
from config import FIXED_COLS
from database import (
    create_section, delete_section, list_sections,
    load_section, save_section,
)


# ════════════════════════════════════════════════════════════════════════════════
#  SHARED WIDGET: Student Manager
# ════════════════════════════════════════════════════════════════════════════════

def student_manager(user: str, section: str, editable: bool = True) -> None:
    """
    Reusable widget to add / edit / remove students in a section.
    Set *editable=False* for read-only display.
    """
    df = load_section(user, section)
    kp = f"{user}__{section}"          # unique key prefix

    if editable:
        _render_add_student_controls(df, user, section, kp)
        df = load_section(user, section)   # reload after possible write

    _render_student_list(df, user, section, kp, editable)


def _render_add_student_controls(df, user: str, section: str, kp: str) -> None:
    """Manual entry or bulk-paste controls for adding students."""
    mode = st.radio(
        "Add Method", ["Manual Entry", "Bulk Paste (CSV)"],
        horizontal=True, key=f"mode_{kp}"
    )

    if mode == "Manual Entry":
        _add_student_manual(df, user, section, kp)
    else:
        _add_student_bulk(df, user, section, kp)


def _add_student_manual(df, user: str, section: str, kp: str) -> None:
    """Add a single student via text inputs."""
    c1, c2, c3 = st.columns([2, 3, 1])
    sid  = c1.text_input("Student ID",   key=f"sid_{kp}",   placeholder="e.g. 2206001")
    name = c2.text_input("Student Name", key=f"sname_{kp}", placeholder="e.g. Rahim Uddin")
    c3.markdown("<br>", unsafe_allow_html=True)

    if c3.button("➕ Add", key=f"add_{kp}", type="primary"):
        sid, name = sid.strip(), name.strip()
        if not sid or not name:
            st.error("Both ID and Name are required.")
        elif sid in df["ID"].astype(str).values:
            st.error(f"ID '{sid}' already exists.")
        else:
            new_row = pd.DataFrame([{"ID": sid, "Name": name}])
            df = pd.concat([df, new_row], ignore_index=True)
            save_section(user, section, df)
            st.success(f"✅ Added: {name}")
            st.rerun()


def _add_student_bulk(df, user: str, section: str, kp: str) -> None:
    """Add multiple students via CSV text-area (ID,Name per line)."""
    bulk = st.text_area(
        "Paste  ID,Name  (one per line)",
        placeholder="2206001,Rahim Uddin\n2206002,Fatima Islam",
        key=f"bulk_{kp}", height=130,
    )

    if st.button("➕ Add All", key=f"bulk_btn_{kp}", type="primary"):
        added, skipped = [], []
        existing_ids = set(df["ID"].astype(str).values)

        for line in bulk.strip().splitlines():
            parts = line.split(",", 1)
            if len(parts) == 2:
                s, n = parts[0].strip(), parts[1].strip()
                if s and n and s not in existing_ids:
                    added.append({"ID": s, "Name": n})
                    existing_ids.add(s)
                else:
                    skipped.append(s)

        if added:
            df = pd.concat([df, pd.DataFrame(added)], ignore_index=True)
            save_section(user, section, df)
            st.success(f"✅ Added {len(added)} student(s).")
            if skipped:
                st.warning(f"Skipped (duplicate/empty): {', '.join(skipped)}")
            st.rerun()
        else:
            st.error("No valid rows found.")


def _render_student_list(df, user: str, section: str, kp: str, editable: bool) -> None:
    """Display the editable (or read-only) student list and save/delete controls."""
    if df.empty:
        st.info("No students yet. Add students above.")
        return

    count_label = f"{len(df)} STUDENT(S)"
    st.markdown(
        f"<p style='color:var(--text-3);font-size:0.85rem;font-weight:600;'>{count_label}</p>",
        unsafe_allow_html=True,
    )

    edited = st.data_editor(
        df[FIXED_COLS].reset_index(drop=True),
        use_container_width=True,
        key=f"editor_{kp}",
        disabled=not editable,
        hide_index=True,
    )

    if not editable:
        return

    col_save, col_del = st.columns([3, 2])

    with col_save:
        if st.button("💾 Save Changes", key=f"save_stu_{kp}",
                     type="primary", use_container_width=True):
            # Merge edited fixed columns back with existing attendance columns
            att_cols = [c for c in df.columns if c not in FIXED_COLS]
            merged   = edited.copy()
            if att_cols:
                for col in att_cols:
                    merged[col] = df[col].values
            save_section(user, section, merged)
            st.success("✅ Student list saved.")
            st.rerun()

    with col_del:
        with st.expander("🗑️ Remove a Student"):
            del_id = st.text_input("Student ID to remove", key=f"del_stu_{kp}",
                                   placeholder="Enter ID")
            if st.button("Remove", key=f"del_stu_btn_{kp}"):
                del_id = del_id.strip()
                if del_id in df["ID"].astype(str).values:
                    df = df[df["ID"].astype(str) != del_id].reset_index(drop=True)
                    save_section(user, section, df)
                    st.success(f"Removed ID: {del_id}")
                    st.rerun()
                else:
                    st.error("ID not found.")


# ════════════════════════════════════════════════════════════════════════════════
#  TEACHER DASHBOARD
# ════════════════════════════════════════════════════════════════════════════════

def teacher_dashboard() -> None:
    """Main dashboard for a logged-in teacher."""
    user = st.session_state.user

    _render_teacher_sidebar(user)
    _render_page_header("📘 My Dashboard", "Manage your sections and take attendance")
    _render_create_section_form(user)

    sections = list_sections(user)
    if not sections:
        st.info("No sections yet. Create one above to get started.")
        return

    section_count_badge = f"<span class='badge badge-blue'>{len(sections)}</span>"
    st.markdown(f"### My Sections &nbsp; {section_count_badge}", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    for section in sections:
        _render_section_card(user, section)


def _render_teacher_sidebar(user: str) -> None:
    with st.sidebar:
        st.markdown(f"### 👤 {user}")
        st.caption("Teacher Account")
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()


def _render_create_section_form(user: str) -> None:
    with st.expander("➕ Create New Section", expanded=False):
        sec_name = st.text_input("Section Name", placeholder="e.g. BGE-3rd Year B",
                                 key="new_sec_name")
        if st.button("Create Section", type="primary"):
            ok, msg = create_section(user, sec_name)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)


def _render_section_card(user: str, section: str) -> None:
    """Render one expander card for a section with stats and action buttons."""
    with st.expander(f"📘 {section}", expanded=False):
        df     = load_section(user, section)
        report = build_report(df)
        n      = len(report)

        # Summary metrics
        good       = int((report["Attendance %"] >= 75).sum()) if n else 0
        risk       = int((report["Attendance %"] < 60).sum())  if n else 0
        total_cls  = int(report["Total Classes"].max())         if n else 0

        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Students",   n)
        s2.metric("Classes",    total_cls)
        s3.metric("≥ 75%",      good)
        s4.metric("< 60% Risk", risk)

        _render_section_action_buttons(user, section)
        _render_section_delete_confirm(user, section)

        st.markdown("---")
        st.markdown("##### 👨‍🎓 Students")
        student_manager(user, section, editable=True)


def _render_section_action_buttons(user: str, section: str) -> None:
    """Take Attendance / View Report / Delete buttons for a section."""
    btn1, btn2, btn3 = st.columns([3, 3, 1])

    with btn1:
        if st.button("📋 Take Attendance", key=f"att_{section}",
                     use_container_width=True, type="primary"):
            st.session_state.page    = "attendance"
            st.session_state.section = section
            st.rerun()

    with btn2:
        if st.button("📊 View Report", key=f"rep_{section}", use_container_width=True):
            st.session_state.page    = "report"
            st.session_state.section = section
            st.rerun()

    with btn3:
        if st.button("🗑️", key=f"del_sec_{section}", help="Delete this section"):
            st.session_state[f"confirm_del_{section}"] = True


def _render_section_delete_confirm(user: str, section: str) -> None:
    """Confirmation prompt before deleting a section."""
    if not st.session_state.get(f"confirm_del_{section}"):
        return

    st.warning(f"Delete **{section}** and all its data? This cannot be undone.")
    yes_col, no_col = st.columns(2)

    if yes_col.button("Yes, delete", key=f"yes_del_{section}", type="primary"):
        delete_section(user, section)
        del st.session_state[f"confirm_del_{section}"]
        st.success(f"Section '{section}' deleted.")
        st.rerun()

    if no_col.button("Cancel", key=f"no_del_{section}"):
        del st.session_state[f"confirm_del_{section}"]
        st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
#  ADMIN PANEL
# ════════════════════════════════════════════════════════════════════════════════

def admin_panel() -> None:
    """Admin panel: user management and cross-teacher data view."""
    _render_admin_sidebar()
    _render_page_header("🔧 Admin Panel", "Manage teacher accounts and view all data")

    users    = load_users()
    teachers = [u for u in users if u != "admin"]

    tab_users, tab_data = st.tabs(["👥 User Management", "📂 All Data"])

    with tab_users:
        _render_create_teacher_form()
        st.markdown("---")
        _render_teacher_list(teachers)

    with tab_data:
        _render_all_data_view(teachers)


def _render_admin_sidebar() -> None:
    with st.sidebar:
        st.markdown("### 🔧 Admin")
        st.caption("Administrator Account")
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()


def _render_create_teacher_form() -> None:
    """Form to create a new teacher account (admin only)."""
    st.subheader("➕ Create Teacher Account")
    c1, c2, c3 = st.columns(3)
    new_u  = c1.text_input("Username",        key="new_teacher_u", placeholder="Username")
    new_p  = c2.text_input("Password",         key="new_teacher_p",  type="password", placeholder="Password")
    new_p2 = c3.text_input("Confirm Password", key="new_teacher_p2", type="password", placeholder="Confirm")

    if st.button("💾 Create Teacher Account", type="primary"):
        if new_p != new_p2:
            st.error("Passwords do not match.")
            return
        ok, msg = register_user(new_u, new_p)
        if ok:
            st.success(msg)
            for k in ["new_teacher_u", "new_teacher_p", "new_teacher_p2"]:
                st.session_state.pop(k, None)
            st.rerun()
        else:
            st.error(msg)


def _render_teacher_list(teachers: list[str]) -> None:
    """Expandable list of teacher accounts with reset-password and delete actions."""
    st.subheader("Current Teachers")
    if not teachers:
        st.info("No teacher accounts yet.")
        return

    for teacher in teachers:
        with st.expander(f"👤 {teacher}"):
            secs = list_sections(teacher)
            st.markdown(f"**Sections:** {', '.join(secs) if secs else 'None'}")
            st.markdown("<br>", unsafe_allow_html=True)

            r1, r2 = st.columns(2)

            with r1:
                new_pwd = st.text_input("New Password", type="password",
                                        key=f"rpwd_{teacher}", placeholder="Min. 4 characters")
                if st.button("🔑 Reset Password", key=f"reset_{teacher}", type="primary"):
                    ok, msg = reset_password(teacher, new_pwd)
                    st.success(msg) if ok else st.error(msg)

            with r2:
                st.markdown("&nbsp;", unsafe_allow_html=True)
                if st.button("🗑️ Delete User", key=f"deluser_{teacher}"):
                    st.session_state[f"confirm_delusr_{teacher}"] = True

            _render_delete_user_confirm(teacher)


def _render_delete_user_confirm(teacher: str) -> None:
    """Confirmation prompt before deleting a teacher account."""
    if not st.session_state.get(f"confirm_delusr_{teacher}"):
        return

    st.warning(f"Delete **{teacher}** and ALL their data? This cannot be undone.")
    yes_col, no_col = st.columns(2)

    if yes_col.button("Yes, delete", key=f"yes_delusr_{teacher}", type="primary"):
        ok, msg = delete_user(teacher)
        st.success(msg) if ok else st.error(msg)
        del st.session_state[f"confirm_delusr_{teacher}"]
        st.rerun()

    if no_col.button("Cancel", key=f"no_delusr_{teacher}"):
        del st.session_state[f"confirm_delusr_{teacher}"]
        st.rerun()


def _render_all_data_view(teachers: list[str]) -> None:
    """Admin view to browse any teacher's section data."""
    if not teachers:
        st.info("No teachers yet.")
        return

    sel_teacher = st.selectbox("Select Teacher", teachers)
    secs        = list_sections(sel_teacher)

    if not secs:
        st.info("No sections for this teacher.")
        return

    sel_sec = st.selectbox("Select Section", secs)
    df      = load_section(sel_teacher, sel_sec)

    sub1, sub2 = st.tabs(["Students", "Attendance Report"])

    with sub1:
        student_manager(sel_teacher, sel_sec, editable=True)

    with sub2:
        if df.empty:
            st.info("No data.")
        else:
            report = build_report(df)
            st.dataframe(report, use_container_width=True, hide_index=True)
            st.download_button(
                "📥 Download Report",
                data=to_excel_bytes(report),
                file_name=f"{sel_teacher}_{sel_sec}_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
            )


# ── Shared page header ────────────────────────────────────────────────────────

def _render_page_header(title: str, subtitle: str) -> None:
    st.markdown(f"""
    <div class='page-header'>
        <h1>{title}</h1>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)
