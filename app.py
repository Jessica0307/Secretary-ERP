import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import io

# --- 1. Database Connection (保持鎖定) ---
try:
    DB_URL = st.secrets["DB_URL"]
    engine = create_engine(DB_URL)
except:
    st.error("❌ Please check DB_URL in Secrets")
    st.stop()

# --- 2. Navigation (新增 Data Exchange) ---
st.set_page_config(page_title="ERP Cloud V34", layout="wide")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "⚙️ Group Management", "📤 Data Exchange"])

# 定義系統必填欄位 (用於 Upload 檢查)
REQUIRED_COLS = ["client_group", "name_en", "name_ch", "incorp_date", "incorp_place", "ci_no", "br_no", "co_type", "reg_addr", "corres_addr"]

# --- 3. Data Exchange (匯入/匯出功能) ---
if choice == "📤 Data Exchange":
    st.header("📤 Data Exchange & Backup")
    
    st.subheader("1. Download Template & Backup")
    col_ex1, col_ex2 = st.columns(2)
    
    # 範本欄位定義
    template_cols = ["client_group", "name_en", "name_ch", "incorp_date", "incorp_place", "incorp_place_others", "ci_no", "br_no", "co_type", "reg_addr", "corres_addr", "round_loc", "sign_loc", "seal_loc", "nd2a_eff_date", "nd2a_file_date", "nd2a_download", "nd4_eff_date", "nd4_file_date", "nd4_download", "dissolution_date"]
    
    # 空白範本下載
    tmp_df = pd.DataFrame(columns=template_cols)
    buffer_tmp = io.BytesIO()
    with pd.ExcelWriter(buffer_tmp, engine='xlsxwriter') as writer:
        tmp_df.to_excel(writer, index=False)
    
    col_ex1.download_button(label="📥 Download Blank Template", data=buffer_tmp.getvalue(), file_name="Company_Import_Template.xlsx", mime="application/vnd.ms-excel")

    # 全資料導出 (Backup)
    df_all_export = pd.read_sql("SELECT * FROM companies", engine)
    buffer_all = io.BytesIO()
    with pd.ExcelWriter(buffer_all, engine='xlsxwriter') as writer:
        df_all_export.to_excel(writer, index=False)
    
    col_ex2.download_button(label="📦 Export All Data (Backup)", data=buffer_all.getvalue(), file_name=f"Backup_{datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.ms-excel")

    st.write("---")
    st.subheader("2. Upload & Import Data")
    uploaded_file = st.file_uploader("Choose Excel File", type=["xlsx"])
    
    if uploaded_file:
        try:
            up_df = pd.read_excel(uploaded_file, engine='openpyxl') # 指定 openpyxl 避免 error
            st.write("Preview:")
            st.dataframe(up_df.head())
            
            if st.button("🚀 Confirm Upload"):
                error_logs = []
                # 簡單檢查欄位名稱
                for col in REQUIRED_COLS:
                    if col not in up_df.columns:
                        st.error(f"❌ 檔案格式不符，缺少必要欄位: {col}")
                        st.stop()
                
                # 逐行必填檢查
                for i, row in up_df.iterrows():
                    missing = [c for c in REQUIRED_COLS if pd.isna(row[c]) or str(row[c]).strip() == ""]
                    if missing:
                        error_logs.append(f"第 {i+2} 行: 缺少 {', '.join(missing)}")
                
                if error_logs:
                    st.error("❌ 上傳攔截：請修正以下必填項")
                    for log in error_logs[:5]: st.write(log)
                else:
                    up_df.to_sql('companies', engine, if_exists='append', index=False)
                    st.success("✅ 匯入成功！")
                    st.rerun()
        except Exception as e:
            st.error(f"讀取失敗: {e}")

# --- 4. Company Register (100% 回復第 23 版邏輯) ---
elif choice == "🏢 Company Register":
    st.header("🏢 Company Records Management")
    mode = st.radio("Mode", ["🆕 Add New", "✏️ Edit Existing", "📋 Copy Existing"], horizontal=True)
    df_all = pd.read_sql("SELECT * FROM companies", engine)
    groups = pd.read_sql("SELECT group_name FROM client_groups", engine)['group_name'].tolist()
    d = {'cg': "", 'en': "", 'ch': "", 'idate': None, 'place': "", 'p_oth': "", 'ci': "", 'br': "", 'type': "", 'ra': "", 'ca': "", 'rl': "", 'sl': "", 'cl': "", 'n2e': None, 'n2f': None, 'n2d': False, 'n4e': None, 'n4f': None, 'n4d': False, 'dis': None}
    target_name = None

    if mode in ["✏️ Edit Existing", "📋 Copy Existing"] and not df_all.empty:
        comp_list = [""] + df_all['name_en'].tolist()
        target_name = st.selectbox("Select Company", comp_list)
        if target_name != "":
            row = df_all[df_all['name_en'] == target_name].iloc[0]
            d = {'cg': row.get('client_group', ""), 'en': row.get('name_en', ""), 'ch': row.get('name_ch', ""), 'idate': row.get('incorp_date'), 'place': row.get('incorp_place', ""), 'p_oth': row.get('incorp_place_others', ""), 'ci': row.get('ci_no', ""), 'br': row.get('br_no', ""), 'type': row.get('co_type', ""), 'ra': row.get('reg_addr', ""), 'ca': row.get('corres_addr', ""), 'rl': row.get('round_loc', ""), 'sl': row.get('sign_loc', ""), 'cl': row.get('seal_loc', ""), 'n2e': row.get('nd2a_eff_date'), 'n2f': row.get('nd2a_file_date'), 'n2d': str(row.get('nd2a_download', "")) == 'True', 'n4e': row.get('nd4_eff_date'), 'n4f': row.get('nd4_file_date'), 'n4d': str(row.get('nd4_download', "")) == 'True', 'dis': row.get('dissolution_date')}
            if mode == "📋 Copy Existing": d['en'], d['ch'] = "", ""

    st.markdown("### General Information")
    def red_label(text, value):
        return f":red[⚠️ {text} (Required!)]" if not value or str(value).strip() == "" or value is None else text

    client_group = st.selectbox(red_label("Select Client Group", d['cg']), [""] + groups, index=(groups.index(d['cg'])+1 if d['cg'] in groups else 0))
    col1, col2 = st.columns(2)
    name_en = col1.text_input(red_label("Company English Name", d['en']), value=d['en'])
    name_ch = col2.text_input(red_label("Company Chinese Name", d['ch']), value=d['ch'])
    col3, col4 = st.columns(2)
    inc_date = col3.date_input(red_label("Date of Incorporation", d['idate']), value=d['idate'])
    places = ["", "HK", "BVI", "Cayman Island", "Others"]
    inc_place = col4.selectbox(red_label("Place of Incorporation", d['place']), places, index=places.index(d['place']) if d['place'] in places else 0)
    place_others = st.text_input(red_label("Specify Country", d['p_oth']), value=d['p_oth']) if inc_place == "Others" else ""

    st.write("---")
    col_ci, col_br = st.columns(2)
    ci_no = col_ci.text_input(red_label("CI Number", d['ci']), value=d['ci'])
    br_no = col_br.text_input(red_label("BR Number", d['br']), value=d['br'])
    types = ["", "Private Company", "Public Company", "Company Limited by Guarantee"]
    co_type = st.selectbox(red_label("Company Type", d['type']), types, index=types.index(d['type']) if d['type'] in types else 0)

    st.write("---")
    st.markdown("### 📝 ND2A & ND4 (15-Day Logic)")
    c1, c2, c3 = st.columns([2,2,2])
    nd2a_eff = c1.date_input("ND2A Effective Date", value=d['n2e'])
    if nd2a_eff: c3.warning(f"ND2A Deadline: {nd2a_eff + timedelta(days=15)}")
    r1, r2, r3 = st.columns([2,2,2])
    nd4_eff = r1.date_input("ND4 Effective Date", value=d['n4e'])
    if nd4_eff: r3.warning(f"ND4 Deadline: {nd4_eff + timedelta(days=15)}")

    st.write("---")
    reg_addr = st.text_area(red_label("Registered Office Address", d['ra']), value=d['ra'])
    corres_addr = st.text_area(red_label("Correspondence Address", d['ca']), value=d['ca'])
    
    l1, l2, l3 = st.columns(3)
    round_l = l1.text_input(red_label("Round Chop", d['rl']), value=d['rl'])
    sign_l = l2.text_input(red_label("Signature Chop", d['sl']), value=d['sl'])
    common_l = l3.text_input(red_label("Common Seal", d['cl']), value=d['cl'])

    required_fields = {"Group": client_group, "EN": name_en, "CH": name_ch, "Date": inc_date, "Place": inc_place, "CI": ci_no, "BR": br_no, "Type": co_type, "RegAddr": reg_addr, "CorAddr": corres_addr, "Round": round_l, "Sign": sign_l, "Seal": common_l}
    if inc_place == "Others": required_fields["Country"] = place_others

    def check_all():
        empty = [k for k, v in required_fields.items() if not v or str(v).strip() == "" or v is None]
        if empty: st.error(f"❌ 未填寫: {', '.join(empty)}"); return False
        return True

    if mode in ["🆕 Add New", "📋 Copy Existing"]:
        if st.button("💾 Save Record"):
            if check_all():
                new_row = {'client_group': client_group, 'name_en': name_en, 'name_ch': name_ch, 'incorp_date': inc_date, 'incorp_place': inc_place, 'incorp_place_others': place_others, 'ci_no': ci_no, 'br_no': br_no, 'co_type': co_type, 'reg_addr': reg_addr, 'corres_addr': corres_addr, 'round_loc': round_l, 'sign_loc': sign_l, 'seal_loc': common_l, 'nd2a_eff_date': nd2a_eff, 'nd4_eff_date': nd4_eff}
                pd.DataFrame([new_row]).to_sql('companies', engine, if_exists='append', index=False)
                st.success("Saved!"); st.rerun()
    else:
        if st.button("🆙 Update Record"):
            if check_all():
                df_new = df_all[df_all['name_en'] != target_name]
                up_row = {'client_group': client_group, 'name_en': name_en, 'name_ch': name_ch, 'incorp_date': inc_date, 'incorp_place': inc_place, 'incorp_place_others': place_others, 'ci_no': ci_no, 'br_no': br_no, 'co_type': co_type, 'reg_addr': reg_addr, 'corres_addr': corres_addr, 'round_loc': round_l, 'sign_loc': sign_l, 'seal_loc': common_l, 'nd2a_eff_date': nd2a_eff, 'nd4_eff_date': nd4_eff}
                pd.concat([df_new, pd.DataFrame([up_row])]).to_sql('companies', engine, if_exists='replace', index=False)
                st.success("Updated!"); st.rerun()

# --- 5. Dashboard & Group Management (略) ---
elif choice == "📊 Dashboard":
    st.header("📊 Compliance Overview")
    df = pd.read_sql("SELECT * FROM companies", engine)
    st.dataframe(df, use_container_width=True)

elif choice == "⚙️ Group Management":
    st.header("⚙️ Group Management")
    new_g = st.text_input("New Group Name")
    if st.button("Add"):
        pd.DataFrame([{'group_name': new_g}]).to_sql('client_groups', engine, if_exists='append', index=False)
        st.rerun()
