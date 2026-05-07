import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta

# --- 1. 雲端連線 (只准改這部分，介面絕不動) ---
try:
    DB_URL = st.secrets["DB_URL"]
    engine = create_engine(DB_URL)
except:
    st.error("❌ Secrets 未設定好 DB_URL")
    st.stop()

# --- 2. V34 介面還原 (Wide Mode) ---
st.set_page_config(page_title="Secretarial System V34", layout="wide")

# --- 3. 還原 V34 左邊 Panel 導航 ---
st.sidebar.title("管理選單")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "⚙️ Group Management"])

# --- 4. 內容分頁 ---

if choice == "⚙️ Group Management":
    st.header("⚙️ Group Management")
    new_group = st.text_input("Add New Group Name")
    if st.button("Add"):
        try:
            # 直接存入雲端
            pd.DataFrame([{'group_name': new_group}]).to_sql('client_groups', engine, if_exists='append', index=False)
            st.success(f"Group '{new_group}' Added!")
            st.rerun()
        except:
            st.error("Error: Group might already exist.")

elif choice == "🏢 Company Register":
    st.header("🏢 Company Records Management")
    
    # 讀取 Group 列表
    try:
        existing_groups = pd.read_sql("SELECT group_name FROM client_groups", engine)['group_name'].tolist()
    except:
        existing_groups = []
    
    client_group = st.selectbox("Select Client Group", [""] + existing_groups)
    
    # 【還原 V34 佈局】左右並排
    col1, col2 = st.columns(2)
    name_en = col1.text_input("Company English Name")
    name_ch = col2.text_input("Company Chinese Name")
    
    col3, col4 = st.columns(2)
    inc_date = col3.date_input("Date of Incorporation")
    
    # 【還原 V34 佈局】Others 彈出邏輯
    inc_place = col4.selectbox("Place of Incorporation", ["HK", "BVI", "Cayman Island", "Others"])
    place_others = ""
    if inc_place == "Others":
        place_others = st.text_input("Please specify country")
    
    st.write("---")
    
    # 【還原 V34 佈局】CI/BR 並排
    col_ci, col_br = st.columns(2)
    ci_no = col_ci.text_input("CI Number")
    br_no = col_br.text_input("BR Number")
    
    # 【還原 V34 佈局】ND2A 15日提醒
    st.write("---")
    st.markdown("### 📝 Statutory Filing Reminder")
    r1, r2, r3 = st.columns([2, 2, 2])
    n2_eff = r1.date_input("ND2A Effective Date", value=None)
    if n2_eff:
        # 法定 15 日計數
        deadline = n2_eff + timedelta(days=15)
        r3.warning(f"⚠️ ND2A Deadline: {deadline} (Statutory: 15 days)")

    # 儲存
    if st.button("Save To Cloud"):
        # 準備資料
        data = {
            'client_group': client_group,
            'name_en': name_en,
            'name_ch': name_ch,
            'incorp_date': inc_date,
            'incorp_place': inc_place,
            'incorp_place_others': place_others,
            'ci_no': ci_no,
            'br_no': br_no
        }
        pd.DataFrame([data]).to_sql('companies', engine, if_exists='append', index=False)
        st.success("Data Saved to Cloud Successfully!")

elif choice == "📊 Dashboard":
    st.header("📊 Master Dashboard")
    try:
        # 從雲端讀取顯示
        df = pd.read_sql("SELECT * FROM companies", engine)
        st.dataframe(df, use_container_width=True)
    except:
        st.info("No data found in cloud database.")
