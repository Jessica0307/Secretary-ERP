import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime, timedelta

# --- 1. Database Setup (保持 File 名連動) ---
current_file = os.path.basename(__file__).replace('.py', '.db')
conn = sqlite3.connect(current_file, check_same_thread=False)
c = conn.cursor()

# 確保所有結構鎖定
c.execute('''CREATE TABLE IF NOT EXISTS companies 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, client_group TEXT, name_en TEXT, name_ch TEXT, 
              incorp_date DATE, incorp_place TEXT, incorp_place_others TEXT, ci_no TEXT, br_no TEXT, co_type TEXT, 
              reg_addr TEXT, corres_addr TEXT, round_loc TEXT, sign_loc TEXT, seal_loc TEXT,
              nd2a_eff_date DATE, nd2a_file_date DATE, nd2a_download TEXT,
              nd4_eff_date DATE, nd4_file_date DATE, nd4_download TEXT,
              dissolution_date DATE, status TEXT DEFAULT 'Active')''')

c.execute('''CREATE TABLE IF NOT EXISTS client_groups (id INTEGER PRIMARY KEY, group_name TEXT UNIQUE)''')
conn.commit()

# --- 2. Navigation ---
st.set_page_config(page_title=f"ERP {current_file}", layout="wide")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "📜 Statutory Registers", "⚙️ Group Management"])

# --- 3. Group Management (保持 Edit & Delete 功能) ---
if choice == "⚙️ Group Management":
    st.header("⚙️ Client Group Management")
    new_g = st.text_input("Group Name to Add")
    if st.button("Add Group"):
        try:
            c.execute("INSERT INTO client_groups (group_name) VALUES (?)", (new_g,))
            conn.commit()
            st.rerun()
        except: st.error("Exists.")
    
    st.write("---")
    g_df = pd.read_sql("SELECT * FROM client_groups", conn)
    if not g_df.empty:
        target_g = st.selectbox("Select Group", g_df['group_name'].tolist())
        col_edit, col_del = st.columns(2)
        new_name = col_edit.text_input("New Name")
        if col_edit.button("Update"):
            c.execute("UPDATE client_groups SET group_name=? WHERE group_name=?", (new_name, target_g))
            c.execute("UPDATE companies SET client_group=? WHERE client_group=?", (new_name, target_g))
            conn.commit()
            st.rerun()
        if col_del.button("⚠️ Delete"):
            c.execute("DELETE FROM client_groups WHERE group_name=?", (target_g,))
            conn.commit()
            st.rerun()

# --- 4. Company Register (排版絕對鎖定 + 新增法定日數標明) ---
elif choice == "🏢 Company Register":
    st.header("🏢 Company Records Management")
    
    st.markdown("### General Information")
    existing_groups = pd.read_sql("SELECT group_name FROM client_groups", conn)['group_name'].tolist()
    client_group = st.selectbox("Select Client Group", [""] + existing_groups)
    
    col1, col2 = st.columns(2)
    name_en = col1.text_input("Company English Name")
    name_ch = col2.text_input("Company Chinese Name")
    
    col3, col4 = st.columns(2)
    inc_date = col3.date_input("Date of Incorporation")
    inc_place = col4.selectbox("Place of Incorporation", ["HK", "BVI", "Cayman Island", "Others"])
    place_others = st.text_input("Specify Country") if inc_place == "Others" else ""

    st.write("---")
    
    # CI 左, BR 右 (LOCK)
    col_ci, col_br = st.columns(2)
    ci_no = col_ci.text_input("CI Number")
    br_no = col_br.text_input("BR Number")
    co_type = st.selectbox("Company Type", ["Private Company", "Public Company", "Company Limited by Guarantee"])
    
    st.write("---")

    # ND2A (LOCK + 新增法定日數)
    st.markdown("### 📝 Company Secretary Appointment (ND2A)")
    c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
    nd2a_eff = c1.date_input("Effective Date (Appt)", value=None, key="n2e")
    nd2a_file = c2.date_input("Filing Date (ND2A)", value=None, key="n2f")
    if nd2a_eff:
        # 直接標明法定日數 15 日
        c3.warning(f"Statutory Period: 15 days\n\n⚠️ Deadline: {nd2a_eff + timedelta(days=15)}")
    else: 
        c3.info("Statutory Period: 15 days")
    nd2a_dl = c4.checkbox("Downloaded", key="n2d")

    # ND4 (LOCK + 新增法定日數)
    st.markdown("### 📝 Company Secretary Resignation (ND4)")
    r1, r2, r3, r4 = st.columns([2, 2, 2, 1])
    nd4_eff = r1.date_input("Effective Date (Resign)", value=None, key="n4e")
    nd4_file = r2.date_input("Filing Date (ND4)", value=None, key="n4f")
    if nd4_eff:
        # 直接標明法定日數 15 日
        r3.warning(f"Statutory Period: 15 days\n\n⚠️ Deadline: {nd4_eff + timedelta(days=15)}")
    else: 
        r3.info("Statutory Period: 15 days")
    nd4_dl = r4.checkbox("Downloaded", key="n4d")

    st.write("---")

    # 地址 (LOCK)
    st.markdown("### 📍 Address & Contact")
    col_reg, col_cor = st.columns(2)
    reg_addr = col_reg.text_area("Registered Office Address")
    corres_addr = col_cor.text_area("Correspondence Address")
    
    # 印章 (LOCK)
    st.markdown("### 🗄️ Seal Storage") 
    l1, l2, l3 = st.columns(3)
    round_l = l1.text_input("Round Chop Location")
    sign_l = l2.text_input("Signature Chop Location")
    common_l = l3.text_input("Common Seal Location")
    
    st.write("---")
    dis_date = st.date_input("Company Dissolution Date", value=None)
    
    if st.button("Save To Records"):
        c.execute('''INSERT INTO companies (client_group, name_en, name_ch, incorp_date, incorp_place, 
                    incorp_place_others, ci_no, br_no, co_type, reg_addr, corres_addr, 
                    round_loc, sign_loc, seal_loc, nd2a_eff_date, nd2a_file_date, nd2a_download, 
                    nd4_eff_date, nd4_file_date, nd4_download, dissolution_date) 
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                  (client_group, name_en, name_ch, inc_date, inc_place, place_others, 
                   ci_no, br_no, co_type, reg_addr, corres_addr, round_l, sign_l, common_l,
                   nd2a_eff, nd2a_file, str(nd2a_dl), nd4_eff, nd4_file, str(nd4_dl), dis_date))
        conn.commit()
        st.success("Saved!")

# --- 5. Dashboard ---
elif choice == "📊 Dashboard":
    st.header("📊 Compliance Overview")
    df = pd.read_sql("SELECT * FROM companies", conn)
    st.dataframe(df)
