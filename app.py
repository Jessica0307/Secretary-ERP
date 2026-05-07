import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta

# --- 1. 雲端連線設定 (LOCK: 不動) ---
try:
    DB_URL = st.secrets["DB_URL"]
    engine = create_engine(DB_URL)
except:
    st.error("❌ 請先在 Streamlit Secrets 填寫 DB_URL")
    st.stop()

# --- 2. 介面設定 ---
st.set_page_config(page_title="Secretarial ERP", layout="wide")

# --- 3. 左邊選單還原 (跟足圖入面嘅 Emoji 同名) ---
st.sidebar.markdown("### Navigation")
choice = st.sidebar.radio(
    label="Navigation Options",
    options=["📊 Dashboard", "🏢 Company Register", "📜 Statutory Registers", "⚙️ Group Management"],
    label_visibility="collapsed"
)

# --- 4. 功能邏輯 ---

if choice == "🏢 Company Register":
    # 標題與圖示 (跟足圖中格式)
    st.markdown("## 🏢 Company Records Management")
    st.markdown("### General Information")
    
    # 讀取現有集團
    existing_groups = pd.read_sql("SELECT group_name FROM client_groups", engine)['group_name'].tolist()
    
    # Select Client Group (單獨一行)
    client_group = st.selectbox("Select Client Group", [""] + existing_groups)
    
    # 名稱並排 (兩格)
    col1, col2 = st.columns(2)
    name_en = col1.text_input("Company English Name")
    name_ch = col2.text_input("Company Chinese Name")
    
    # 成立日期與地點 (兩格)
    col3, col4 = st.columns(2)
    inc_date = col3.date_input("Date of Incorporation", value=datetime.today())
    inc_place = col4.selectbox("Place of Incorporation", ["HK", "BVI", "Cayman Island", "Others"])
    
    # 【重點還原】如果係 Others，顯示 Specify Country (單獨一行)
    place_others = ""
    if inc_place == "Others":
        place_others = st.text_input("Specify Country")
    
    # 分割線 (跟足圖中粗細)
    st.write("---")
    
    # CI / BR Number 並排
    col_ci, col_br = st.columns(2)
    ci_no = col_ci.text_input("CI Number")
    br_no = col_br.text_input("BR Number")

    # 儲存按鈕
    if st.button("Save Records"):
        data = {
            'client_group': client_group, 'name_en': name_en, 'name_ch': name_ch,
            'incorp_date': inc_date, 'incorp_place': inc_place, 'incorp_place_others': place_others,
            'ci_no': ci_no, 'br_no': br_no
        }
        pd.DataFrame([data]).to_sql('companies', engine, if_exists='append', index=False)
        st.success("Successfully Saved to Cloud!")

elif choice == "📊 Dashboard":
    st.header("📊 Master Dashboard")
    try:
        df = pd.read_sql("SELECT * FROM companies", engine)
        st.dataframe(df, use_container_width=True)
    except:
        st.info("暫時未有資料。")

elif choice == "⚙️ Group Management":
    st.header("⚙️ Group Management")
    new_g = st.text_input("Add New Group")
    if st.button("Add"):
        pd.DataFrame([{'group_name': new_g}]).to_sql('client_groups', engine, if_exists='append', index=False)
        st.rerun()

elif choice == "📜 Statutory Registers":
    st.header("📜 Statutory Registers")
    st.info("此模組開發中，排版將與 V35 保持一致。")
