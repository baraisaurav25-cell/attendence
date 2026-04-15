"""
============================================================
  BioTrack: Smart Attendance System v2.0
  Dept. of Biotechnology & Genetic Engineering · SAU
  Features: Modern UI · Auto-Excel · Real-time Analytics
============================================================
"""

import customtkinter as ctk
import pandas as pd
import os
from datetime import datetime
from tkinter import messagebox
import random

# ── CONFIGURATION (ফাইল এবং কালার সেটিংস) ─────────────────────
STUDENTS_FILE = "students.xlsx"
REPORT_FILE   = "attendance_report.xlsx"

# লগইন ক্রেডেনশিয়াল (প্রয়োজনে এখান থেকে পরিবর্তন করতে পারবে)
USERS = {
    "admin":   {"password": "bge2024",  "role": "admin"},
    "teacher": {"password": "sau1234",  "role": "teacher"},
}

# কালার প্যালেট (GitHub Dark Theme Inspired)
BG_PRIMARY    = "#0D1117"; BG_SECONDARY  = "#161B22"; BG_CARD = "#1C2230"
BG_ROW_EVEN   = "#1A2438"; BG_ROW_ODD    = "#1C2230"; ACCENT_TEAL = "#00D4AA"
ACCENT_BLUE   = "#0EA5E9"; ACCENT_AMBER  = "#F59E0B"; TEXT_PRIMARY = "#E6EDF3"
TEXT_SECONDARY= "#8B949E"; GREEN_IND     = "#22C55E"; RED_IND = "#EF4444"
BORDER_COLOR  = "#30363D"; SEARCH_BG     = "#21262D"

SESSION_LABELS = {"AM": "🌅 Morning (AM)", "PM": "🌆 Afternoon (PM)"}

# ── DATA SETUP (এক্সেল ফাইল না থাকলে অটোমেটিক তৈরি করবে) ────────
def setup_initial_data():
    # মাস্টার স্টুডেন্ট লিস্ট তৈরি
    if not os.path.exists(STUDENTS_FILE):
        students = {
            "ID": [f"220{6000+i}" for i in range(1, 26)],
            "Name": ["Rahim Uddin", "Karim Hossain", "Sumaiya Akter", "Nasrin Begum", "Farhan Ahmed", 
                     "Tania Islam", "Saurav Barai", "Mehedi Hasan", "Sadia Rahman", "Jubayer Ahmed", 
                     "Nusrat Jahan", "Arif Hossain", "Sharmin Akter", "Sabbir Ahmed", "Mim Akter", 
                     "Rifat Islam", "Saurav Biswas", "Rabeya Khatun", "Imran Hossain", "Poly Akter", 
                     "Asif Ahmed", "Rima Begum", "Tanvir Hossain", "Laboni Das", "Sujon Mia"]
        }
        pd.DataFrame(students).to_excel(STUDENTS_FILE, index=False)
    
    # এটেনডেন্স রিপোর্ট ফাইল তৈরি (পুরো ক্লাসের ডাটা এখানে থাকবে)
    if not os.path.exists(REPORT_FILE):
        df = pd.read_excel(STUDENTS_FILE)
        report = df.copy()
        # স্যাম্পল হিসেবে ২ দিনের ডাটা ঢুকিয়ে রাখা (যাতে পার্সেন্টেজ দেখা যায়)
        for date in ["2026-04-10_AM", "2026-04-13_PM"]:
            report[date] = [random.choice([0, 1, 1, 1]) for _ in range(len(df))]
        report.to_excel(REPORT_FILE, index=False)

# ── DATA HELPERS (ডাটা প্রসেসিং লজিক) ───────────────────────
def load_report():
    if not os.path.exists(REPORT_FILE): return None
    return pd.read_excel(REPORT_FILE, dtype={"ID": str})

def compute_percentages(students_df, report_df):
    # তারিখের কলামগুলো খুঁজে বের করা (ID এবং Name বাদ দিয়ে)
    date_cols = [c for c in report_df.columns if c not in ("ID", "Name")] if report_df is not None else []
    total = len(date_cols)
    stats = {}
    for sid in students_df["ID"]:
        if report_df is None or total == 0: 
            stats[str(sid)] = 0
        else:
            row = report_df[report_df["ID"] == str(sid)]
            present = int(row[date_cols].sum(axis=1).values[0]) if not row.empty else 0
            stats[str(sid)] = round((present / total) * 100, 1)
    return stats

# ── GUI COMPONENTS (প্রতিটি স্টুডেন্টের রো বা সারি) ─────────────
class StudentRow(ctk.CTkFrame):
    def __init__(self, master, sid, name, pct, row_index, **kw):
        bg = BG_ROW_EVEN if row_index % 2 == 0 else BG_ROW_ODD
        super().__init__(master, fg_color=bg, corner_radius=6, **kw)
        self.sid = sid
        self.var = ctk.BooleanVar(value=False)
        self.grid_columnconfigure(2, weight=1)
        
        # সিরিয়াল, আইডি এবং নাম
        ctk.CTkLabel(self, text=f"{row_index+1:02d}", text_color=TEXT_SECONDARY, width=30).grid(row=0, column=0, padx=10, pady=8)
        ctk.CTkLabel(self, text=sid, font=ctk.CTkFont(weight="bold"), text_color=ACCENT_TEAL, width=90).grid(row=0, column=1, padx=5)
        ctk.CTkLabel(self, text=name, text_color=TEXT_PRIMARY, anchor="w").grid(row=0, column=2, padx=10, sticky="ew")
        
        # এটেনডেন্স চেক বক্স
        self.chk = ctk.CTkCheckBox(self, text="Present", variable=self.var, fg_color=ACCENT_TEAL, width=80)
        self.chk.grid(row=0, column=3, padx=10)

        # পার্সেন্টেজ লজিক (৬০% এর নিচে হলে লাল, উপরে হলে সবুজ)
        color = GREEN_IND if pct >= 60 else RED_IND
        self.pct_lbl = ctk.CTkLabel(self, text=f"{pct}%", font=ctk.CTkFont(weight="bold"), text_color=color, width=60)
        self.pct_lbl.grid(row=0, column=4, padx=15)

# ── MAIN APP (মূল অ্যাপ্লিকেশন উইন্ডো) ──────────────────────────
class AttendanceApp(ctk.CTk):
    def __init__(self, user, role):
        super().__init__()
        self.title(f"BioTrack SAU - {user}")
        self.geometry("1000x750")
        self.configure(fg_color=BG_PRIMARY)
        self.role = role
        self.all_rows = []
        setup_initial_data()
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        # হেডার সেকশন
        hdr = ctk.CTkFrame(self, fg_color=BG_SECONDARY, corner_radius=0, height=80)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="🧬 BioTrack: Smart Attendance System", font=ctk.CTkFont(size=24, weight="bold"), text_color=ACCENT_TEAL).pack(pady=(12,0))
        ctk.CTkLabel(hdr, text="Biotechnology & Genetic Engineering · Sylhet Agricultural University", text_color=TEXT_SECONDARY).pack()

        # কন্ট্রোল বার (সেশন সিলেক্টর এবং সেভ বাটন)
        tool = ctk.CTkFrame(self, fg_color=BG_CARD, height=60, corner_radius=0)
        tool.pack(fill="x", pady=2)
        
        self.sess_var = ctk.StringVar(value="AM")
        ctk.CTkRadioButton(tool, text="Morning (AM)", variable=self.sess_var, value="AM", text_color=TEXT_PRIMARY).pack(side="left", padx=20)
        ctk.CTkRadioButton(tool, text="Afternoon (PM)", variable=self.sess_var, value="PM", text_color=TEXT_PRIMARY).pack(side="left")
        
        ctk.CTkButton(tool, text="💾 Save Attendance", fg_color=ACCENT_TEAL, text_color="#000", font=ctk.CTkFont(weight="bold"), height=35, command=self._save).pack(side="right", padx=20)
        
        # সার্চ বার
        self.search_entry = ctk.CTkEntry(tool, placeholder_text="Search ID...", width=200, fg_color=SEARCH_BG, border_color=BORDER_COLOR)
        self.search_entry.pack(side="right", padx=10)
        self.search_entry.bind("<KeyRelease>", self._search)

        # স্ক্রলযোগ্য স্টুডেন্ট লিস্ট
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)

    def _load_data(self):
        # রিয়েল-টাইম ডাটা লোড এবং পার্সেন্টেজ আপডেট
        for w in self.scroll.winfo_children(): w.destroy()
        self.all_rows = []
        df = pd.read_excel(STUDENTS_FILE, dtype={"ID": str})
        report = load_report()
        pcts = compute_percentages(df, report)
        
        for i, row in df.iterrows():
            sid_str = str(row['ID'])
            r = StudentRow(self.scroll, sid_str, row['Name'], pcts.get(sid_str, 0), i)
            r.pack(fill="x", pady=2)
            self.all_rows.append(r)

    def _search(self, event):
        # আইডি দিয়ে সার্চ করার লজিক
        q = self.search_entry.get().lower()
        for r in self.all_rows:
            if q in r.sid.lower(): 
                r.pack(fill="x", pady=2)
            else: 
                r.pack_forget()

    def _save(self):
        # তারিখ অনুযায়ী নতুন কলাম তৈরি এবং এক্সেল আপডেট
        date_str = datetime.now().strftime("%Y-%m-%d")
        key = f"{date_str}_{self.sess_var.get()}"
        report = load_report()
        
        if report is None: return

        # বর্তমান সিলেকশন আপডেট করা
        for r in self.all_rows:
            report.loc[report["ID"] == r.sid, key] = 1 if r.var.get() else 0
        
        try:
            report.to_excel(REPORT_FILE, index=False)
            messagebox.showinfo("Success", f"Attendance for {key} has been saved to the overall report.")
            self._load_data() # ডাটা রিফ্রেশ করা
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file. Make sure Excel is closed.\n{e}")

# ── LOGIN WINDOW (লগইন উইন্ডো) ─────────────────────────────
class Login(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Login - BioTrack")
        self.geometry("400x500")
        self.configure(fg_color=BG_PRIMARY)
        self.result = None
        
        ctk.CTkLabel(self, text="🧬", font=ctk.CTkFont(size=60)).pack(pady=40)
        ctk.CTkLabel(self, text="BioTrack System", font=ctk.CTkFont(size=20, weight="bold"), text_color=ACCENT_TEAL).pack()
        
        self.u = ctk.CTkEntry(self, placeholder_text="Username", width=280, height=40)
        self.u.pack(pady=15)
        self.p = ctk.CTkEntry(self, placeholder_text="Password", show="●", width=280, height=40)
        self.p.pack(pady=10)
        
        ctk.CTkButton(self, text="Login →", fg_color=ACCENT_TEAL, text_color="#000", font=ctk.CTkFont(weight="bold"), height=45, width=280, command=self._check).pack(pady=30)

    def _check(self):
        user, pwd = self.u.get(), self.p.get()
        if user in USERS and USERS[user]["password"] == pwd:
            self.result = (user, USERS[user]["role"])
            self.destroy()
        else: 
            messagebox.showerror("Login Failed", "Invalid username or password.")

# ── ENTRY POINT ──────────────────────────────────────────
if __name__ == "__main__":
    ln = Login()
    ln.mainloop()
    
    # লগইন সফল হলে মেইন অ্যাপ চালু হবে
    if ln.result:
        app = AttendanceApp(ln.result[0], ln.result[1])
        app.mainloop()
