import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta

# --- 1. 雲端連線 (核心修改，不影響介面) ---
try:
    DB_URL = st.secrets["DB_URL"]
    engine = create_engine(DB_URL)
except:
    st.error("❌ Secrets 未設定好 DB_URL")
    st.stop()

# 自動建立變更紀錄表
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

# --- 2. 介面設定 (跟返 V34) ---
st.set_page_config(page_title="Secretarial System V34", layout="wide")
st.sidebar.title("管理選單")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "⚙️ Group Management"])

if choice == "🏢 Company Register":
    st.header("🏢 Company Records Management")
    # 模式選擇
    mode = st.radio("模式選擇", ["🆕 新增公司", "✏️ 編輯現有公司"], horizontal=True)
    
    df_all = pd.read_sql("SELECT * FROM companies", engine)
    groups = pd.read_sql("SELECT group_name FROM client_groups", engine)['group_name'].tolist()
    
    # 預設資料
    default_data = {'group': "", 'en': "", 'ch': "", 'date': None, 'place': "HK", 'others': "", 'ci': "", 'br': ""}
    target_id = None

    if mode == "✏️ 編輯現有公司" and not df_all.empty:
        edit_target = st.selectbox("請選擇要修改的公司", df_all['name_en'].tolist())
        row = df_all[df_all['name_en'] == edit_target].iloc[0]
        target_id = row['id']
        default_data = {
            'group': row['client_group'], 'en': row['name_en'], 'ch': row['name_ch'],
            'date': row['incorp_date'], 'place': row['incorp_place'], 
            'others': row['incorp_place_others'], 'ci': row['ci_no'], 'br': row['br_no']
        }

    st.write("---")
    # 跟返 CR Form 標準排版，唔加任何廢話提示
    client_group = st.selectbox("Select Client Group", [""] + groups, index=(groups.index(default_data['group'])+1 if default_data['group'] in groups else 0))
    
    col1, col2 = st.columns(2)
    name_en = col1.text_input("Company English Name", value=default_data['en'])
    name_ch = col2.text_input("Company Chinese Name", value=default_data['ch'])
    
    col3, col4 = st.columns(2)
    inc_date = col3.date_input("Date of Incorporation", value=default_data['date'])
    
    place_list = ["HK", "BVI", "Cayman Island", "Others"]
    inc_place = col4.selectbox("Place of Incorporation", place_list, index=place_list.index(default_data['place']))
    
    place_others = st.text_input("Please specify country", value=default_data['others']) if inc_place == "Others" else ""
    
    st.write("---")
    col_ci, col_br = st.columns(2)
    ci_no = col_ci.text_input("CI Number", value=default_data['ci'])
    br_no = col_br.text_input("BR Number", value=default_data['br'])

    if mode == "🆕 新增公司":
        if st.button("💾 儲存資料"):
            new_data = {'client_group': client_group, 'name_en': name_en, 'name_ch': name_ch, 'incorp_date': inc_date, 'incorp_place': inc_place, 'incorp_place_others': place_others, 'ci_no': ci_no, 'br_no': br_no}
            pd.DataFrame([new_data]).to_sql('companies', engine, if_exists='append', index=False)
            st.success("儲存成功")
            st.rerun()
    else:
        if st.button("🆙 更新資料"):
            # 紀錄變更內容
            changes = []
            if name_en != default_data['en']: changes.append(f"EN: {default_data['en']} -> {name_en}")
            if ci_no != default_data['ci']: changes.append(f"CI: {default_data['ci']} -> {ci_no}")
            
            with engine.begin() as conn:
                conn.execute(text("UPDATE companies SET client_group=:cg, name_en=:en, name_ch=:ch, incorp_date=:dt, incorp_place=:pl, incorp_place_others=:oth, ci_no=:ci, br_no=:br WHERE id=:id"),
                    {"cg": client_group, "en": name_en, "ch": name_ch, "dt": inc_date, "pl": inc_place, "oth": place_others, "ci": ci_no, "br": br_no, "id": target_id})
                conn.execute(text("INSERT INTO audit_logs (company_name, action, change_details) VALUES (:name, 'UPDATE', :detail)"),
                    {"name": name_en, "detail": ", ".join(changes) if changes else "資料更新"})
            st.success("更新成功")
            st.rerun()

elif choice == "📊 Dashboard":
    st.header("📊 Master Dashboard")
    st.subheader("🏢 公司清單")
    st.dataframe(pd.read_sql("SELECT * FROM companies", engine), use_container_width=True)
    
    st.write("---")
    st.subheader("🕒 修改紀錄")
    log_df = pd.read_sql("SELECT company_name, action, change_details, changed_at FROM audit_logs ORDER BY changed_at DESC", engine)
    st.table(log_df)

elif choice == "⚙️ Group Management":
    st.header("⚙️ Group Management")
    new_g = st.text_input("New Group Name")
    if st.button("Add"):
        pd.DataFrame([{'group_name': new_g}]).to_sql('client_groups', engine, if_exists='append', index=False)
        st.success("Success")
        st.rerun()
