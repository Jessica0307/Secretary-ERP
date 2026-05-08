import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import io

# --- 1. Database Connection ---
try:
    DB_URL = st.secrets["DB_URL"]
    engine = create_engine(DB_URL)
except:
    st.error("❌ Please check DB_URL in Secrets")
    st.stop()

# --- 2. Navigation (LOCK V23 Layout) ---
st.set_page_config(page_title="ERP Cloud V34", layout="wide")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "⚙️ Group Management", "📤 Data Exchange"])

# 定義必填欄位 (用於上傳驗證)
REQUIRED_COLS = ["client_group", "name_en", "name_ch", "incorp_date", "incorp_place", "ci_no", "br_no", "co_type", "reg_addr", "corres_addr", "round_loc", "sign_loc", "seal_loc"]

# --- 3. Data Exchange (解決日期格式與 N/A 豁免) ---
if choice == "📤 Data Exchange":
    st.header("📤 Data Exchange & Backup")
    
    st.subheader("1. Download & Backup")
    col_ex1, col_ex2 = st.columns(2)
    
    template_cols = ["client_group", "name_en", "name_ch", "incorp_date", "incorp_place", "incorp_place_others", "ci_no", "br_no", "co_type", "reg_addr", "corres_addr", "round_loc", "sign_loc", "seal_loc", "nd2a_eff_date", "nd2a_file_date", "nd2a_download", "nd4_eff_date", "nd4_file_date", "nd4_download", "dissolution_date"]
    
    # 下載空白範本
    tmp_df = pd.DataFrame(columns=template_cols)
    buffer_tmp = io.BytesIO()
    with pd.ExcelWriter(buffer_tmp, engine='xlsxwriter') as writer:
        tmp_df.to_excel(writer, index=False)
    col_ex1.download_button(label="📥 Download Blank Template", data=buffer_tmp.getvalue(), file_name="Company_Record_Template.xlsx", mime="application/vnd.ms-excel")

    # 備份 (Export)
    df_all_export = pd.read_sql("SELECT * FROM companies", engine)
    buffer_all = io.BytesIO()
    with pd.ExcelWriter(buffer_all, engine='xlsxwriter') as writer:
        df_all_export.to_excel(writer, index=False)
    col_ex2.download_button(label="📦 Export All Data (Backup)", data=buffer_all.getvalue(), file_name=f"Full_Backup_{datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.ms-excel")

    st.write("---")
    st.subheader("2. Upload & Bulk Import")
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
    
    if uploaded_file:
        try:
            # 讀取 Excel
            up_df = pd.read_excel(uploaded_file, engine='openpyxl', keep_default_na=False)
            st.write("Preview (First 5 rows):")
            st.dataframe(up_df.head())
            
            if st.button("🚀 Confirm Upload to Cloud"):
                # A. 深度清洗日期欄位，防止 InvalidDatetimeFormat 錯誤
                date_cols = ["incorp_date", "nd2a_eff_date", "nd2a_file_date", "nd4_eff_date", "nd4_file_date", "dissolution_date"]
                for col in date_cols:
                    if col in up_df.columns:
                        # 將空白字串或 n/a 字眼轉為真正的 NaT (NULL)
                        up_df[col] = up_df[col].apply(lambda x: None if str(x).strip().lower() in ["", "nan", "n/a", "none", "nil"] else x)
                        up_df[col] = pd.to_datetime(up_df[col], errors='coerce')

                # B. 必填檢查
                error_logs = []
                for i, row in up_df.iterrows():
                    missing = []
                    for c in REQUIRED_COLS:
                        val = row[c]
                        # 檢查：如果是空值 (NaN/NaT) 或空白字串，就報錯
                        if pd.isna(val) or str(val).strip() == "":
                            missing.append(c)
                    if missing:
                        error_logs.append(f"Row {i+2}: 缺少 {', '.join(missing)}")
                
                if error_logs:
                    st.error("❌ 上傳攔截：有必填格仔未填 (或格式錯誤)")
                    for log in error_logs[:10]: st.write(log)
                else:
                    with st.spinner("Saving to database..."):
                        # 確保 DataFrame 只有資料庫有的欄位
                        # 如果 Excel 有多了 status 欄位，這裡會過濾掉
                        cols_in_db = pd.read_sql("SELECT * FROM companies LIMIT 0", engine).columns.tolist()
                        final_up_df = up_df[[c for c in up_df.columns if c in cols_in_db]]
                        
                        final_up_df.to_sql('companies', engine, if_exists='append', index=False)
                        st.success("✅ 匯入成功！")
                        st.rerun()
        except Exception as e:
            st.error(f"Upload Error: {e}")

# --- 4. Company Register (100% 鎖定第 23 版邏輯) ---
elif choice == "🏢 Company Register":
    st.header("🏢 Company Records Management")
    mode = st.radio("Mode", ["🆕 Add New", "✏️ Edit Existing", "📋 Copy Existing"], horizontal=True)
    
    df_all = pd.read_sql("SELECT * FROM companies", engine)
    groups = pd.read_sql("SELECT group_name FROM client_groups", engine)['group_name'].tolist()
    
    d = {'cg': "", 'en': "", 'ch': "", 'idate': None, 'place': "", 'p_oth': "", 'ci': "", 'br': "", 'type': "", 'ra': "", 'ca': "", 'rl': "", 'sl': "", 'cl': "", 'n2e': None, 'n2f': None, 'n2d': False, 'n4e': None, 'n4f': None, 'n4d': False, 'dis': None}
    target_name = None

    if mode in ["✏️ Edit Existing", "📋 Copy Existing"] and not df_all.empty:
        comp_list = [""] + df_all['name_en'].tolist()
        label = "Select Company to Edit" if mode == "✏️ Edit Existing" else "Select Company to Copy From"
        target_name = st.selectbox(label, comp_list)
        
        if target_name != "":
            row = df_all[df_all['name_en'] == target_name].iloc[0]
            d = {
                'cg': row.get('client_group', ""), 'en': row.get('name_en', ""), 'ch': row.get('name_ch', ""), 
                'idate': row.get('incorp_date'), 'place': row.get('incorp_place', ""), 
                'p_oth': row.get('incorp_place_others', ""), 'ci': row.get('ci_no', ""), 'br': row.get('br_no', ""), 
                'type': row.get('co_type', ""), 'ra': row.get('reg_addr', ""), 'ca': row.get('corres_addr', ""),
                'rl': row.get('round_loc', ""), 'sl': row.get('sign_loc', ""), 'cl': row.get('seal_loc', ""),
                'n2e': row.get('nd2a_eff_date'), 'n2f': row.get('nd2a_file_date'), 
                'n2d': str(row.get('nd2a_download', "")) == 'True',
                'n4e': row.get('nd4_eff_date'), 'n4f': row.get('nd4_file_date'), 
                'n4d': str(row.get('nd4_download', "")) == 'True',
                'dis': row.get('dissolution_date')
            }
            if mode == "📋 Copy Existing": d['en'], d['ch'] = "", ""

    st.markdown("### General Information")
    def red_label(text, value):
        if not value or str(value).strip() == "" or value is None:
            return f":red[⚠️ {text} (Required!)]"
        return text

    client_group = st.selectbox(red_label("Select Client Group", d['cg']), [""] + groups, index=(groups.index(d['cg'])+1 if d['cg'] in groups else 0))
    col1, col2 = st.columns(2)
    name_en = col1.text_input(red_label("Company English Name", d['en']), value=d['en'])
    name_ch = col2.text_input(red_label("Company Chinese Name", d['ch']), value=d['ch'])
    col3, col4 = st.columns(2)
    inc_date = col3.date_input(red_label("Date of Incorporation", d['idate']), value=d['idate'])
    places = ["", "HK", "BVI", "Cayman Island", "Others"]
    p_idx = places.index(d['place']) if d['place'] in places else 0
    inc_place = col4.selectbox(red_label("Place of Incorporation", d['place']), places, index=p_idx)
    place_others = st.text_input(red_label("Specify Country", d['p_oth']), value=d['p_oth']) if inc_place == "Others" else ""

    st.write("---")
    col_ci, col_br = st.columns(2)
    ci_no = col_ci.text_input(red_label("CI Number", d['ci']), value=d['ci'])
    br_no = col_br.text_input(red_label("BR Number", d['br']), value=d['br'])
    types = ["", "Private Company", "Public Company", "Company Limited by Guarantee"]
    t_idx = types.index(d['type']) if d['type'] in types else 0
    co_type = st.selectbox(red_label("Company Type", d['type']), types, index=t_idx)
    
    st.write("---")
    st.markdown("### 📝 Company Secretary Appointment (ND2A)")
    c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
    nd2a_eff = c1.date_input("Effective Date (Appt)", value=d['n2e'], key="n2e")
    nd2a_file = c2.date_input("Filing Date (ND2A)", value=d['n2f'], key="n2f")
    if nd2a_eff: c3.warning(f"Statutory Period: 15 days\n\n⚠️ Deadline: {nd2a_eff + timedelta(days=15)}")
    else: c3.info("Statutory Period: 15 days")
    nd2a_dl = c4.checkbox("Downloaded", value=d['n2d'], key="n2d")

    st.markdown("### 📝 Company Secretary Resignation (ND4)")
    r1, r2, r3, r4 = st.columns([2, 2, 2, 1])
    nd4_eff = r1.date_input("Effective Date (Resign)", value=d['n4e'], key="n4e")
    nd4_file = r2.date_input("Filing Date (ND4)", value=d['n4f'], key="n4f")
    if nd4_eff: r3.warning(f"Statutory Period: 15 days\n\n⚠️ Deadline: {nd4_eff + timedelta(days=15)}")
    else: r3.info("Statutory Period: 15 days")
    nd4_dl = r4.checkbox("Downloaded", value=d['n4d'], key="n4d")

    st.write("---")
    st.markdown("### 📍 Address & Contact")
    col_reg, col_cor = st.columns(2)
    reg_addr = col_reg.text_area(red_label("Registered Office Address", d['ra']), value=d['ra'])
    corres_addr = col_cor.text_area(red_label("Correspondence Address", d['ca']), value=d['ca'])
    st.markdown("### 🗄️ Seal Storage") 
    l1, l2, l3 = st.columns(3)
    round_l = l1.text_input(red_label("Round Chop Location", d['rl']), value=d['rl'])
    sign_l = l2.text_input(red_label("Signature Chop Location", d['sl']), value=d['sl'])
    common_l = l3.text_input(red_label("Common Seal Location", d['cl']), value=d['cl'])
    st.write("---")
    dis_date = st.date_input("Company Dissolution Date", value=d['dis'])
    
    # 必填驗證清單
    required_fields = {"Client Group": client_group, "EN Name": name_en, "CH Name": name_ch, "Inc Date": inc_date, "Inc Place": inc_place, "CI No": ci_no, "BR No": br_no, "Co Type": co_type, "Reg Addr": reg_addr, "Cor Addr": corres_addr, "Round Chop": round_l, "Sign Chop": sign_l, "Common Seal": common_l}
    if inc_place == "Others": required_fields["Country"] = place_others

    def check_fields():
        empty = [k for k, v in required_fields.items() if not v or str(v).strip() == "" or v is None]
        if empty: st.error(f"❌ 以下項目尚未填寫：{', '.join(empty)}"); return False
        return True

    if mode in ["🆕 Add New", "📋 Copy Existing"]:
        with st.popover("💾 Save To Cloud"):
            if st.button("Yes, Confirm Save"):
                if check_fields():
                    new_data = {'client_group': client_group, 'name_en': name_en, 'name_ch': name_ch, 'incorp_date': inc_date, 'incorp_place': inc_place, 'incorp_place_others': place_others, 'ci_no': ci_no, 'br_no': br_no, 'co_type': co_type, 'reg_addr': reg_addr, 'corres_addr': corres_addr, 'round_loc': round_l, 'sign_loc': sign_l, 'seal_loc': common_l, 'nd2a_eff_date': nd2a_eff, 'nd2a_file_date': nd2a_file, 'nd2a_download': str(nd2a_dl), 'nd4_eff_date': nd4_eff, 'nd4_file_date': nd4_file, 'nd4_download': str(nd4_dl), 'dissolution_date': dis_date}
                    pd.DataFrame([new_data]).to_sql('companies', engine, if_exists='append', index=False)
                    st.success("New Record Saved!"); st.rerun()
    else:
        col_b1, col_b2 = st.columns(2)
        with col_b1.popover("🆙 Update Record"):
            if st.button("Yes, Confirm Update"):
                if check_fields():
                    df_filtered = df_all[df_all['name_en'] != target_name]
                    updated_row = {'client_group': client_group, 'name_en': name_en, 'name_ch': name_ch, 'incorp_date': inc_date, 'incorp_place': inc_place, 'incorp_place_others': place_others, 'ci_no': ci_no, 'br_no': br_no, 'co_type': co_type, 'reg_addr': reg_addr, 'corres_addr': corres_addr, 'round_loc': round_l, 'sign_loc': sign_l, 'seal_loc': common_l, 'nd2a_eff_date': nd2a_eff, 'nd2a_file_date': nd2a_file, 'nd2a_download': str(nd2a_dl), 'nd4_eff_date': nd4_eff, 'nd4_file_date': nd4_file, 'nd4_download': str(nd4_dl), 'dissolution_date': dis_date}
                    pd.concat([df_filtered, pd.DataFrame([updated_row])], ignore_index=True).to_sql('companies', engine, if_exists='replace', index=False)
                    st.success("Updated!"); st.rerun()
        with col_b2.popover("🚨 DELETE RECORD"):
            st.error(f"Deleting: **{target_name}**")
            if st.button("🔥 YES, DELETE FOREVER"):
                df_all[df_all['name_en'] != target_name].to_sql('companies', engine, if_exists='replace', index=False)
                st.warning("Deleted!"); st.rerun()

# --- 5. Dashboard ---
elif choice == "📊 Dashboard":
    st.header("📊 Compliance Overview")
    df = pd.read_sql("SELECT * FROM companies", engine)
    st.dataframe(df, use_container_width=True)

# --- 6. Group Management ---
elif choice == "⚙️ Group Management":
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
        with st.popover("🗑️ Delete Group"):
            if st.button("Confirm Delete Group"):
                g_df[g_df['group_name'] != target_g].to_sql('client_groups', engine, if_exists='replace', index=False)
                st.rerun()
