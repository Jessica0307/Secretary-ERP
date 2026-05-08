import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import io
from weasyprint import HTML

# --- 1. Database Connection (鎖定 V32 邏輯) ---
try:
    DB_URL = st.secrets["DB_URL"]
    engine = create_engine(DB_URL)
except:
    st.error("❌ Please check DB_URL in Secrets")
    st.stop()

# --- 2. Navigation ---
st.set_page_config(page_title="ERP Cloud V38", layout="wide")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "⚙️ Group Management", "📤 Data Exchange"])

# 定義必填欄位
REQUIRED_COLS = ["client_group", "name_en", "name_ch", "incorp_date", "incorp_place", "ci_no", "br_no", "co_type", "reg_addr", "corres_addr", "round_loc", "sign_loc", "seal_loc"]

# --- PDF 生成函式 (引用網絡字型以解決 Cloud 亂碼) ---
def generate_custom_pdf(selected_df):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 這裡加入 Google Fonts 的引用，確保 Linux Server 也能顯示中文
    html_content = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+HK:wght@400;700&display=swap" rel="stylesheet">
        <style>
            @page {{ size: A4; margin: 15mm; }}
            body {{ 
                font-family: 'Noto Sans HK', sans-serif; 
                color: #2c3e50; line-height: 1.4; 
            }}
            .header {{ text-align: center; border-bottom: 2px solid #34495e; padding-bottom: 10px; margin-bottom: 20px; }}
            .company-card {{ page-break-inside: avoid; border: 1px solid #dcdde1; border-radius: 8px; padding: 20px; margin-bottom: 25px; background-color: #fbfbfb; }}
            .name-en {{ font-size: 16pt; font-weight: bold; color: #2980b9; border-bottom: 2px solid #3498db; }}
            .name-ch {{ font-size: 14pt; color: #34495e; margin-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 10pt; }}
            th {{ text-align: left; width: 35%; color: #7f8c8d; border-bottom: 1px solid #f1f2f6; padding: 6px 0; }}
            td {{ border-bottom: 1px solid #f1f2f6; padding: 6px 0; color: #2c3e50; }}
            .section-title {{ background: #ebf3f9; padding: 5px 10px; font-weight: bold; font-size: 11pt; margin-top: 15px; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="header"><h1>Corporate Portfolio Report</h1><p>Generated: {now}</p></div>
    """
    for _, row in selected_df.iterrows():
        html_content += f"""
        <div class="company-card">
            <div class="name-en">{row.get('name_en','')}</div>
            <div class="name-ch">{row.get('name_ch','')}</div>
            <div class="section-title">Registration / 註冊資料</div>
            <table>
                <tr><th>Client Group</th><td>{row.get('client_group','')}</td></tr>
                <tr><th>Incorp. Date / Place</th><td>{row.get('incorp_date','')} ({row.get('incorp_place','')})</td></tr>
                <tr><th>CI No. / BR No.</th><td>{row.get('ci_no','')} / {row.get('br_no','')}</td></tr>
                <tr><th>Company Type</th><td>{row.get('co_type','')}</td></tr>
            </table>
            <div class="section-title">Addresses & Items / 地址及物品</div>
            <table>
                <tr><th>Registered Addr</th><td>{row.get('reg_addr','')}</td></tr>
                <tr><th>Correspondence Addr</th><td>{row.get('corres_addr','')}</td></tr>
                <tr><th>Stamps Location</th><td>{row.get('round_loc','')} / {row.get('sign_loc','')} / {row.get('seal_loc','')}</td></tr>
            </table>
        </div>"""
    html_content += "</body></html>"
    return HTML(string=html_content).write_pdf()

# --- 3. Data Exchange ---
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

# --- 4. Company Register (維持第 32 版邏輯) ---
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

    client_group = st.selectbox(red_label("Select Group", d['cg']), [""] + groups, index=(groups.index(d['cg'])+1 if d['cg'] in groups else 0))
    c1, c2 = st.columns(2); n_en = c1.text_input(red_label("EN Name", d['en']), value=d['en']); n_ch = c2.text_input(red_label("CH Name", d['ch']), value=d['ch'])
    c3, c4 = st.columns(2); i_d = c3.date_input(red_label("Incorp Date", d['idate']), value=d['idate']); ps = ["", "HK", "BVI", "Cayman Island", "Others"]; p_idx = ps.index(d['place']) if d['place'] in ps else 0; i_p = c4.selectbox(red_label("Place", d['place']), ps, index=p_idx); p_o = st.text_input("Specify", value=d['p_oth']) if i_p == "Others" else ""
    st.write("---")
    ci = st.text_input(red_label("CI", d['ci']), value=d['ci']); br = st.text_input(red_label("BR", d['br']), value=d['br'])
    ts = ["", "Private Company", "Public Company", "Company Limited by Guarantee"]; t_idx = ts.index(d['type']) if d['type'] in ts else 0; c_t = st.selectbox(red_label("Type", d['type']), ts, index=t_idx)
    st.write("---")
    cc1, cc2 = st.columns(2); n2e = cc1.date_input("ND2A Eff", value=d['n2e']); n4e = cc2.date_input("ND4 Eff", value=d['n4e'])
    st.write("---")
    ra = st.text_area(red_label("Reg Addr", d['ra']), value=d['ra']); ca = st.text_area(red_label("Cor Addr", d['ca']), value=d['ca'])
    l1, l2, l3 = st.columns(3); r_l = l1.text_input(red_label("Round", d['rl']), value=d['rl']); s_l = l2.text_input(red_label("Sign", d['sl']), value=d['sl']); c_l = l3.text_input(red_label("Common", d['cl']), value=d['cl'])
    
    if mode in ["🆕 Add New", "📋 Copy Existing"]:
        if st.button("💾 Save"):
            new_r = {'client_group': client_group, 'name_en': n_en, 'name_ch': n_ch, 'incorp_date': i_d, 'incorp_place': i_p, 'incorp_place_others': p_o, 'ci_no': ci, 'br_no': br, 'co_type': c_t, 'reg_addr': ra, 'corres_addr': ca, 'round_loc': r_l, 'sign_loc': s_l, 'seal_loc': c_l, 'nd2a_eff_date': n2e, 'nd4_eff_date': n4e}
            pd.DataFrame([new_r]).to_sql('companies', engine, if_exists='append', index=False); st.success("Saved!"); st.rerun()
    else:
        cb1, cb2 = st.columns(2)
        with cb1.popover("🆙 Update"):
            if st.button("Confirm Update"):
                df_f = df_all[df_all['name_en'] != target_name]
                up_r = {'client_group': client_group, 'name_en': n_en, 'name_ch': n_ch, 'incorp_date': i_d, 'incorp_place': i_p, 'incorp_place_others': p_o, 'ci_no': ci, 'br_no': br, 'co_type': c_t, 'reg_addr': ra, 'corres_addr': ca, 'round_loc': r_l, 'sign_loc': s_l, 'seal_loc': c_l, 'nd2a_eff_date': n2e, 'nd4_eff_date': n4e}
                pd.concat([df_f, pd.DataFrame([up_r])], ignore_index=True).to_sql('companies', engine, if_exists='replace', index=False); st.success("Updated!"); st.rerun()
        with cb2.popover("🚨 DELETE"):
            st.error("Delete?"); conf = st.text_input("Type DELETE")
            if st.button("🔥 Confirm", disabled=(conf != "DELETE")):
                df_all[df_all['name_en'] != target_name].to_sql('companies', engine, if_exists='replace', index=False); st.rerun()

# --- 5. Dashboard ---
elif choice == "📊 Dashboard":
    st.header("📊 Compliance Overview")
    df_raw = pd.read_sql("SELECT * FROM companies", engine)
    groups = pd.read_sql("SELECT group_name FROM client_groups", engine)['group_name'].tolist()
    
    if not df_raw.empty:
        t1, t2, t3, t4 = st.columns([3, 2, 2, 5])
        filter_g = t1.selectbox("🔍 Filter Group", ["All Groups"] + groups)
        if t2.button("🔄 Refresh"): st.rerun()
        
        df_filtered = df_raw if filter_g == "All Groups" else df_raw[df_raw['client_group'] == filter_g]
        
        if 'select_state' not in st.session_state: st.session_state.select_state = False
        if t3.button("✅ Select All"): st.session_state.select_state = True; st.rerun()
        if t4.button("🧹 Clear All"): st.session_state.select_state = False; st.rerun()

        df_display = df_filtered.copy()
        df_display.insert(0, "Select", st.session_state.select_state)
        
        edited_df = st.data_editor(df_display, column_config={"Select": st.column_config.CheckboxColumn("Select", default=False)}, disabled=[c for c in df_display.columns if c != "Select"], hide_index=True, use_container_width=True, key="dashboard_editor_v38")
        
        selected_rows = edited_df[edited_df["Select"] == True]
        
        if len(selected_rows) > 0:
            st.info(f"Selected {len(selected_rows)} records")
            act1, act2 = st.columns([3, 7])
            with act1:
                if st.button("📥 Export PDF"):
                    pdf_bytes = generate_custom_pdf(selected_rows)
                    st.download_button(label="Download PDF", data=pdf_bytes, file_name="Report.pdf", mime="application/pdf")
            with act2.popover("🧨 BATCH DELETE"):
                st.error("DANGER"); conf = st.text_input("Type DELETE")
                if st.button("🔥 PURGE", disabled=(conf != "DELETE")):
                    to_del = selected_rows["name_en"].tolist()
                    df_raw[~df_raw["name_en"].isin(to_del)].to_sql('companies', engine, if_exists='replace', index=False); st.rerun()
    else: st.info("No records.")

# --- 6. Group Management ---
elif choice == "⚙️ Group Management":
    st.header("⚙️ Group Management")
    new_g = st.text_input("New Group")
    if st.button("Add"):
        pd.DataFrame([{'group_name': new_g}]).to_sql('client_groups', engine, if_exists='append', index=False); st.rerun()
    st.write("---")
    g_df = pd.read_sql("SELECT * FROM client_groups", engine)
    if not g_df.empty:
        target_g = st.selectbox("Select", g_df['group_name'].tolist())
        with st.popover("🗑️ Delete"):
            c = st.text_input("Type DELETE")
            if st.button("Confirm", disabled=(c != "DELETE")):
                g_df[g_df['group_name'] != target_g].to_sql('client_groups', engine, if_exists='replace', index=False); st.rerun()
