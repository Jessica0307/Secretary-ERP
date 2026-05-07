import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta

# --- 1. 數據庫連接 (LOCK) ---
try:
    DB_URL = st.secrets["DB_URL"]
    engine = create_engine(DB_URL)
except:
    st.error("❌ 未偵測到 Secrets 設定，請在 Streamlit Cloud 設定 DB_URL")
    st.stop()

# 初始化表格
def init_db():
    with engine.connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id SERIAL PRIMARY KEY, client_group TEXT, name_en TEXT, name_ch TEXT, 
                incorp_date DATE, incorp_place TEXT, ci_no TEXT, br_no TEXT, co_type TEXT, 
                reg_addr TEXT, corres_addr TEXT, round_loc TEXT, sign_l TEXT, common_l TEXT,
                nd2a_eff_date DATE, nd2a_file_date DATE, nd2a_download TEXT,
                nd4_eff_date DATE, nd4_file_date DATE, nd4_download TEXT,
                dissolution_date DATE
            )
        """)
        conn.execute("CREATE TABLE IF NOT EXISTS client_groups (id SERIAL PRIMARY KEY, group_name TEXT UNIQUE)")

init_db()

# --- 2. 介面設定 ---
st.set_page_config(page_title="Company Records Management", layout="wide")

# 側邊欄導航
choice = st.sidebar.radio("Navigation", ["🏢 Company Register", "📊 Dashboard", "⚙️ Group Management"])

if choice == "🏢 Company Register":
    st.header("🏢 Company Records Management")
    
    # --- General Information ---
    st.subheader("General Information")
    existing_groups = pd.read_sql("SELECT group_name FROM client_groups", engine)['group_name'].tolist()
    client_group = st.selectbox("Select Client Group", [""] + existing_groups)
    
    col1, col2 = st.columns(2)
    name_en = col1.text_input("Company English Name")
    name_ch = col2.text_input("Company Chinese Name")
    
    col3, col4 = st.columns(2)
    inc_date = col3.date_input("Date of Incorporation", value=datetime.now())
    inc_place = col4.selectbox("Place of Incorporation", ["HK", "BVI", "Cayman Island", "Others"])
    
    st.write("---")
    # CI/BR 左右排版
    col_ci, col_br = st.columns(2)
    ci_no = col_ci.text_input("CI Number")
    br_no = col_br.text_input("BR Number")
    
    co_type = st.selectbox("Company Type", ["Private Company", "Public Company", "Company Limited by Guarantee"])
    
    st.write("---")
    
    # --- ND2A Section ---
    st.subheader("📝 Company Secretary Appointment (ND2A)")
    c1, c2, c3, c4 = st.columns([2.5, 2.5, 3, 1])
    n2_eff = c1.date_input("Effective Date (Appt)", value=None, key="n2e")
    n2_file = c2.date_input("Filing Date (ND2A)", value=None, key="n2f")
    if n2_eff:
        c3.info(f"Statutory Period: 15 days\n\n⚠️ Deadline: {n2_eff + timedelta(days=15)}")
    else:
        c3.info("Statutory Period: 15 days")
    n2_dl = c4.checkbox("Downloaded", key="n2d")

    # --- ND4 Section ---
    st.subheader("📝 Company Secretary Resignation (ND4)")
    r1, r2, r3, r4 = st.columns([2.5, 2.5, 3, 1])
    n4_eff = r1.date_input("Effective Date (Resign)", value=None, key="n4e")
    n4_file = r2.date_input("Filing Date (ND4)", value=None, key="n4f")
    if n4_eff:
        r3.info(f"Statutory Period: 15 days\n\n⚠️ Deadline: {n4_eff + timedelta(days=15)}")
    else:
        r3.info("Statutory Period: 15 days")
    n4_dl = r4.checkbox("Downloaded", key="n4d")

    st.write("---")
    
    # --- Address & Contact ---
    st.subheader("📍 Address & Contact")
    al, ar = st.columns(2)
    reg_addr = al.text_area("Registered Office Address")
    corres_addr = ar.text_area("Correspondence Address")
    
    # --- Seal Storage ---
    st.subheader("🗄️ Seal Storage")
    s1, s2, s3 = st.columns(3)
    round_l = s1.text_input("Round Chop Location")
    sign_l = s2.text_input("Signature Chop Location")
    common_l = s3.text_input("Common Seal Location")
    
    st.write("---")
    dis_date = st.date_input("Company Dissolution Date", value=None)
    
    if st.button("Save To Records"):
        data = {
            'client_group': client_group, 'name_en': name_en, 'name_ch': name_ch,
            'incorp_date': inc_date, 'incorp_place': inc_place, 'ci_no': ci_no, 'br_no': br_no,
            'co_type': co_type, 'reg_addr': reg_addr, 'corres_addr': corres_addr,
            'round_loc': round_l, 'sign_l': sign_l, 'common_l': common_l,
            'nd2a_eff_date': n2_eff, 'nd2a_file_date': n2_file, 'nd2a_download': str(n2_dl),
            'nd4_eff_date': n4_eff, 'nd4_file_date': n4_file, 'nd4_download': str(n4_dl),
            'dissolution_date': dis_date
        }
        pd.DataFrame([data]).to_sql('companies', engine, if_exists='append', index=False)
        st.success("✅ Record Successfully Saved to Cloud!")

elif choice == "📊 Dashboard":
    st.header("📊 Master Dashboard")
    df = pd.read_sql("SELECT * FROM companies", engine)
    st.dataframe(df, use_container_width=True)

elif choice == "⚙️ Group Management":
    st.header("⚙️ Group Management")
    new_g = st.text_input("Add New Group Name")
    if st.button("Add"):
        try:
            pd.DataFrame([{'group_name': new_g}]).to_sql('client_groups', engine, if_exists='append', index=False)
            st.rerun()
        except: st.error("Group already exists.")
