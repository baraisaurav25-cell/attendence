import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURATION ---
REPORT_FILE = "attendance_report.xlsx"

USERS = {
    "admin": {"password": "bge2024", "role": "admin"},
    "teacher": {"password": "sau1234", "role": "teacher"},
}

st.set_page_config(page_title="BioTrack Mobile", page_icon="🧬", layout="wide")

# --- CSS ---
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
        data = {
            "ID": [f"220{6000+i}" for i in range(1, 26)],
            "Name": ["Rahim Uddin", "Karim Hossain", "Sumaiya Akter", "Nasrin Begum", "Farhan Ahmed", 
                     "Tania Islam", "Saurav Barai", "Mehedi Hasan", "Sadia Rahman", "Jubayer Ahmed", 
                     "Nusrat Jahan", "Arif Hossain", "Sharmin Akter", "Sabbir Ahmed", "Mim Akter", 
                     "Rifat Islam", "Saurav Biswas", "Rabeya Khatun", "Imran Hossain", "Poly Akter", 
                     "Asif Ahmed", "Rima Begum", "Tanvir Hossain", "Laboni Das", "Sujon Mia"],
            "Total Present": 0,
            "Total Absent": 0,
            "Total Class": 0,
            "Attendance %": 0.0
        }
        df = pd.DataFrame(data)
        df.to_excel(REPORT_FILE, index=False)
        return df

def update_calculations(df):
    # তারিখের কলামগুলো খুঁজে বের করা (ফিক্সড কলামগুলো বাদ দিয়ে)
    fixed_cols = ["ID", "Name", "Total Present", "Total Absent", "Total Class", "Attendance %"]
    date_cols = [c for c in df.columns if c not in fixed_cols]
    
    total_classes = len(date_cols)
    
    for index, row in df.iterrows():
        if total_classes > 0:
            present_count = row[date_cols].sum()
            absent_count = total_classes - present_count
            pct = round((present_count / total_classes) * 100, 1)
            
            df.at[index, "Total Present"] = int(present_count)
            df.at[index, "Total Absent"] = int(absent_count)
            df.at[index, "Total Class"] = int(total_classes)
            df.at[index, "Attendance %"] = pct
    return df

# --- LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🧬 BioTrack Login")
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        if user in USERS and USERS[user]["password"] == pwd:
            st.session_state.logged_in = True
            st.rerun()
        else: st.error("Invalid Credentials")
    st.stop()

# --- MAIN APP ---
df = load_data()

st.title("🧬 BioTrack: Smart Attendance")
col1, col2, col3 = st.columns([2, 2, 3])

with col1:
    selected_date = st.date_input("তারিখ", datetime.now())
with col2:
    session = st.selectbox("সেশন", ["AM", "PM", "Extra"])
with col3:
    search = st.text_input("🔍 আইডি সার্চ করুন")

date_key = f"{selected_date}_{session}"
st.write(f"এন্ট্রি নিচ্ছেন: **{date_key}**")

# --- FORM ---
attendance_updates = {}
filtered_df = df[df['ID'].str.contains(search)] if search else df

with st.form("attendance_form"):
    for _, row in filtered_df.iterrows():
        sid = str(row['ID'])
        pct = row['Attendance %']
        color = "green-pct" if pct >= 60 else "red-pct"
        
        default_val = False
        if date_key in df.columns:
            default_val = True if df.loc[df['ID'] == sid, date_key].values[0] == 1 else False
            
        c1, c2 = st.columns([3, 1])
        with c1:
            attendance_updates[sid] = st.checkbox(f"{sid} - {row['Name']}", value=default_val)
        with c2:
            st.markdown(f"<span class='{color}'>{pct}%</span>", unsafe_allow_html=True)
            
    if st.form_submit_button("💾 Save Attendance", use_container_width=True):
        if date_key not in df.columns:
            df[date_key] = 0
        
        for sid, is_present in attendance_updates.items():
            df.loc[df['ID'] == sid, date_key] = 1 if is_present else 0
        
        # ক্যালকুলেশন আপডেট করা
        df = update_calculations(df)
        df.to_excel(REPORT_FILE, index=False)
        st.success("সেভ হয়েছে!")
        st.rerun()

# --- DISPLAY ---
if st.checkbox("ফুল রিপোর্ট দেখুন"):
    st.dataframe(df[["ID", "Name", "Total Class", "Total Present", "Total Absent", "Attendance %"]])
    with open(REPORT_FILE, "rb") as f:
        st.download_button("📩 Download Excel", f, file_name="BioTrack_Report.xlsx")
