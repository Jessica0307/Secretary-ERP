import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta

# --- 1. 雲端 Database 連線 (取代 sqlite3) ---
try:
    DB_URL = st.secrets["DB_URL"]
    engine = create_engine(DB_URL)
except:
    st.error("❌ Please set DB_URL in Streamlit Secrets.")
    st.stop()

# 初始化變更紀錄表
with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id SERIAL PRIMARY KEY,
            company_name TEXT,
            action TEXT,
            change_details TEXT,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))

# --- 2. Navigation (100% V34) ---
st.set_page_config(page_title="Secretarial System V34 Cloud", layout="wide")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "📜 Statutory Registers", "⚙️ Group Management"])

# --- 3. Group Management (100% V34 佈局) ---
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
                conn.execute(text("UPDATE client_groups SET group_name=:n WHERE group_name=:o"), {"n": new_name, "o": target_g})
                conn.execute(text("UPDATE companies SET client_group=:n WHERE client_group=:o"), {"n": new_name, "o": target_g})
            st.rerun()
        if col_del.button("⚠️ Delete"):
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM client_groups WHERE group_name=:g"), {"g": target_g})
            st.rerun()

# --- 4. Company Register (V34 排版絕對鎖定 + 同頁 Edit 功能) ---
elif choice == "🏢 Company Register":
    st.header("🏢 Company Records Management")
    
    # 加入模式切換 (不影響下方排版)
    mode = st.radio("Mode", ["🆕 Add New", "✏️ Edit Existing"], horizontal=True)
    
    df_all = pd.read_sql("SELECT * FROM companies", engine)
    existing_groups = pd.read_sql("SELECT group_name FROM client_groups", engine)['group_name'].tolist()
    
    # 初始化資料 (Edit 模式會自動填入)
    default = {'cg': "", 'en': "", 'ch': "", 'idate': None, 'place': "HK", 'oth': "", 'ci': "", 'br': "", 'type': "Private Company", 'ra': "", 'ca': "", 'rl': "", 'sl': "", 'cl': "", 'n2e': None, 'n2f': None, 'n2d': False, 'n4e': None, 'n4f': None, 'n4d': False, 'dis': None}
    target_id = None

    if mode == "✏️ Edit Existing" and not df_all.empty:
        edit_target = st.selectbox("Select Company to Edit", df_all['name_en'].tolist())
        row = df_all[df_all['name_en'] == edit_target].iloc[0]
        target_id = row['id']
        default = {
            'cg': row['client_group'], 'en': row['name_en'], 'ch': row['name_ch'], 'idate': row['incorp_date'],
            'place': row['incorp_place'], 'oth': row['incorp_place_others'], 'ci': row['ci_no'], 'br': row['br_no'],
            'type': row['co_type'], 'ra': row['reg_addr'], 'ca': row['corres_addr'], 'rl': row['round_loc'],
            'sl': row['sign_loc'], 'cl': row['seal_loc'], 'n2e': row['nd2a_eff_date'], 'n2f': row['nd2a_file_date'],
            'n2d': row['nd2a_download'] == 'True', 'n4e': row['nd4_eff_date'], 'n4f': row['nd4_file_date'],
            'n4d': row['nd4_download'] == 'True', 'dis': row['dissolution_date']
        }

    st.markdown("### General Information")
    client_group = st.selectbox("Select Client Group", [""] + existing_groups, index=(existing_groups.index(default['cg'])+1 if default['cg'] in existing_groups else 0))
    
    col1, col2 = st.columns(2)
    name_en = col1.text_input("Company English Name", value=default['en'])
    name_ch = col2.text_input("Company Chinese Name", value=default['ch'])
    
    col3, col4 = st.columns(2)
    inc_date = col3.date_input("Date of Incorporation", value=default['idate'])
    inc_place = col4.selectbox("Place of Incorporation", ["HK", "BVI", "Cayman Island", "Others"], index=["HK", "BVI", "Cayman Island", "Others"].index(default['place']))
    place_others = st.text_input("Specify Country", value=default['oth']) if inc_place == "Others" else ""

    st.write("---")
    col_ci, col_br = st.columns(2)
    ci_no = col_ci.text_input("CI Number", value=default['ci'])
    br_no = col_br.text_input("BR Number", value=default['br'])
    co_type = st.selectbox("Company Type", ["Private Company", "Public Company", "Company Limited by Guarantee"], index=["Private Company", "Public Company", "Company Limited by Guarantee"].index(default['type']))
    
    st.write("---")
    st.markdown("### 📝 Company Secretary Appointment (ND2A)")
    c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
    nd2a_eff = c1.date_input("Effective Date (Appt)", value=default['n2e'], key="n2e")
    nd2a_file = c2.date_input("Filing Date (ND2A)", value=default['n2f'], key="n2f")
    if nd2a_eff:
        c3.warning(f"Statutory Period: 15 days\n\n⚠️ Deadline: {nd2a_eff + timedelta(days=15)}")
    else: c3.info("Statutory Period: 15 days")
    nd2a_dl = c4.checkbox("Downloaded", value=default['n2d'], key="n2d")

    st.markdown("### 📝 Company Secretary Resignation (ND4)")
    r1, r2, r3, r4 = st.columns([2, 2, 2, 1])
    nd4_eff = r1.date_input("Effective Date (Resign)", value=default['n4e'], key="n4e")
    nd4_file = r2.date_input("Filing Date (ND4)", value=default['n4f'], key="n4f")
    if nd4_eff:
        r3.warning(f"Statutory Period: 15 days\n\n⚠️ Deadline: {nd4_eff + timedelta(days=15)}")
    else: r3.info("Statutory Period: 15 days")
    nd4_dl = r4.checkbox("Downloaded", value=default['n4d'], key="n4d")

    st.write("---")
    st.markdown("### 📍 Address & Contact")
    col_reg, col_cor = st.columns(2)
    reg_addr = col_reg.text_area("Registered Office Address", value=default['ra'])
    corres_addr = col_cor.text_area("Correspondence Address", value=default['ca'])
    
    st.markdown("### 🗄️ Seal Storage") 
    l1, l2, l3 = st.columns(3)
    round_l = l1.text_input("Round Chop Location", value=default['rl'])
    sign_l = l2.text_input("Signature Chop Location", value=default['sl'])
    common_l = l3.text_input("Common Seal Location", value=default['cl'])
    
    st.write("---")
    dis_date = st.date_input("Company Dissolution Date", value=default['dis'])
    
    # 按鈕邏輯
    if mode == "🆕 Add New":
        if st.button("Save To Records"):
            new_data = {'client_group': client_group, 'name_en': name_en, 'name_ch': name_ch, 'incorp_date': inc_date, 'incorp_place': inc_place, 'incorp_place_others': place_others, 'ci_no': ci_no, 'br_no': br_no, 'co_type': co_type, 'reg_addr': reg_addr, 'corres_addr': corres_addr, 'round_loc': round_l, 'sign_loc': sign_l, 'seal_loc': common_l, 'nd2a_eff_date': nd2a_eff, 'nd2a_file_date': nd2a_file, 'nd2a_download': str(nd2a_dl), 'nd4_eff_date': nd4_eff, 'nd4_file_date': nd4_file, 'nd4_download': str(nd4_dl), 'dissolution_date': dis_date}
            pd.DataFrame([new_data]).to_sql('companies', engine, if_exists='append', index=False)
            st.success("Saved!")
    else:
        if st.button("Update Record"):
            with engine.begin() as conn:
                conn.execute(text("""UPDATE companies SET client_group=:cg, name_en=:en, name_ch=:ch, incorp_date=:idate, incor
