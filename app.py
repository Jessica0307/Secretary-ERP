import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import io
from weasyprint import HTML

# --- 1. Database Connection (鎖定 V32) ---
try:
    DB_URL = st.secrets["DB_URL"]
    engine = create_engine(DB_URL)
except:
    st.error("❌ Please check DB_URL in Secrets")
    st.stop()

# --- 2. Navigation ---
st.set_page_config(page_title="ERP Cloud V34", layout="wide")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "⚙️ Group Management", "📤 Data Exchange"])

# 定義必填欄位 (用於上傳驗證)
REQUIRED_COLS = ["client_group", "name_en", "name_ch", "incorp_date", "incorp_place", "ci_no", "br_no", "co_type", "reg_addr", "corres_addr", "round_loc", "sign_loc", "seal_loc"]

# --- PDF 生成函式 (專業美化版) ---
def generate_custom_pdf(selected_df):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    html_content = f"""
    <html>
    <head>
        <style>
            @page {{ size: A4; margin: 15mm; }}
            body {{ font-family: 'Arial', sans-serif; color: #2c3e50; line-height: 1.4; }}
            .header {{ text-align: center; border-bottom: 2px solid #34495e; padding-bottom: 10px; margin-bottom: 20px; }}
            .company-card {{ page-break-inside: avoid; border: 1px solid #dcdde1; border-radius: 8px; padding: 20px; margin-bottom: 25px; background-color: #fbfbfb; }}
            .name-en {{ font-size: 16pt; font-weight: bold; color: #2980b9; border-bottom: 2px solid #3498db; }}
            .name-ch {{ font-size: 14pt; color: #34495e; margin-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 10pt; }}
            th {{ text-align: left; width: 35%; color: #7f8c8d; border-bottom: 1px solid #eee; padding: 6px 0; }}
            td {{ border-bottom: 1px solid #eee; padding: 6px 0; color: #2c3e50; }}
            .section-title {{ background: #ebf3f9; padding: 5px 10px; font-weight: bold; font-size: 11pt; margin-top: 15px; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="header"><h1>Corporate Portfolio Report</h1><p>Selected Records: {len(selected_df)} | Generated: {now}</p></div>
    """
    for _, row in selected_df.iterrows():
        html_content += f"""
        <div class="company-card">
            <div class="name-en">{row.get('name_en','')}</div>
            <div class="name-ch">{row.get('name_ch','')}</div>
            <div class="section-title">Registration & Legal</div>
            <table>
                <tr><th>Client Group</th><td>{row.get('client_group','')}</td></tr>
                <tr><th>Incorp. Date / Place</th><td>{row.get('incorp_date','')} ({row.get('incorp_place','')})</td></tr>
                <tr><th>CI No. / BR No.</th><td>{row.get('ci_no','')} / {row.get('br_no','')}</td></tr>
                <tr><th>Company Type</th><td>{row.get('co_type','')}</td></tr>
            </table>
            <div class="section-title">Compliance Status</div>
            <table>
                <tr><th>ND2A Effective Date</th><td>{row.get('nd2a_eff_date','N/A')}</td></tr>
                <tr><th>ND4 Effective Date</th><td>{row.get('nd4_eff_date','N/A')}</td></tr>
            </table>
            <div class="section-title">Addresses & Items</div>
            <table>
                <tr><th>Registered Addr</th><td>{row.get('reg_addr','')}</td></tr>
                <tr><th>Correspondence Addr</th><td>{row.get('corres_addr','')}</td></tr>
                <tr><th>Stamps & Seal Location</th><td>{row.get('round_loc','')} / {row.get('sign_loc','')} / {row.get('seal_loc','')}</td></tr>
            </table>
        </div>"""
    html_content += "</body></html>"
    return HTML(string=html_content).write_pdf()

# --- 3. Data Exchange (回歸 V32 邏輯) ---
if choice == "📤 Data Exchange":
    st.header("📤 Data Exchange & Backup")
    st.subheader("1. Download & Backup")
    col_ex1, col_ex2 = st.columns(2)
    template_cols = ["client_group", "name_en", "name_ch", "incorp_date", "incorp_place", "incorp_place_others", "ci_no", "br_no", "co_type", "reg_addr", "corres_addr", "round_loc", "sign_loc", "seal_loc", "nd2a_eff_date", "nd2a_file_date", "nd2a_download", "nd4_eff_date", "nd4_file_date", "nd4_download", "dissolution_date"]
    tmp_df = pd.DataFrame(columns=template_cols)
    buffer_tmp = io.BytesIO()
    with pd.ExcelWriter(buffer_tmp, engine='xlsxwriter') as writer:
        tmp_df.to_excel(writer, index=False)
    col_ex1.download_button(label="📥 Download Blank Template", data=buffer_tmp.getvalue(), file_name="Company_Record_Template.xlsx")

    df_all_export = pd.read_sql("SELECT * FROM companies", engine)
    buffer_all = io.BytesIO()
    with pd.ExcelWriter(buffer_all, engine='xlsxwriter') as writer:
        df_all_export.to_excel(writer, index=False)
    col_ex2.download_button(label="📦 Export All Data (Backup)", data=buffer_all.getvalue(), file_name=f"Full_Backup_{datetime.now().strftime('%Y%m%d')}.xlsx")

    st.write("---")
    st.subheader("2. Upload & Bulk Import")
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
    if uploaded_file:
        try:
            up_df = pd.read_excel(uploaded_file, engine='openpyxl', keep_default_na=False)
            if st.button("🚀 Confirm Upload"):
                date_cols = ["incorp_date", "nd2a_eff_date", "nd2a_file_date", "nd4_eff_date", "nd4_file_date", "dissolution_date"]
                for col in date_cols:
                    if col in up_df.columns:
                        up_df[col] = up_df[col].apply(lambda x: None if str(x).strip().lower() in ["", "nan", "n/a", "none", "nil"] else x)
                        up_df[col] = pd.to_datetime(up_df[col], errors='coerce')
                up_df.to_sql('companies', engine, if_exists='append', index=False)
                st.success("✅ Uploaded!"); st.rerun()
        except Exception as e: st.error(f"Error: {e}")

# --- 4. Company Register (回歸 V32 邏輯 + 強化刪除確認) ---
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
    cc1, cc2, cc3 = st.columns([2, 2, 2]); n2e = cc1.date_input("ND2A Eff", value=d['n2e']); n2f = cc2.date_input("ND2A File", value=d['n2f'])
    if n2e: cc3.warning(f"Deadline: {n2e + timedelta(days=15)}")
    rr1, rr2, rr3 = st.columns([2, 2, 2]); n4e = rr1.date_input("ND4 Eff", value=d['n4e']); n4f = rr2.date_input("ND4 File", value=d['n4f'])
    if n4e: rr3.warning(f"Deadline: {n4e + timedelta(days=15)}")
    st.write("---")
    reg_addr = st.text_area(red_label("Reg Addr", d['ra']), value=d['ra']); corres_addr = st.text_area(red_label("Cor Addr", d['ca']), value=d['ca'])
    l1, l2, l3 = st.columns(3); round_l = l1.text_input(red_label("Round", d['rl']), value=d['rl']); sign_l = l2.text_input(red_label("Sign", d['sl']), value=d['sl']); common_l = l3.text_input(red_label("Common", d['cl']), value=d['cl'])
    dis_date = st.date_input("Dissolution", value=d['dis'])
    
    if mode in ["🆕 Add New", "📋 Copy Existing"]:
        with st.popover("💾 Save"):
            if st.button("Confirm Save"):
                pd.DataFrame([{'client_group': client_group, 'name_en': name_en, 'name_ch': name_ch, 'incorp_date': inc_date, 'incorp_place': inc_place, 'incorp_place_others': place_others, 'ci_no': ci_no, 'br_no': br_no, 'co_type': co_type, 'reg_addr': reg_addr, 'corres_addr': corres_addr, 'round_loc': round_l, 'sign_loc': sign_l, 'seal_loc': common_l, 'nd2a_eff_date': n2e, 'nd2a_file_date': n2f, 'nd4_eff_date': n4e, 'nd4_file_date': n4f, 'dissolution_date': dis_date}]).to_sql('companies', engine, if_exists='append', index=False)
                st.success("Saved!"); st.rerun()
    else:
        cb1, cb2 = st.columns(2)
        with cb1.popover("🆙 Update"):
            if st.button("Confirm Update"):
                df_f = df_all[df_all['name_en'] != target_name]
                up_r = {'client_group': client_group, 'name_en': name_en, 'name_ch': name_ch, 'incorp_date': inc_date, 'incorp_place': inc_place, 'incorp_place_others': place_others, 'ci_no': ci_no, 'br_no': br_no, 'co_type': co_type, 'reg_addr': reg_addr, 'corres_addr': corres_addr, 'round_loc': round_l, 'sign_loc': sign_l, 'seal_loc': common_l, 'nd2a_eff_date': n2e, 'nd2a_file_date': n2f, 'nd4_eff_date': n4e, 'nd4_file_date': n4f, 'dissolution_date': dis_date}
                pd.concat([df_f, pd.DataFrame([up_r])], ignore_index=True).to_sql('companies', engine, if_exists='replace', index=False); st.success("Updated!"); st.rerun()
        
        with cb2.popover("🚨 DELETE THIS COMPANY"):
            st.error(f"⚠️ **ATTENTION!** ⚠️")
            st.write(f"You are about to permanently delete: **{target_name}**")
            confirm_text = st.text_input("Type **DELETE** to confirm", key="single_del_input")
            if st.button("🔥 YES, DELETE NOW", disabled=(confirm_text != "DELETE")):
                df_all[df_all['name_en'] != target_name].to_sql('companies', engine, if_exists='replace', index=False)
                st.warning(f"{target_name} deleted."); st.rerun()

# --- 5. Dashboard (核心功能：支援自選導出 PDF) ---
elif choice == "📊 Dashboard":
    st.header("📊 Compliance Overview & Batch Actions")
    df = pd.read_sql("SELECT * FROM companies", engine)
    
    if not df.empty:
        if 'select_state' not in st.session_state: st.session_state.select_state = False
        t1, t2, t3, t4 = st.columns([2, 2, 2, 6])
        if t1.button("🔄 Refresh"): st.rerun()
        if t2.button("✅ Select All"): st.session_state.select_state = True; st.rerun()
        if t3.button("🧹 Clear All"): st.session_state.select_state = False; st.rerun()
            
        df.insert(0, "Select", st.session_state.select_state)
        # 允許表格自帶篩選功能 (用戶可自行 filter Group)
        edited_df = st.data_editor(df, column_config={"Select": st.column_config.CheckboxColumn("Select", default=False)}, disabled=[c for c in df.columns if c != "Select"], hide_index=True, use_container_width=True, key="dashboard_editor_v34")
        
        selected_rows = edited_df[edited_df["Select"] == True]
        
        if len(selected_rows) > 0:
            st.info(f"已選取 {len(selected_rows)} 筆紀錄")
            
            # 操作工具列
            act1, act2 = st.columns([3, 7])
            
            # --- 功能 A: 導出 PDF (僅選中項) ---
            with act1:
                if st.button("📥 Export Selected to PDF"):
                    pdf_bytes = generate_custom_pdf(selected_rows)
                    st.download_button(label="Click to Download PDF", data=pdf_bytes, file_name=f"Selected_Companies_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf")
            
            # --- 功能 B: 批量刪除 (鎖定 V32 邏輯) ---
            with act2.popover("🧨 CRITICAL: BATCH DELETE"):
                st.error("### 🛑 DANGER ZONE")
                st.write(f"這將永久刪除資料庫中選中的 **{len(selected_rows)}** 筆紀錄。")
                user_conf = st.text_input(f"請輸入 **DELETE** 確認", key="batch_del_input")
                if st.button("🔥 確認永久刪除", disabled=(user_conf != "DELETE")):
                    to_del = selected_rows["name_en"].tolist()
                    latest = pd.read_sql("SELECT * FROM companies", engine)
                    latest[~latest["name_en"].isin(to_del)].to_sql('companies', engine, if_exists='replace', index=False)
                    st.success(f"已清理 {len(selected_rows)} 筆紀錄！"); st.rerun()
    else: st.info("No records.")

# --- 6. Group Management (鎖定 V32 邏輯) ---
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
            st.error(f"Delete Group: **{target_g}**?")
            conf = st.text_input("Type **DELETE** to confirm", key="group_del_input")
            if st.button("Confirm Delete Group", disabled=(conf != "DELETE")):
                g_df[g_df['group_name'] != target_g].to_sql('client_groups', engine, if_exists='replace', index=False)
                st.rerun()
