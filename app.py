import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta

# 1. 直接讀取雲端密鑰
try:
    DB_URL = st.secrets["DB_URL"]
    engine = create_engine(DB_URL)
except:
    st.error("❌ 未偵測到 Secrets 設定，請在 Streamlit Cloud 設定 DB_URL")
    st.stop()

# 2. UI 分頁鎖定
st.set_page_config(page_title="ERP V36 Cloud", layout="wide")
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🏢 Company Register", "⚙️ Group Management"])

with tab3:
    st.header("⚙️ Group Management")
    new_g = st.text_input("New Group Name")
    if st.button("Add"):
        pd.DataFrame([{'group_name': new_g}]).to_sql('client_groups', engine, if_exists='append', index=False)
        st.success("Added!")

with tab2:
    st.header("🏢 Company Register")
    col1, col2 = st.columns(2)
    name_en = col1.text_input("English Name")
    name_ch = col2.text_input("中文名稱")
    ci_no = col1.text_input("CI No")
    br_no = col2.text_input("BR No")
    if st.button("Save"):
        data = {'name_en': name_en, 'name_ch': name_ch, 'ci_no': ci_no, 'br_no': br_no}
        pd.DataFrame([data]).to_sql('companies', engine, if_exists='append', index=False)
        st.success("Saved!")

with tab1:
    st.header("📊 Master Dashboard")
    try:
        df = pd.read_sql("SELECT * FROM companies", engine)
        st.dataframe(df, use_container_width=True)
    except:
        st.info("暫時未有公司資料")
