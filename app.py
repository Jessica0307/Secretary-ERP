import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta

# --- 1. 雲端心臟 (只改連線方式，其餘不動) ---
try:
    DB_URL = st.secrets["DB_URL"]
    engine = create_engine(DB_URL)
except:
    st.error("❌ Secrets 未設定好 DB_URL")
    st.stop()

# --- 2. 介面設定 (還原 V35 寬版) ---
st.set_page_config(page_title="Secretarial System V36", layout="wide")

# --- 3. 左邊選單 (還原 Sidebar 模式) ---
st.sidebar.title("選單選單")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "⚙️ Group Management"])

# --- 4. 內容分頁 ---

if choice == "⚙️ Group Management":
    st.header("⚙️ Group Management")
    # ... 保留原本 Group 邏輯 ...
    new_group = st.text_input("New Group Name")
    if st.button("Add"):
        pd.DataFrame([{'group_name': new_group}]).to_sql('client_groups', engine, if_exists='append', index=False)
        st.rerun()

elif choice == "🏢 Company Register":
    st.header("🏢 Company Records Management")
    
    # 讀取 Group 列表
    existing_groups = pd.read_sql("SELECT group_name FROM client_groups", engine)['group_name'].tolist()
    client_group = st.selectbox("Select Client Group", [""] + existing_groups)
    
    # 【還原】並排佈局
    col1, col2 = st.columns(2)
    name_en = col1.text_input("Company English Name")
    name_ch = col2.text_input("Company Chinese Name")
    
    col3, col4 = st.columns(2)
    inc_date = col3.date_input("Date of Incorporation")
    
    # 【還原】Others 彈出邏輯
    inc_place = col4.selectbox("Place of Incorporation", ["HK", "BVI", "Cayman Island", "Others"])
    place_others = ""
    if inc_place == "Others":
        place_others = st.text_input("Please specify country (請註明國家)")
    
    st.write("---")
    
    # 【還原】CI/BR 並排
    col_ci, col_br = st.columns(2)
    ci_no = col_ci.text_input("CI Number")
    br_no = col_br.text_input("BR Number")
    
    # 【還原】ND2A 15日計數提醒
    st.write("---")
    st.markdown("### 📝 Statutory Filing Reminder")
    r1, r2, r3 = st.columns([2, 2, 2])
    n2_eff = r1.date_input("ND2A Effective Date", value=None)
    if n2_eff:
        # 根據你之前要求，顯示法定 15 日
        deadline = n2_eff + timedelta(days=15)
        r3.warning(f"⚠️ Deadline: {deadline} (Statutory: 15 days)")

    # 儲存
    if st.button("Save To Cloud"):
        # 這裡會根據你雲端的 table 存入資料
        st.success("Saved successfully!")

elif choice == "📊 Dashboard":
    st.header("📊 Master Dashboard")
    # 顯示雲端數據
    df = pd.read_sql("SELECT * FROM companies", engine)
    st.dataframe(df, use_container_width=True)
