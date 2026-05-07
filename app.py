import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta

# --- 1. 雲端連線設定 (LOCK: 不動) ---
try:
    DB_URL = st.secrets["DB_URL"]
    engine = create_engine(DB_URL)
except:
    st.error("❌ 請在 Streamlit Secrets 填寫正確的 DB_URL")
    st.stop()

# --- 2. 介面設定 ---
st.set_page_config(page_title="Secretarial ERP V34", layout="wide")

st.sidebar.title("管理選單")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "⚙️ Group Management"])

# --- 3. 邏輯區 ---

if choice == "⚙️ Group Management":
    st.header("⚙️ Client Group Management")
    new_g = st.text_input("新增集團名稱")
    if st.button("新增"):
        pd.DataFrame([{'group_name': new_g}]).to_sql('client_groups', engine, if_exists='append', index=False)
        st.success("已新增")
        st.rerun()

elif choice == "🏢 Company Register":
    st.header("🏢 新增公司資料")
    
    # 讀取 Group 列表
    groups = pd.read_sql("SELECT group_name FROM client_groups", engine)['group_name'].tolist()
    client_group = st.selectbox("Select Client Group", [""] + groups)
    
    col1, col2 = st.columns(2)
    name_en = col1.text_input("Company English Name")
    name_ch = col2.text_input("Company Chinese Name")
    
    col3, col4 = st.columns(2)
    # 【解決方案 1】：日期改為 value=None，方便你直接喺格內打數字 (例如 2024-05-01)
    inc_date = col3.date_input("Date of Incorporation (可直接鍵盤輸入)", value=None)
    inc_place = col4.selectbox("Place of Incorporation", ["HK", "BVI", "Cayman Island", "Others"])
    
    place_others = ""
    if inc_place == "Others":
        place_others = st.text_input("Please specify country")
    
    st.write("---")
    col_ci, col_br = st.columns(2)
    ci_no = col_ci.text_input("CI Number")
    br_no = col_br.text_input("BR Number")
    
    if st.button("💾 儲存新資料"):
        data = {
            'client_group': client_group, 'name_en': name_en, 'name_ch': name_ch,
            'incorp_date': inc_date, 'incorp_place': inc_place, 'incorp_place_others': place_others,
            'ci_no': ci_no, 'br_no': br_no
        }
        pd.DataFrame([data]).to_sql('companies', engine, if_exists='append', index=False)
        st.success("成功儲存到雲端！")

elif choice == "📊 Dashboard":
    st.header("📊 Master Dashboard & Edit")
    
    # 讀取所有資料
    df = pd.read_sql("SELECT * FROM companies", engine)
    st.dataframe(df, use_container_width=True)
    
    st.write("---")
    
    # 【解決方案 2】：加入 Edit 功能
    st.subheader("📝 編輯現有資料 (Edit Record)")
    
    if not df.empty:
        # 俾你揀邊一間公司嚟改 (用 ID 嚟認)
        edit_id = st.selectbox("請選擇要編輯的公司 ID", df['id'].tolist())
        
        # 撳掣後讀取該筆資料入 Form
        target_row = df[df['id'] == edit_id].iloc[0]
        
        with st.expander("打開編輯表單"):
            new_en = st.text_input("修改英文名", value=target_row['name_en'])
            new_ch = st.text_input("修改中文名", value=target_row['name_ch'])
            new_ci = st.text_input("修改 CI No.", value=target_row['ci_no'])
            new_br = st.text_input("修改 BR No.", value=target_row['br_no'])
            
            if st.button("更新雲端資料"):
                with engine.begin() as conn:
                    query = text("""
                        UPDATE companies 
                        SET name_en = :en, name_ch = :ch, ci_no = :ci, br_no = :br 
                        WHERE id = :id
                    """)
                    conn.execute(query, {"en": new_en, "ch": new_ch, "ci": new_ci, "br": new_br, "id": edit_id})
                st.success(f"ID {edit_id} 已更新！")
                st.rerun()
    else:
        st.info("目前沒有資料可以編輯。")
