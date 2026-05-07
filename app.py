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

# --- 2. Navigation (KEEP V34 Layout) ---
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
                # 兼容處理：無論欄位名是大寫還是細寫
                c_name = "group_name" if "group_name" in g_df.columns else "GROUP_NAME"
                conn.execute(text(f'UPDATE client_groups SET "{c_name}"=:n WHERE "{c_name}"=:t'), {"n": new_name, "t": target_g})
            st.rerun()
        if col_del.button("⚠️ Delete Group"):
            with engine.begin() as conn:
                c_name = "group_name" if "group_name" in g_df.columns else "GROUP_NAME"
                conn.execute(text(f'DELETE FROM client_groups WHERE "{c_name}"=:t'), {"t": target_g})
            st.rerun()

# --- 4. Company Register ---
elif choice == "🏢 Company Register":
    st.header("🏢 Company Records Management")
    mode = st.radio("Mode", ["🆕 Add New", "✏️ Edit Existing"], horizontal=True)
    
    df_all = pd.read_sql("SELECT * FROM companies", engine)
    groups = pd.read_sql("SELECT group_name FROM client_groups", engine)['group_name'].tolist()
    
    # 預設值
    d = {'cg': "", 'en': "", 'ch': "", 'idate': None, 'place': "HK", 'p_oth': "", 'ci': "", 'br': "", 'type': "Private Company", 'ra': "", 'ca': "", 'rl': "", 'sl': "", 'cl': "", 'n2e': None, 'n2f': None, 'n2d': False, 'n4e': None, 'n4f': None, 'n4d': False, 'dis': None}
    target_id = None

    if mode == "✏️ Edit Existing" and not df_all.empty:
        edit_target = st.selectbox("Select Company to Edit", df_all['name_en'].tolist())
        row = df_all[df_all['name_en'] == edit_target].iloc[0]
        
        # 【修正 KeyError 核心位】：嘗試多種方式獲取 ID
        target_id = row.get('id', row.get('ID', row.name))
        
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
    st.markdown("### 📝 ND2A Reminder")
    c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
    nd2a_eff = c1.date_input("Effective Date (Appt)", value=d['n2e'], key="n2e")
    nd2a_file = c2.date_input("Filing Date (ND2A)", value=d['n2f'], key="n2f")
    if nd2a_eff:
        c3.warning(f"Deadline: {nd2a_eff + timedelta(days=15)}")
    nd2a_dl = c4.checkbox("Downloaded", value=d['n2d'], key="n2d")

    st.markdown("### 📝 ND4 Reminder")
    r1, r2, r3, r4 = st.columns([2, 2, 2, 1])
    nd4_eff = r1.date_input("Effective Date (Resign)", value=d['n4e'], key="n4e")
    nd4_file = r2.date_input("Filing Date (ND4)", value=d['n4f'], key="n4f")
    if nd4_eff:
        r3.warning(f"Deadline: {nd4_eff + timedelta(days=15)}")
    nd4_dl = r4.checkbox("Downloaded", value=d['n4d'], key="n4d")

    st.write("---")
    st.markdown("### 📍 Address & Seal")
    col_reg, col_cor = st.columns(2)
    reg_addr = col_reg.text_area("Registered Office Address", value=d['ra'])
    corres_addr = col_cor.text_area("Correspondence Address", value=d['ca'])
    
    l1, l2, l3 = st.columns(3)
    round_l = l1.text_input("Round Chop", value=d['rl'])
    sign_l = l2.text_input("Signature Chop", value=d['sl'])
    common_l = l3.text_input("Common Seal", value=d['cl'])
    
    st.write("---")
    dis_date = st.date_input("Dissolution Date", value=d['dis'])
    
    if mode == "🆕 Add New":
        if st.button("💾 Save To Cloud"):
            new_data = {'client_group': client_group, 'name_en': name_en, 'name_ch': name_ch, 'incorp_date': inc_date, 'incorp_place': inc_place, 'incorp_place_others': place_others, 'ci_no': ci_no, 'br_no': br_no, 'co_type': co_type, 'reg_addr': reg_addr, 'corres_addr': corres_addr, 'round_loc': round_l, 'sign_loc': sign_l, 'seal_loc': common_l, 'nd2a_eff_date': nd2a_eff, 'nd2a_file_date': nd2a_file, 'nd2a_download': str(nd2a_dl), 'nd4_eff_date': nd4_eff, 'nd4_file_date': nd4_file, 'nd4_download': str(nd4_dl), 'dissolution_date': dis_date}
            pd.DataFrame([new_data]).to_sql('companies', engine, if_exists='append', index=False)
            st.success("Saved!")
            st.rerun()
    else:
        col_b1, col_b2 = st.columns(2)
        if col_b1.button("🆙 Update Record"):
            with engine.begin() as conn:
                # 嘗試偵測真正的 ID 欄位名
                id_name = "id" if "id" in df_all.columns else "ID"
                # 先刪除舊的，再新增新的 (避免手寫複雜的 Update SQL 報錯)
                conn.execute(text(f'DELETE FROM companies WHERE "{id_name}" = :id'), {"id": target_id})
                updated_data = {id_name: target_id, 'client_group': client_group, 'name_en': name_en, 'name_ch': name_ch, 'incorp_date': inc_date, 'incorp_place': inc_place, 'incorp_place_others': place_others, 'ci_no': ci_no, 'br_no': br_no, 'co_type': co_type, 'reg_addr': reg_addr, 'corres_addr': corres_addr, 'round_loc': round_l, 'sign_loc': sign_l, 'seal_loc': common_l, 'nd2a_eff_date': nd2a_eff, 'nd2a_file_date': nd2a_file, 'nd2a_download': str(nd2a_dl), 'nd4_eff_date': nd4_eff, 'nd4_file_date': nd4_file, 'nd4_download': str(nd4_dl), 'dissolution_date': dis_date}
                pd.DataFrame([updated_data]).to_sql('companies', engine, if_exists='append', index=False)
            st.success("Updated!")
            st.rerun()
            
        if col_b2.button("🔥 DELETE RECORD"):
            with engine.begin() as conn:
                id_name = "id" if "id" in df_all.columns else "ID"
                conn.execute(text(f'DELETE FROM companies WHERE "{id_name}" = :id'), {"id": target_id})
            st.warning("Deleted!")
            st.rerun()

# --- 5. Dashboard ---
elif choice == "📊 Dashboard":
    st.header("📊 Compliance Overview")
    df = pd.read_sql("SELECT * FROM companies", engine)
    st.dataframe(df, use_container_width=True)
