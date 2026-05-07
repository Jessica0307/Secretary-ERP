import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta

# --- 1. 雲端 Database 連線 (固定) ---
try:
    DB_URL = st.secrets["DB_URL"]
    engine = create_engine(DB_URL)
except:
    st.error("❌ 請在 Streamlit Secrets 填寫正確的 DB_URL")
    st.stop()

# --- 2. Navigation (保持 V34) ---
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
        col_edit, col_del = st.columns(2)
        new_name = col_edit.text_input("New Name")
        if col_edit.button("Update"):
            with engine.begin() as conn:
                conn.execute(text("UPDATE client_groups SET group_name=:n WHERE group_name=:t"), {"n": new_name, "t": target_g})
            st.rerun()
        if col_del.button("⚠️ Delete Group"):
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM client_groups WHERE group_name=:t"), {"t": target_g})
            st.rerun()

# --- 4. Company Register (排版絕對鎖定 + 確認機制) ---
elif choice == "🏢 Company Register":
    st.header("🏢 Company Records Management")
    
    mode = st.radio("Mode", ["🆕 Add New", "✏️ Edit Existing"], horizontal=True)
    
    df_all = pd.read_sql("SELECT * FROM companies", engine)
    groups = pd.read_sql("SELECT group_name FROM client_groups", engine)['group_name'].tolist()
    
    d = {'cg': "", 'en': "", 'ch': "", 'idate': None, 'place': "HK", 'p_oth': "", 'ci': "", 'br': "", 'type': "Private Company", 'ra': "", 'ca': "", 'rl': "", 'sl': "", 'cl': "", 'n2e': None, 'n2f': None, 'n2d': False, 'n4e': None, 'n4f': None, 'n4d': False, 'dis': None}
    target_id = None

    if mode == "✏️ Edit Existing" and not df_all.empty:
        edit_target = st.selectbox("Select Company to Edit", df_all['name_en'].tolist())
        row = df_all[df_all['name_en'] == edit_target].iloc[0]
        # 修正 KeyError 與欄位對應
        target_id = row['id'] if 'id' in row else row.name 
        d = {'cg': row['client_group'], 'en': row['name_en'], 'ch': row['name_ch'], 'idate': row['incorp_date'], 'place': row['incorp_place'], 'p_oth': row['incorp_place_others'], 'ci': row['ci_no'], 'br': row['br_no'], 'type': row['co_type'], 'ra': row['reg_addr'], 'ca': row['corres_addr'], 'rl': row.get('round_loc', ""), 'sl': row.get('sign_loc', ""), 'cl': row.get('seal_loc', ""), 'n2e': row['nd2a_eff_date'], 'n2f': row['nd2a_file_date'], 'n2d': str(row['nd2a_download']) == 'True', 'n4e': row['nd4_eff_date'], 'n4f': row['nd4_file_date'], 'n4d': str(row['nd4_download']) == 'True', 'dis': row['dissolution_date']}

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
    st.markdown("### 📝 Company Secretary Appointment (ND2A)")
    c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
    nd2a_eff = c1.date_input("Effective Date (Appt)", value=d['n2e'], key="n2e")
    nd2a_file = c2.date_input("Filing Date (ND2A)", value=d['n2f'], key="n2f")
    if nd2a_eff:
        c3.warning(f"Statutory Period: 15 days\n\n⚠️ Deadline: {nd2a_eff + timedelta(days=15)}")
    else: c3.info("Statutory Period: 15 days")
    nd
