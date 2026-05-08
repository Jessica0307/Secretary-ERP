import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import io

# --- 1. Database Connection (鎖定) ---
try:
    DB_URL = st.secrets["DB_URL"]
    engine = create_engine(DB_URL)
except:
    st.error("❌ Please check DB_URL in Secrets")
    st.stop()

# --- 2. Navigation (LOCK V28) ---
st.set_page_config(page_title="ERP Cloud V34", layout="wide")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "⚙️ Group Management", "📤 Data Exchange"])

# 定義必填欄位
REQUIRED_COLS = ["client_group", "name_en", "name_ch", "incorp_date", "incorp_place", "ci_no", "br_no", "co_type", "reg_addr", "corres_addr", "round_loc", "sign_loc", "seal_loc"]

# --- 3. Data Exchange (鎖定 V28 邏輯) ---
if choice == "📤 Data Exchange":
    st.header("📤 Data Exchange & Backup")
    st.subheader("1. Download & Backup")
    col_ex1, col_ex2 = st.columns(2)
    template_cols = ["client_group", "name_en", "name_ch", "incorp_date", "incorp_place", "incorp_place_others", "ci_no", "br_no", "co_type", "reg_addr", "corres_addr", "round_loc", "sign_loc", "seal_loc", "nd2a_eff_date", "nd2a_file_date", "nd2a_download", "nd4_eff_date", "nd4_file_date", "nd4_download", "dissolution_date"]
    tmp_df = pd.DataFrame(columns=template_cols)
    buffer_tmp = io.BytesIO()
    with pd.ExcelWriter(buffer_tmp, engine='xlsxwriter') as writer:
        tmp_df.to_excel(writer, index=False)
    col_ex1.download_button(label="📥 Download Blank Template", data=buffer_tmp.getvalue(), file_name="Company_Record_Template.xlsx", mime="application/vnd.ms-excel")

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
            up_df = pd.read_excel(uploaded_file, engine='openpyxl', keep_default_na=False)
            if st.button("🚀 Confirm Upload to Cloud"):
                date_cols = ["incorp_date", "nd2a_eff_date", "nd2a_file_date", "nd4_eff_date", "nd4_file_date", "dissolution_date"]
                for col in date_cols:
                    if col in up_df.columns:
                        up_df[col] = up_df[col].apply(lambda x: None if str(x).strip().lower() in ["", "nan", "n/a", "none", "nil"] else x)
                        up_df[col] = pd.to_datetime(up_df[col], errors='coerce')
                error_logs = []
                for i, row in up_df.iterrows():
                    missing = [c for c in REQUIRED_COLS if pd.isna(row[c]) or str(row[c]).strip() == ""]
                    if missing: error_logs.append(f"Row {i+2}: 缺少 {', '.join(missing)}")
                if error_logs:
                    for log in error_logs[:10]: st.write(log)
                else:
                    up_df.to_sql('companies', engine, if_exists='append', index=False)
                    st.success("✅ 匯入成功！"); st.rerun()
        except Exception as e: st.error(f"Error: {e}")

# --- 4. Company Register (100% 鎖定第 28 版邏輯) ---
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

    def red_label(text, value):
        return f":red[⚠️ {text} (Required!)]" if not value or str(value).strip() == "" or value is None else text

    client_group = st.selectbox(red_label("Select Client Group", d['cg']), [""] + groups, index=(groups.index(d['cg'])+1 if d['cg'] in groups else 0))
    c1, c2 = st.columns(2); name_en = c1.text_input(red_label("English Name", d['en']), value=d['en']); name_ch = c2.text_input(red_label("Chinese Name", d['ch']), value=d['ch'])
    c3, c4 = st.columns(2); inc_date = c3.date_input(red_label("Incorp Date", d['idate']), value=d['idate']); places = ["", "HK", "BVI", "Cayman Island", "Others"]; p_idx = places.index(d['place']) if d['place'] in places else 0; inc_place = c4.selectbox(red_label("Place", d['place']), places, index=p_idx); place_others = st.text_input("Specify", value=d['p_oth']) if inc_place == "Others" else ""
    st.write("---")
    col_ci, col_br = st.columns(2); ci_no = col_ci.text_input(red_label("CI", d['ci']), value=d['ci']); br_no = col_br.text_input(red_label("BR", d['br']), value=d['br']); types = ["", "Private Company", "Public Company", "Company Limited by Guarantee"]; t_idx = types.index(d['type']) if d['type'] in types else 0; co_type = st.selectbox(red_label("Type", d['type']), types, index=t_idx)
    st.write("---")
    st.markdown("### 📝 ND2A & ND4")
    cc1, cc2, cc3 = st.columns([2, 2, 2]); n2e = cc1.date_input("ND2A Eff", value=d['n2e']); n2f = cc2.date_input("ND2A File", value=d['n2f'])
    if n2e: cc3.warning(f"Deadline: {n2e + timedelta(days=15)}")
    rr1, rr2, rr3 = st.columns([2, 2, 2]); n4e = rr1.date_input("ND4 Eff", value=d['n4e']); n4f = rr2.date_input("ND4 File", value=d['n4f'])
    if n4e: rr3.warning(f"Deadline: {n4e + timedelta(days=15)}")
    st.write("---")
    reg_addr = st.text_area(red_label("Reg Addr", d['ra']), value=d['ra']); corres_addr = st.text_area(red_label("Cor Addr", d['ca']), value=d['ca'])
    l1, l2, l3 = st.columns(3); round_l = l1.text_input(red_label("Round", d['rl']), value=d['rl']); sign_l = l2.text_input(red_label("Sign", d['sl']), value=d['sl']); common_l = l3.text_input(red_label("Common", d['cl']), value=d['cl'])
    dis_date = st.date_input("Dissolution", value=d['dis'])
    
    required_fields = {"Group": client_group, "EN": name_en, "CH": name_ch, "Date": inc_date, "Place": inc_place, "CI": ci_no, "BR": br_no, "Type": co_type, "Reg": reg_addr, "Cor": corres_addr, "Round": round_l, "Sign": sign_l, "Common": common_l}
    if mode in ["🆕 Add New", "📋 Copy Existing"]:
        with st.popover("💾 Save"):
            if st.button("Confirm Save"):
                if all(required_fields.values()):
                    pd.DataFrame([{'client_group': client_group, 'name_en': name_en, 'name_ch': name_ch, 'incorp_date': inc_date, 'incorp_place': inc_place, 'incorp_place_others': place_others, 'ci_no': ci_no, 'br_no': br_no, 'co_type': co_type, 'reg_addr': reg_addr, 'corres_addr': corres_addr, 'round_loc': round_l, 'sign_loc': sign_l, 'seal_loc': common_l, 'nd2a_eff_date': n2e, 'nd2a_file_date': n2f, 'nd4_eff_date': n4e, 'nd4_file_date': n4f, 'dissolution_date': dis_date}]).to_sql('companies', engine, if_exists='append', index=False)
                    st.success("Saved!"); st.rerun()
    else:
        col_b1, col_b2 = st.columns(2)
        with col_b1.popover("🆙 Update"):
            if st.button("Confirm Update"):
                df_f = df_all[df_all['name_en'] != target_name]
                up_r = {'client_group': client_group, 'name_en': name_en, 'name_ch': name_ch, 'incorp_date': inc_date, 'incorp_place': inc_place, 'incorp_place_others': place_others, 'ci_no': ci_no, 'br_no': br_no, 'co_type': co_type, 'reg_addr': reg_addr, 'corres_addr': corres_addr, 'round_loc': round_l, 'sign_loc': sign_l, 'seal_loc': common_l, 'nd2a_eff_date': n2e, 'nd2a_file_date': n2f, 'nd4_eff_date': n4e, 'nd4_file_date': n4f, 'dissolution_date': dis_date}
                pd.concat([df_f, pd.DataFrame([up_r])], ignore_index=True).to_sql('companies', engine, if_exists='replace', index=False); st.success("Updated!"); st.rerun()

# --- 5. Dashboard (新增批量刪除功能) ---
elif choice == "📊 Dashboard":
    st.header("📊 Compliance Overview & Batch Delete")
    df = pd.read_sql("SELECT * FROM companies", engine)
    
    if not df.empty:
        # 新增選取欄位
        df.insert(0, "Select", False)
        
        # 顯示可編輯表格 (用於選擇)
        edited_df = st.data_editor(
            df,
            column_config={"Select": st.column_config.CheckboxColumn(required=True)},
            disabled=[c for c in df.columns if c != "Select"],
            hide_index=True,
            use_container_width=True
        )
        
        selected_rows = edited_df[edited_df["Select"] == True]
        
        if len(selected_rows) > 0:
            st.warning(f"Selected {len(selected_rows)} companies for deletion.")
            with st.popover("🚨 BATCH DELETE"):
                st.write("Are you sure? This cannot be undone.")
                if st.button("🔥 YES, DELETE SELECTED"):
                    names_to_delete = selected_rows["name_en"].tolist()
                    new_df = df[~df["name_en"].isin(names_to_delete)].drop(columns=["Select"])
                    new_df.to_sql('companies', engine, if_exists='replace', index=False)
                    st.success(f"Deleted {len(selected_rows)} records!")
                    st.rerun()
    else:
        st.info("No records found.")

# --- 6. Group Management (鎖定 V28) ---
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
