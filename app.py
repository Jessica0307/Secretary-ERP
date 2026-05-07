import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta

# --- 1. 連接設定 (LOCK: 不動) ---
try:
    DB_URL = st.secrets["DB_URL"]
    engine = create_engine(DB_URL)
except:
    st.error("❌ 請先在 Streamlit Secrets 填寫 DB_URL")
    st.stop()

# --- 2. 導航樣式還原 (左邊 Panel 模式) ---
st.set_page_config(page_title="Secretarial ERP V36", layout="wide")

# 還原左邊 Radio Button 導航
st.sidebar.title("選單")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "⚙️ Group Management"])

# --- 3. 功能邏輯 ---

if choice == "⚙️ Group Management":
    st.header("⚙️ Client Group Management")
    # ... (Group 管理邏輯保留)
    new_g = st.text_input("Add New Group Name")
    if st.button("Add Group"):
        try:
            with engine.connect() as conn:
                conn.execute(f"INSERT INTO client_groups (group_name) VALUES ('{new_g}')")
            st.rerun()
        except: st.error("Exists.")

elif choice == "🏢 Company Register":
    st.header("🏢 Company Records Management")
    
    # 1. Group 選擇
    existing_groups = pd.read_sql("SELECT group_name FROM client_groups", engine)['group_name'].tolist()
    client_group = st.selectbox("Select Client Group", [""] + existing_groups)
    
    # 2. 名稱並排
    col1, col2 = st.columns(2)
    name_en = col1.text_input("Company English Name")
    name_ch = col2.text_input("Company Chinese Name")
    
    # 3. 成立日期與地點
    col3, col4 = st.columns(2)
    inc_date = col3.date_input("Date of Incorporation")
    inc_place = col4.selectbox("Place of Incorporation", ["HK", "BVI", "Cayman Island", "Others"])
    
    # 【還原細節：Others 彈出輸入框】
    place_others = ""
    if inc_place == "Others":
        place_others = st.text_input("Please specify country (請註冊成立地名稱)")
    
    st.write("---")
    
    # 4. CI / BR 並排 (LOCK)
    col_ci, col_br = st.columns(2)
    ci_no = col_ci.text_input("CI Number")
    br_no = col_br.text_input("BR Number")
    
    # 5. 類型
    co_type = st.selectbox("Company Type", ["Private Company", "Public Company", "Limited by Guarantee"])
    
    st.write("---")
    
    # 6. ND2A / ND4 提醒位 (還原 15 日邏輯)
    st.markdown("### 📝 Statutory Filing Reminder")
    r1, r2, r3 = st.columns([2, 2, 2])
    n2_eff = r1.date_input("ND2A Effective Date", value=None)
    if n2_eff:
        # 法定 15 日計算
        deadline = n2_eff + timedelta(days=15)
        r3.warning(f"⚠️ ND2A Deadline: {deadline} (Statutory: 15 days)")
    
    st.write("---")
    
    # 7. 地址對開
    st.markdown("### 📍 Address")
    al, ar = st.columns(2)
    reg_addr = al.text_area("Registered Office Address")
    corres_addr = ar.text_area("Correspondence Address")
    
    if st.button("Save To Cloud"):
        # 儲存到雲端數據庫
        data = {
            'client_group': client_group, 'name_en': name_en, 'name_ch': name_ch,
            'incorp_date': inc_date, 'incorp_place': inc_place, 'incorp_place_others': place_others,
            'ci_no': ci_no, 'br_no': br_no, 'co_type': co_type, 
            'reg_addr': reg_addr, 'corres_addr': corres_addr
        }
        pd.DataFrame([data]).to_sql('companies', engine, if_exists='append', index=False)
        st.success("Successfully Saved!")

elif choice == "📊 Dashboard":
    st.header("📊 Master Cloud Dashboard")
    try:
        df = pd.read_sql("SELECT * FROM companies", engine)
        st.dataframe(df, use_container_width=True)
    except:
        st.info("No data found.")
