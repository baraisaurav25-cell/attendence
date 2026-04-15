import streamlit as st
import pandas as pd
import os
import json
import hashlib
from datetime import datetime
from io import BytesIO

# ─────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────
USERS_FILE   = "biotrack_users.json"
REPORTS_DIR  = "biotrack_reports"   # one Excel per section
os.makedirs(REPORTS_DIR, exist_ok=True)

# ─────────────────────────────────────────────
#  PAGE CONFIG  &  CSS
# ─────────────────────────────────────────────
st.set_page_config(page_title="BioTrack", page_icon="🧬", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Share+Tech+Mono&display=swap');

html, body, [class*="css"] { font-family: 'Share Tech Mono', monospace; }
.main { background-color: #0D1117; }

h1, h2, h3 { font-family: 'Orbitron', sans-serif; color: #38BDF8; }

.pct-ok  { color: #22C55E; font-weight: bold; }
.pct-bad { color: #EF4444; font-weight: bold; }
.pct-mid { color: #FBBF24; font-weight: bold; }

.info-box {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 10px;
}
.section-badge {
    display: inline-block;
    background: #1D4ED8;
    color: white;
    border-radius: 4px;
    padding: 2px 10px;
    font-size: 0.82em;
    margin-left: 6px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  USER / AUTH HELPERS
# ─────────────────────────────────────────────
DEFAULT_ADMIN = {"password": _hash("bge2024"), "role": "admin", "sections": []}

def _hash(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()

def load_users() -> dict:
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE) as f:
            return json.load(f)
    # First run – seed admin
    users = {"admin": DEFAULT_ADMIN}
    save_users(users)
    return users

def save_users(users: dict):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

# ─────────────────────────────────────────────
#  SECTION / EXCEL HELPERS
# ─────────────────────────────────────────────
FIXED_COLS = ["ID", "Name", "Total Present", "Total Absent", "Total Class", "Attendance %"]

def section_file(section: str) -> str:
    safe = section.replace(" ", "_").replace("/", "-")
    return os.path.join(REPORTS_DIR, f"{safe}.xlsx")

def load_section(section: str) -> pd.DataFrame:
    path = section_file(section)
    if os.path.exists(path):
        df = pd.read_excel(path, dtype={"ID": str})
        # Ensure all fixed cols exist and are numeric
        for col in FIXED_COLS:
            if col not in df.columns:
                df[col] = 0
        for col in ["Total Present", "Total Absent", "Total Class", "Attendance %"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        return df
    # Empty template
    return pd.DataFrame(columns=FIXED_COLS)

def save_section(df: pd.DataFrame, section: str):
    df = recalculate(df)
    df.to_excel(section_file(section), index=False)

def recalculate(df: pd.DataFrame) -> pd.DataFrame:
    """Recalculate Total Present / Absent / Class / % from date columns."""
    date_cols = [c for c in df.columns if c not in FIXED_COLS]
    n = len(date_cols)
    if n == 0:
        df["Total Present"] = 0
        df["Total Absent"]  = 0
        df["Total Class"]   = 0
        df["Attendance %"]  = 0.0
        return df

    for idx in df.index:
        vals = df.loc[idx, date_cols]
        present = int(pd.to_numeric(vals, errors="coerce").fillna(0).sum())
        df.at[idx, "Total Present"] = present
        df.at[idx, "Total Absent"]  = n - present
        df.at[idx, "Total Class"]   = n
        df.at[idx, "Attendance %"]  = round(present / n * 100, 1)
    return df

def list_all_sections() -> list[str]:
    """Return every section that has an Excel file."""
    files = [f for f in os.listdir(REPORTS_DIR) if f.endswith(".xlsx")]
    return sorted([f[:-5].replace("_", " ") for f in files])

# ─────────────────────────────────────────────
#  SESSION STATE INIT
# ─────────────────────────────────────────────
for k, v in [("logged_in", False), ("username", ""), ("role", ""), ("page", "attendance")]:
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
#  LOGIN PAGE
# ─────────────────────────────────────────────
def login_page():
    st.title("🧬 BioTrack — Smart Attendance")
    st.markdown("---")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.subheader("Login")
        user = st.text_input("Username")
        pwd  = st.text_input("Password", type="password")
        if st.button("🔓 Login", use_container_width=True):
            users = load_users()
            if user in users and users[user]["password"] == _hash(pwd):
                st.session_state.logged_in = True
                st.session_state.username  = user
                st.session_state.role      = users[user]["role"]
                st.rerun()
            else:
                st.error("ভুল username অথবা password!")

# ─────────────────────────────────────────────
#  SIDEBAR NAV
# ─────────────────────────────────────────────
def sidebar():
    with st.sidebar:
        st.markdown(f"### 🧬 BioTrack")
        st.markdown(f"**User:** `{st.session_state.username}`  "
                    f"<span class='section-badge'>{st.session_state.role}</span>",
                    unsafe_allow_html=True)
        st.markdown("---")

        pages = ["📋 Attendance", "📊 Reports"]
        if st.session_state.role == "admin":
            pages += ["👥 Manage Users", "🗂️ Manage Sections"]

        choice = st.radio("Menu", pages, label_visibility="collapsed")
        st.markdown("---")
        if st.button("🚪 Logout"):
            for k in ["logged_in", "username", "role", "page"]:
                st.session_state[k] = False if k == "logged_in" else ""
            st.rerun()
        return choice

# ─────────────────────────────────────────────
#  PAGE: ATTENDANCE
# ─────────────────────────────────────────────
def page_attendance():
    st.title("📋 Attendance Entry")
    users = load_users()
    u = st.session_state.username

    # Which sections can this teacher see?
    if st.session_state.role == "admin":
        available = list_all_sections()
    else:
        available = users[u].get("sections", [])

    if not available:
        st.warning("আপনার কোনো Section assign করা নেই। Admin-কে বলুন।")
        return

    c1, c2, c3, c4 = st.columns([2, 2, 2, 3])
    with c1:
        section = st.selectbox("Section", available)
    with c2:
        sel_date = st.date_input("তারিখ", datetime.now())
    with c3:
        session  = st.selectbox("সেশন", ["AM", "PM", "Extra"])
    with c4:
        search   = st.text_input("🔍 ID / নাম সার্চ")

    date_key = f"{sel_date}_{session}"
    st.markdown(f"**Entry:** `{section}` → `{date_key}`")

    df = load_section(section)
    if df.empty:
        st.info("এই section-এ কোনো student নেই। 'Manage Sections' থেকে student যোগ করুন।")
        return

    # ── Ensure date_key column exists BEFORE any access ──
    if date_key not in df.columns:
        df[date_key] = 0

    # Search filter (after column is guaranteed to exist)
    if search:
        mask = (df["ID"].str.contains(search, case=False, na=False) |
                df["Name"].str.contains(search, case=False, na=False))
        view_df = df[mask].copy()
    else:
        view_df = df.copy()

    attendance_map = {}
    with st.form("att_form"):
        st.markdown(f"**মোট Student: {len(view_df)}**")
        header = st.columns([3, 1, 1])
        header[0].markdown("**Student**")
        header[1].markdown("**উপস্থিত**")
        header[2].markdown("**Attendance %**")
        st.divider()

        for _, row in view_df.iterrows():
            sid = str(row["ID"])
            pct = float(row.get("Attendance %", 0))
            pct_class = "pct-ok" if pct >= 75 else ("pct-mid" if pct >= 60 else "pct-bad")

            # Safe read — column is guaranteed to exist now
            try:
                cur_val = int(row[date_key])
            except (KeyError, ValueError, TypeError):
                cur_val = 0
            default = cur_val == 1

            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"`{sid}` {row['Name']}")
            with col2:
                attendance_map[sid] = st.checkbox(
                    "✔", value=default,
                    key=f"cb_{sid}_{date_key}_{section}",
                    label_visibility="collapsed"
                )
            with col3:
                st.markdown(f"<span class='{pct_class}'>{pct}%</span>", unsafe_allow_html=True)

        submitted = st.form_submit_button("💾 Save Attendance", use_container_width=True)

    if submitted:
        # Re-load fresh copy to avoid stale state
        df = load_section(section)
        if date_key not in df.columns:
            df[date_key] = 0
        for sid, present in attendance_map.items():
            df.loc[df["ID"] == sid, date_key] = 1 if present else 0
        save_section(df, section)
        st.success(f"✅ {date_key} — {section} সেকশনের attendance সেভ হয়েছে!")
        st.rerun()

# ─────────────────────────────────────────────
#  PAGE: REPORTS
# ─────────────────────────────────────────────
def page_reports():
    st.title("📊 Attendance Reports")
    users = load_users()
    u = st.session_state.username

    if st.session_state.role == "admin":
        available = list_all_sections()
    else:
        available = users[u].get("sections", [])

    if not available:
        st.warning("কোনো Section নেই।")
        return

    section = st.selectbox("Section বেছে নিন", available)
    df = load_section(section)

    if df.empty:
        st.info("এই section-এ কোনো data নেই।")
        return

    df = recalculate(df)

    # Summary metrics
    total_s = len(df)
    good    = len(df[df["Attendance %"] >= 75])
    bad     = len(df[df["Attendance %"] < 60])

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("মোট Student", total_s)
    m2.metric("≥75% (ভালো)", good)
    m3.metric("<60% (বিপদে)", bad)
    m4.metric("মোট ক্লাস", int(df["Total Class"].max()) if not df.empty else 0)

    st.divider()

    # Color-coded table
    st.subheader("Overall Summary")
    display_cols = ["ID", "Name", "Total Class", "Total Present", "Total Absent", "Attendance %"]
    styled = df[display_cols].style.applymap(
        lambda v: "color: #22C55E" if isinstance(v, float) and v >= 75
        else ("color: #EF4444" if isinstance(v, float) and v < 60 else ""),
        subset=["Attendance %"]
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)

    # Date-wise detail
    date_cols = [c for c in df.columns if c not in FIXED_COLS]
    if date_cols and st.checkbox("তারিখ-ওয়ারি বিস্তারিত দেখুন"):
        st.dataframe(df[["ID", "Name"] + date_cols], use_container_width=True, hide_index=True)

    # Download
    st.divider()
    st.subheader("📥 Excel Download")

    # Build multi-sheet Excel
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        # Sheet 1: Summary
        df[display_cols].to_excel(writer, sheet_name="Summary", index=False)
        # Sheet 2: Full (with dates)
        df.to_excel(writer, sheet_name="Full Data", index=False)

    st.download_button(
        "⬇️ Download Excel Report",
        data=buf.getvalue(),
        file_name=f"BioTrack_{section.replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Admin: cross-section report
    if st.session_state.role == "admin" and st.checkbox("সব Section-এর combined report"):
        all_dfs = []
        for sec in list_all_sections():
            tmp = load_section(sec)
            if not tmp.empty:
                tmp = recalculate(tmp)
                tmp.insert(0, "Section", sec)
                all_dfs.append(tmp[["Section"] + display_cols])
        if all_dfs:
            combined = pd.concat(all_dfs, ignore_index=True)
            st.dataframe(combined, use_container_width=True, hide_index=True)
            buf2 = BytesIO()
            combined.to_excel(buf2, index=False)
            st.download_button("⬇️ Combined Excel", buf2.getvalue(),
                               file_name="BioTrack_AllSections.xlsx")

# ─────────────────────────────────────────────
#  PAGE: MANAGE USERS  (admin only)
# ─────────────────────────────────────────────
def page_manage_users():
    st.title("👥 User Management")
    users = load_users()

    # ── Show existing users ──
    st.subheader("বর্তমান Users")
    rows = []
    for uname, info in users.items():
        rows.append({"Username": uname, "Role": info["role"],
                     "Sections": ", ".join(info.get("sections", []))})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.divider()

    # ── Create new teacher ──
    st.subheader("নতুন Teacher তৈরি করুন")
    with st.form("add_user_form"):
        new_user = st.text_input("Username")
        new_pwd  = st.text_input("Password", type="password")
        new_pwd2 = st.text_input("Confirm Password", type="password")
        all_secs = list_all_sections()
        assigned = st.multiselect("Sections assign করুন", all_secs)
        if st.form_submit_button("➕ Create Teacher"):
            if not new_user or not new_pwd:
                st.error("Username ও Password দিন।")
            elif new_pwd != new_pwd2:
                st.error("Password মিলছে না!")
            elif new_user in users:
                st.error("এই username ইতিমধ্যে আছে!")
            else:
                users[new_user] = {"password": _hash(new_pwd),
                                   "role": "teacher", "sections": assigned}
                save_users(users)
                st.success(f"✅ `{new_user}` তৈরি হয়েছে!")
                st.rerun()

    st.divider()

    # ── Edit sections of existing teacher ──
    st.subheader("Teacher-এর Section পরিবর্তন করুন")
    teachers = [u for u, i in users.items() if i["role"] == "teacher"]
    if teachers:
        with st.form("edit_sections_form"):
            pick = st.selectbox("Teacher বেছে নিন", teachers)
            all_secs = list_all_sections()
            cur_secs = users[pick].get("sections", [])
            new_secs = st.multiselect("Sections", all_secs, default=cur_secs)
            if st.form_submit_button("💾 আপডেট করুন"):
                users[pick]["sections"] = new_secs
                save_users(users)
                st.success("আপডেট হয়েছে!")
                st.rerun()

    st.divider()

    # ── Delete user ──
    st.subheader("User মুছুন")
    deletable = [u for u in users if u != "admin"]
    if deletable:
        with st.form("del_user_form"):
            del_user = st.selectbox("User বেছে নিন", deletable)
            if st.form_submit_button("🗑️ Delete", type="primary"):
                del users[del_user]
                save_users(users)
                st.success(f"`{del_user}` মুছে ফেলা হয়েছে।")
                st.rerun()

    # ── Change password ──
    st.divider()
    st.subheader("Password পরিবর্তন করুন")
    with st.form("change_pwd_form"):
        target = st.selectbox("User", list(users.keys()), key="cpwd_user")
        np1 = st.text_input("নতুন Password", type="password", key="np1")
        np2 = st.text_input("Confirm", type="password", key="np2")
        if st.form_submit_button("🔑 Password পরিবর্তন করুন"):
            if np1 != np2:
                st.error("Password মিলছে না!")
            elif len(np1) < 6:
                st.error("কমপক্ষে ৬ অক্ষর দিন।")
            else:
                users[target]["password"] = _hash(np1)
                save_users(users)
                st.success("Password পরিবর্তন হয়েছে!")

# ─────────────────────────────────────────────
#  PAGE: MANAGE SECTIONS  (admin only)
# ─────────────────────────────────────────────
def page_manage_sections():
    st.title("🗂️ Section Management")

    # ── Create new section ──
    st.subheader("নতুন Section তৈরি করুন")
    with st.form("new_section_form"):
        sec_name = st.text_input("Section নাম (যেমন: BGE-2nd Year A)")
        if st.form_submit_button("➕ Section তৈরি করুন"):
            if not sec_name.strip():
                st.error("নাম দিন।")
            elif os.path.exists(section_file(sec_name)):
                st.warning("এই নামে Section ইতিমধ্যে আছে।")
            else:
                empty = pd.DataFrame(columns=FIXED_COLS)
                save_section(empty, sec_name)
                st.success(f"✅ `{sec_name}` তৈরি হয়েছে!")
                st.rerun()

    st.divider()

    # ── Add students to section ──
    st.subheader("Section-এ Student যোগ করুন")
    all_secs = list_all_sections()
    if not all_secs:
        st.info("আগে একটি Section তৈরি করুন।")
        return

    with st.form("add_students_form"):
        sec = st.selectbox("Section", all_secs, key="add_stu_sec")
        st.caption("CSV ফরম্যাট: ID,Name  (প্রতি লাইনে একজন)")
        raw = st.text_area("Student তালিকা পেস্ট করুন",
                           placeholder="2206001,Rahim Uddin\n2206002,Karim Hossain")
        if st.form_submit_button("➕ যোগ করুন"):
            df = load_section(sec)
            errors, added = [], 0
            for line in raw.strip().splitlines():
                parts = [p.strip() for p in line.split(",", 1)]
                if len(parts) != 2 or not parts[0] or not parts[1]:
                    errors.append(line); continue
                sid, name = parts
                if sid in df["ID"].values:
                    errors.append(f"{sid} already exists")
                    continue
                new_row = {"ID": sid, "Name": name,
                           "Total Present": 0, "Total Absent": 0,
                           "Total Class": 0, "Attendance %": 0.0}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                added += 1
            save_section(df, sec)
            st.success(f"{added} জন student যোগ করা হয়েছে।")
            if errors:
                st.warning("এই লাইনগুলো skip হয়েছে: " + " | ".join(errors))
            st.rerun()

    st.divider()

    # ── View / remove students ──
    st.subheader("Student তালিকা ও মুছুন")
    view_sec = st.selectbox("Section", all_secs, key="view_stu_sec")
    df = load_section(view_sec)
    if df.empty:
        st.info("কোনো student নেই।")
    else:
        st.dataframe(df[["ID", "Name", "Attendance %"]], use_container_width=True, hide_index=True)
        with st.form("remove_student_form"):
            del_id = st.text_input("মুছতে Student ID দিন")
            if st.form_submit_button("🗑️ Remove Student", type="primary"):
                if del_id in df["ID"].values:
                    df = df[df["ID"] != del_id].reset_index(drop=True)
                    save_section(df, view_sec)
                    st.success(f"`{del_id}` মুছে ফেলা হয়েছে।")
                    st.rerun()
                else:
                    st.error("ID পাওয়া যায়নি।")

    st.divider()

    # ── Delete entire section ──
    st.subheader("Section মুছুন ⚠️")
    with st.form("del_section_form"):
        del_sec = st.selectbox("Section", all_secs, key="del_sec_sel")
        confirm = st.text_input('নিশ্চিত করতে "DELETE" টাইপ করুন')
        if st.form_submit_button("🗑️ Section মুছুন", type="primary"):
            if confirm == "DELETE":
                path = section_file(del_sec)
                if os.path.exists(path):
                    os.remove(path)
                st.success(f"`{del_sec}` মুছে ফেলা হয়েছে।")
                st.rerun()
            else:
                st.error('DELETE লিখুন।')

# ─────────────────────────────────────────────
#  MAIN ROUTER
# ─────────────────────────────────────────────
if not st.session_state.logged_in:
    login_page()
    st.stop()

choice = sidebar()

if "Attendance" in choice:
    page_attendance()
elif "Reports" in choice:
    page_reports()
elif "Users" in choice:
    page_manage_users()
elif "Sections" in choice:
    page_manage_sections()
