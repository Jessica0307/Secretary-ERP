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

# 確保雲端 Table 結構
with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS companies (
            id SERIAL PRIMARY KEY, client_group TEXT, name_en TEXT, name_ch TEXT, 
            incorp_date DATE, incorp_place TEXT, incorp_place_others TEXT, ci_no TEXT, br_no TEXT, co_type TEXT, 
            reg_addr TEXT, corres_addr TEXT, round_loc TEXT, sign_loc TEXT, seal_loc TEXT,
            nd2a_eff_date DATE, nd2a_file_date DATE, nd2a_download TEXT,
            nd4_eff_date DATE, nd4_file_date DATE, nd4_download TEXT,
            dissolution_date DATE, status TEXT DEFAULT 'Active'
        )
    """))
    conn.execute(text("CREATE TABLE IF NOT EXISTS client_groups (id SERIAL PRIMARY KEY, group_name TEXT UNIQUE)"))
    conn.execute(text("CREATE TABLE IF NOT EXISTS audit_logs (id SERIAL PRIMARY KEY, company_name TEXT, action TEXT, change_details TEXT, changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"))

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
                conn.execute(text("UPDATE companies SET client_group=:n WHERE client_group=:t"), {"n": new_name, "t": target_g})
            st.rerun()
        if col_del.button("⚠️ Delete"):
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM client_groups WHERE group_name=:t"), {"t": target_g})
            st.rerun()

# --- 4. Company Register (排版絕對鎖定 + 新增 Delete 功能) ---
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
        
        if 'id' in row: target_id = row['id']
        elif 'ID' in row: target_id = row['ID']
        else: target_id = row.name 
        
        d = {'cg': row['client_group'], 'en': row['name_en'], 'ch': row['name_ch'], 'idate': row['incorp_date'], 'place': row['incorp_place'], 'p_oth': row['incorp_place_others'], 'ci': row['ci_no'], 'br': row['br_no'], 'type': row['co_type'], 'ra': row['reg_addr'], 'ca': row['corres_addr'], 'rl': row['round_loc'], 'sl': row['sign_loc'], 'cl': row['seal_loc'], 'n2e': row['nd2a_eff_date'], 'n2f': row['nd2a_file_date'], 'n2d': str(row['nd2a_download']) == 'True', 'n4e': row['nd4_eff_date'], 'n4f': row['nd4_file_date'], 'n4d': str(row['nd4_download']) == 'True', 'dis': row['dissolution_date']}

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
    nd2a_dl = c4.checkbox("Downloaded", value=d['n2d'], key="n2d")

    st.markdown("### 📝 Company Secretary Resignation (ND4)")
    r1, r2, r3, r4 = st.columns([2, 2, 2, 1])
    nd4_eff = r1.date_input("Effective Date (Resign)", value=d['n4e'], key="n4e")
    nd4_file = r2.date_input("Filing Date (ND4)", value=d['n4f'], key="n4f")
    if nd4_eff:
        r3.warning(f"Statutory Period: 15 days\n\n⚠️ Deadline: {nd4_eff + timedelta(days=15)}")
    else: r3.info("Statutory Period: 15 days")
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
    
    if mode == "🆕 Add New":
        if st.button("Save To Records"):
            new_data = {'client_group': client_group, 'name_en': name_en, 'name_ch': name_ch, 'incorp_date': inc_date, 'incorp_place': inc_place, 'incorp_place_others': place_others, 'ci_no': ci_no, 'br_no': br_no, 'co_type': co_type, 'reg_addr': reg_addr, 'corres_addr': corres_addr, 'round_loc': round_l, 'sign_loc': sign_l, 'seal_loc': common_l, 'nd2a_eff_date': nd2a_eff, 'nd2a_file_date': nd2a_file, 'nd2a_download': str(nd2a_dl), 'nd4_eff_date': nd4_eff, 'nd4_file_date': nd4_file, 'nd4_download': str(nd4_dl), 'dissolution_date': dis_date}
            pd.DataFrame([new_data]).to_sql('companies', engine, if_exists='append', index=False)
            st.success("Saved!")
            st.rerun()
    else:
        # Edit 模式下的按鈕區 (排版跟返 Group Management)
        b_col1, b_col2 = st.columns(2)
        if b_col1.button("Update Record"):
            with engine.begin() as conn:
                sql = text("""
                    UPDATE companies SET 
                    client_group=:cg, name_en=:en, name_ch=:ch, incorp_date=:idate, 
                    incorp_place=:place, incorp_place_others=:p_oth, ci_no=:ci, br_no=:br, 
                    co_type=:type, reg_addr=:ra, corres_addr=:ca, round_loc=:rl, 
                    sign_loc=:sl, seal_loc=:cl, nd2a_eff_date=:n2e, nd2a_file_date=:n2f, 
                    nd2a_download=:n2d, nd4_eff_date=:n4e, nd4_file_date=:n4f, 
                    nd4_download=:n4d, dissolution_date=:dis 
                    WHERE id=:id
                """)
                conn.execute(sql, {"cg": client_group, "en": name_en, "ch": name_ch, "idate": inc_date, "place": inc_place, "p_oth": place_others, "ci": ci_no, "br": br_no, "type": co_type, "ra": reg_addr, "ca": corres_addr, "rl": round_l, "sl": sign_l, "cl": common_l, "n2e": nd2a_eff, "n2f": nd2a_file, "n2d": str(nd2a_dl), "n4e": nd4_eff, "n4f": nd4_file, "n4d": str(nd4_dl), "dis": dis_date, "id": target_id})
                conn.execute(text("INSERT INTO audit_logs (company_name, action, change_details) VALUES (:n, 'UPDATE', 'Manual Update')"), {"n": name_en})
            st.success("Updated!")
            st.rerun()
        
        # ⚠️ 新增 Delete 功能，方便你清理重複資料
        if b_col2.button("⚠️ Delete Record"):
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM companies WHERE id=:id"), {"id": target_id})
                conn.execute(text("INSERT INTO audit_logs (company_name, action, change_details) VALUES (:n, 'DELETE', 'Company Removed')"), {"n": name_en})
            st.warning("Company Deleted!")
            st.rerun()

# --- 5. Dashboard ---
elif choice == "📊 Dashboard":
    st.header("📊 Compliance Overview")
    df = pd.read_sql("SELECT * FROM companies", engine)
    st.dataframe(df, use_container_width=True)
    
    st.write("---")
    st.subheader("🕒 Audit Logs")
    logs = pd.read_sql("SELECT * FROM audit_logs ORDER BY changed_at DESC", engine)
    st.table(logs)
