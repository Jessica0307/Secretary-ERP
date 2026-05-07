import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta

# --- 1. Database Connection ---
try:
    DB_URL = st.secrets["DB_URL"]
    engine = create_engine(DB_URL)
except:
    st.error("❌ Please check DB_URL in Secrets")
    st.stop()

# --- 2. Navigation (LOCK V34 Layout) ---
st.set_page_config(page_title="ERP Cloud V34", layout="wide")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "⚙️ Group Management"])

# --- 3. Group Management ---
if choice == "⚙️ Group Management":
    st.header("⚙️ Client Group Management")
    new_g = st.text_input("Group Name to Add")
    if st.button("Add Group"):
        try:
            pd.DataFrame([{'group_name': new_g}]).to_sql('client_groups', engine, if_exists='append', index=False)
            st.rerun()
        except: st.error("Exists.")
    
    st.write("---")
    g_df = pd.read_sql("SELECT * FROM client_groups", engine)
    if not g_df.empty:
        target_g = st.selectbox("Select Group", g_df['group_name'].tolist())
        with st.popover("⚠️ Delete Group"):
            st.warning(f"Delete group '{target_g}'?")
            if st.button("Confirm Delete Group"):
                new_df = g_df[g_df['group_name'] != target_g]
                new_df.to_sql('client_groups', engine, if_exists='replace', index=False)
                st.rerun()

# --- 4. Company Register ---
elif choice == "🏢 Company Register":
    st.header("🏢 Company Records Management")
    mode = st.radio("Mode", ["🆕 Add New", "✏️ Edit Existing"], horizontal=True)
    
    df_all = pd.read_sql("SELECT * FROM companies", engine)
    groups = pd.read_sql("SELECT group_name FROM client_groups", engine)['group_name'].tolist()
    
    d = {'cg': "", 'en': "", 'ch': "", 'idate': None, 'place': "HK", 'p_oth': "", 'ci': "", 'br': "", 'type': "Private Company", 'ra': "", 'ca': "", 'rl': "", 'sl': "", 'cl': "", 'n2e': None, 'n2f': None, 'n2d': False, 'n4e': None, 'n4f': None, 'n4d': False, 'dis': None}
    target_name = None

    if mode == "✏️ Edit Existing" and not df_all.empty:
        target_name = st.selectbox("Select Company to Edit", df_all['name_en'].tolist())
        row = df_all[df_all['name_en'] == target_name].iloc[0]
        
        d = {
            'cg': row.get('client_group', ""), 'en': row.get('name_en', ""), 'ch': row.get('name_ch', ""), 
            'idate': row.get('incorp_date'), 'place': row.get('incorp_place', "HK"), 
            'p_oth': row.get('incorp_place_others', ""), 'ci': row.get('ci_no', ""), 'br': row.get('br_no', ""), 
            'type': row.get('co_type', "Private Company"), 'ra': row.get('reg_addr', ""), 'ca': row.get('corres_addr', ""),
            'rl': row.get('round_loc', ""), 'sl': row.get('sign_loc', ""), 'cl': row.get('seal_loc', ""),
            'n2e': row.get('nd2a_eff_date'), 'n2f': row.get('nd2a_file_date'), 
            'n2d': str(row.get('nd2a_download', "")) == 'True',
            'n4e': row.get('nd4_eff_date'), 'n4f': row.get('nd4_file_date'), 
            'n4d': str(row.get('nd4_download', "")) == 'True',
            'dis': row.get('dissolution_date')
        }

    st.markdown("### General Information")
    client_group = st.selectbox("Select Client Group", [""] + groups, index=(groups.index(d['cg'])+1 if d['cg'] in groups else 0))
    col1, col2 = st.columns(2)
    name_en = col1.text_input("Company English Name", value=d['en'])
    name_ch = col2.text_input("Company Chinese Name", value=d['ch'])
    col3, col4 = st.columns(2)
    inc_date = col3.date_input("Date of Incorporation", value=d['idate'])
    inc_place = col4.selectbox("Place of Incorporation", ["HK", "BVI", "Cayman Island", "Others"], index=["HK", "BVI", "Cayman Island", "Others"].index(d['place']))
    place_others = st.text_input("Specify Country", value=d['p_oth']) if inc_place == "Others" else ""

    st.write("---")
    col_ci, col_br = st.columns(2)
    ci_no = col_ci.text_input("CI Number", value=d['ci'])
    br_no = col_br.text_input("BR Number", value=d['br'])
    co_type = st.selectbox("Company Type", ["Private Company", "Public Company", "Company Limited by Guarantee"], index=["Private Company", "Public Company", "Company Limited by Guarantee"].index(d['type']))
    
    st.write("---")
    # --- ND2A 位 (100% 還原法定日數顯示) ---
    st.markdown("### 📝 Company Secretary Appointment (ND2A)")
    c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
    nd2a_eff = c1.date_input("Effective Date (Appt)", value=d['n2e'], key="n2e")
    nd2a_file = c2.date_input("Filing Date (ND2A)", value=d['n2f'], key="n2f")
    if nd2a_eff:
        # 直接標明法定日數 15 日
        c3.warning(f"Statutory Period: 15 days\n\n⚠️ Deadline: {nd2a_eff + timedelta(days=15)}")
    else: 
        c3.info("Statutory Period: 15 days")
    nd2a_dl = c4.checkbox("Downloaded", value=d['n2d'], key="n2d")

    # --- ND4 位 (100% 還原法定日數顯示) ---
    st.markdown("### 📝 Company Secretary Resignation (ND4)")
    r1, r2, r3, r4 = st.columns([2, 2, 2, 1])
    nd4_eff = r1.date_input("Effective Date (Resign)", value=d['n4e'], key="n4e")
    nd4_file = r2.date_input("Filing Date (ND4)", value=d['n4f'], key="n4f")
    if nd4_eff:
        # 直接標明法定日數 15 日
        r3.warning(f"Statutory Period: 15 days\n\n⚠️ Deadline: {nd4_eff + timedelta(days=15)}")
    else: 
        r3.info("Statutory Period: 15 days")
    nd4_dl = r4.checkbox("Downloaded", value=d['n4d'], key="n4d")

    st.write("---")
    st.markdown("### 📍 Address & Contact")
    col_reg, col_cor = st.columns(2)
    reg_addr = col_reg.text_area("Registered Office Address", value=d['ra'])
    corres_addr = col_cor.text_area("Correspondence Address", value=d['ca'])
    
    st.markdown("### 🗄️ Seal Storage") 
    l1, l2, l3 = st.columns(3)
    round_l = l1.text_input("Round Chop Location", value=d['rl'])
    sign_l = l2.text_input("Signature Chop Location", value=d['sl'])
    common_l = l3.text_input("Common Seal Location", value=d['cl'])
    
    st.write("---")
    dis_date = st.date_input("Company Dissolution Date", value=d['dis'])
    
    # --- 確認與保存邏輯 (Pandas 覆蓋法 + 確認 Popover) ---
    if mode == "🆕 Add New":
        with st.popover("💾 Save To Cloud"):
            st.write("Confirm save new company?")
            if st.button("Yes, Confirm Save"):
                new_data = {'client_group': client_group, 'name_en': name_en, 'name_ch': name_ch, 'incorp_date': inc_date, 'incorp_place': inc_place, 'incorp_place_others': place_others, 'ci_no': ci_no, 'br_no': br_no, 'co_type': co_type, 'reg_addr': reg_addr, 'corres_addr': corres_addr, 'round_loc': round_l, 'sign_loc': sign_l, 'seal_loc': common_l, 'nd2a_eff_date': nd2a_eff, 'nd2a_file_date': nd2a_file, 'nd2a_download': str(nd2a_dl), 'nd4_eff_date': nd4_eff, 'nd4_file_date': nd4_file, 'nd4_download': str(nd4_dl), 'dissolution_date': dis_date}
                pd.DataFrame([new_data]).to_sql('companies', engine, if_exists='append', index=False)
                st.success("Saved!")
                st.rerun()
    else:
        col_b1, col_b2 = st.columns(2)
        with col_b1.popover("🆙 Update Record"):
            st.write("Confirm update this record?")
            if st.button("Yes, Confirm Update"):
                df_filtered = df_all[df_all['name_en'] != target_name]
                updated_row = {'client_group': client_group, 'name_en': name_en, 'name_ch': name_ch, 'incorp_date': inc_date, 'incorp_place': inc_place, 'incorp_place_others': place_others, 'ci_no': ci_no, 'br_no': br_no, 'co_type': co_type, 'reg_addr': reg_addr, 'corres_addr': corres_addr, 'round_loc': round_l, 'sign_loc': sign_l, 'seal_loc': common_l, 'nd2a_eff_date': nd2a_eff, 'nd2a_file_date': nd2a_file, 'nd2a_download': str(nd2a_dl), 'nd4_eff_date': nd4_eff, 'nd4_file_date': nd4_file, 'nd4_download': str(nd4_dl), 'dissolution_date': dis_date}
                final_df = pd.concat([df_filtered, pd.DataFrame([updated_row])], ignore_index=True)
                final_df.to_sql('companies', engine, if_exists='replace', index=False)
                st.success("Updated!")
                st.rerun()
            
        with col_b2.popover("🚨 DELETE RECORD"):
            st.markdown("### ⚠️ DANGER ZONE")
            st.error(f"Deleting: **{target_name}**")
            if st.button("🔥 YES, DELETE FOREVER"):
                df_filtered = df_all[df_all['name_en'] != target_name]
                df_filtered.to_sql('companies', engine, if_exists='replace', index=False)
                st.warning("Deleted!")
                st.rerun()

# --- 5. Dashboard ---
elif choice == "📊 Dashboard":
    st.header("📊 Compliance Overview")
    df = pd.read_sql("SELECT * FROM companies", engine)
    st.dataframe(df, use_container_width=True)
