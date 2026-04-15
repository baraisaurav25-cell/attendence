import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURATION ---
REPORT_FILE = "attendance_report.xlsx"

# লগইন ক্রেডেনশিয়াল
USERS = {
    "admin": {"password": "bge2024", "role": "admin"},
    "teacher": {"password": "sau1234", "role": "teacher"},
}

# --- PAGE CONFIG ---
st.set_page_config(page_title="BioTrack Mobile", page_icon="🧬", layout="wide")

# --- CSS FOR STYLING (GitHub Dark Theme Style) ---
st.markdown("""
    <style>
    .main { background-color: #0D1117; }
    .stCheckbox { background-color: #161B22; padding: 10px; border-radius: 5px; margin: 2px 0px; }
    .red-pct { color: #EF4444; font-weight: bold; }
    .green-pct { color: #22C55E; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA HELPERS ---
def load_data():
    if os.path.exists(REPORT_FILE):
        return pd.read_excel(REPORT_FILE, dtype={'ID': str})
    else:
        # স্যাম্পল ডাটা দিয়ে ফাইল তৈরি
        data = {
            "ID": [f"220{6000+i}" for i in range(1, 26)],
            "Name": ["Rahim Uddin", "Karim Hossain", "Sumaiya Akter", "Nasrin Begum", "Farhan Ahmed", 
                     "Tania Islam", "Saurav Barai", "Mehedi Hasan", "Sadia Rahman", "Jubayer Ahmed", 
                     "Nusrat Jahan", "Arif Hossain", "Sharmin Akter", "Sabbir Ahmed", "Mim Akter", 
                     "Rifat Islam", "Saurav Biswas", "Rabeya Khatun", "Imran Hossain", "Poly Akter", 
                     "Asif Ahmed", "Rima Begum", "Tanvir Hossain", "Laboni Das", "Sujon Mia"]
        }
        df = pd.DataFrame(data)
        df.to_excel(REPORT_FILE, index=False)
        return df

def get_stats(df):
    date_cols = [c for c in df.columns if c not in ("ID", "Name")]
    total_classes = len(date_cols)
    if total_classes == 0:
        return {str(sid): 0 for sid in df["ID"]}
    
    stats = {}
    for _, row in df.iterrows():
        presents = row[date_cols].sum()
        stats[str(row['ID'])] = round((presents / total_classes) * 100, 1)
    return stats

# --- LOGIN LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🧬 BioTrack Login")
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        if user in USERS and USERS[user]["password"] == pwd:
            st.session_state.logged_in = True
            st.session_state.user = user
            st.rerun()
        else:
            st.error("ভুল ইউজারনেম বা পাসওয়ার্ড!")
    st.stop()

# --- MAIN APP ---
df = load_data()
stats = get_stats(df)

st.title("🧬 BioTrack: Smart Attendance")
st.write(f"Logged in as: **{st.session_state.user.capitalize()}**")

# কন্ট্রোল প্যানেল
col1, col2, col3 = st.columns([2, 2, 3])
with col1:
    date_pick = st.date_input("তারিখ", datetime.now())
with col2:
    session = st.selectbox("সেশন", ["AM", "PM"])
with col3:
    search = st.text_input("🔍 Search Student ID")

date_key = f"{date_pick}_{session}"

# এটেনডেন্স ফর্ম
st.write("---")
attendance_updates = {}

filtered_df = df[df['ID'].str.contains(search)] if search else df

with st.form("attendance_form"):
    # হেডার সারি
    h1, h2, h3 = st.columns([1, 2, 1])
    h1.write("**ID & Name**")
    h3.write("**Attendance & %**")
    
    for _, row in filtered_df.iterrows():
        sid = str(row['ID'])
        pct = stats.get(sid, 0)
        pct_class = "green-pct" if pct >= 60 else "red-pct"
        
        c1, c2 = st.columns([3, 1])
        with c1:
            # বর্তমান স্ট্যাটাস চেক করা (যদি আগে দেওয়া থাকে)
            default_val = False
            if date_key in df.columns:
                default_val = True if df.loc[df['ID'] == sid, date_key].values[0] == 1 else False
            
            attendance_updates[sid] = st.checkbox(f"{sid} - {row['Name']}", value=default_val)
        with c2:
            st.markdown(f"<span class='{pct_class}'>{pct}%</span>", unsafe_allow_html=True)
            
    save_btn = st.form_submit_button("💾 Save All Changes", use_container_width=True)

if save_btn:
    if date_key not in df.columns:
        df[date_key] = 0
    
    for sid, is_present in attendance_updates.items():
        df.loc[df['ID'] == sid, date_key] = 1 if is_present else 0
    
    df.to_excel(REPORT_FILE, index=False)
    st.success(f"সফলভাবে {date_key} এর ডাটা সেভ হয়েছে!")
    st.rerun()

# রিপোর্ট ডাউনলোড অপশন
if st.checkbox("Download Full Excel Report"):
    with open(REPORT_FILE, "rb") as f:
        st.download_button("📩 Download .xlsx File", f, file_name=REPORT_FILE)