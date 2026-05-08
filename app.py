import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import io
from weasyprint import HTML

# --- 1. Database Connection ---
try:
    DB_URL = st.secrets["DB_URL"]
    engine = create_engine(DB_URL)
except:
    st.error("❌ Database connection failed.")
    st.stop()

# --- 2. Navigation ---
st.set_page_config(page_title="ERP Cloud V84", layout="wide")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "⚙️ Group Management", "📤 Data Exchange"])

# --- 3. PDF 生成函式 (【絕對置底】順序：法定申報擺 HTML 最後) ---
def generate_custom_pdf(selected_df):
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    def fmt_date(val):
        if pd.isna(val) or str(val).strip().lower() in ["none", "nan", "n/a", ""]: return "N/A"
        try: return pd.to_datetime(val).strftime('%Y/%m/%d')
        except: return str(val)
    
    html_content = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap" rel="stylesheet">
        <style>
            @page {{ size: A4; margin: 10mm; }}
            body {{ font-family: 'Noto Sans TC', sans-serif; color: #2c3e50; line-height: 1.4; background-color: #ffffff; }}
            .report-header {{ text-align: center; border-bottom: 2px solid #2c3e50; padding-bottom: 10px; margin-bottom: 25px; }}
            .report-header h1 {{ margin: 0; font-size: 24pt; color: #2c3e50; }}
            .report-header p {{ margin: 5px 0; font-size: 10pt; color: #7f8c8d; }}
            .page-wrapper {{ page-break-after: always; padding: 10px; }}
            .page-wrapper:last-child {{ page-break-after: auto; }}
            .company-card {{ border: 1px solid #dcdde1; border-radius: 12px; padding: 25px; background-color: #ffffff; }}
            .name-en {{ font-size: 22pt; font-weight: bold; color: #2980b9; margin-bottom: 2px; }}
            .name-ch {{ font-size: 16pt; color: #333333; margin-bottom: 20px; }}
            .section-bar {{ 
                background-color: #f1f4f6; padding: 8px 15px; font-weight: bold; font-size: 11pt; 
                margin: 20px 0 10px 0; border-left: 5px solid #3498db; color: #2c3e50;
            }}
            .info-table {{ width: 100%; border-collapse: collapse; }}
            .info-table tr {{ border-bottom: 1px solid #f1f2f6; }}
            .info-table th {{ text-align: left; width: 45%; color: #7f8c8d; padding: 8px 0; font-weight: normal; font-size: 10.5pt; }}
            .info-table td {{ text-align: left; padding: 8px 0; color: #2c3e50; font-size: 10.5pt; font-weight: bold; }}
        </style>
    </head>
    <body>
    """
    for _, row in selected_df.iterrows():
        html_content += f"""
        <div class="page-wrapper">
            <div class="report-header"><h1>Corporate Portfolio Report</h1><p>Generated on: {now}</p></div>
            <div class="company-card">
                <div class="name-en">{row.get('name_en','')}</div>
                <div class="name-ch">{row.get('name_ch','')}</div>
                
                <div class="section-bar">Registration Details / 註冊詳情</div>
                <table class="info-table">
                    <tr><th>Client Group / 客戶組別</th><td>{row.get('client_group','')}</td></tr>
                    <tr><th>Incorp. Date (YYYY/MM/DD) / 成立日期</th><td>{fmt_date(row.get('incorp_date'))}</td></tr>
                    <tr><th>Incorp. Place / 成立地點</th><td>{row.get('incorp_place','')}</td></tr>
                    <tr><th>CI No. / 公司註冊編號</th><td>{row.get('ci_no','')}</td></tr>
                    <tr><th>BR No. / 商業登記編號</th><td>{row.get('br_no','')}</td></tr>
                    <tr><th>Company Type / 公司類別</th><td>{row.get('co_type','')}</td></tr>
                </table>

                <div class="section-bar">Addresses / 地址</div>
                <table class="info-table">
                    <tr><th>Registered Address / 註冊地址</th><td>{row.get('reg_addr','')}</td></tr>
                    <tr><th>Correspondence Address / 通訊地址</th><td>{row.get('corres_addr','')}</td></tr>
                </table>

                <div class="section-bar">Items Storage / 物品存放位置</div>
                <table class="info-table">
                    <tr><th>Round Stamp / 小圓章</th><td>{row.get('round_loc','')}</td></tr>
                    <tr><th>Signature Chop / 簽名章</th><td>{row.get('sign_loc','')}</td></tr>
                    <tr><th>Common Seal / 鋼印</th><td>{row.get('seal_loc','')}</td></tr>
                </table>

                <!-- PDF 法定申報置底 -->
                <div class="section-bar">Compliance Filings / 法定申報</div>
                <table class="info-table">
                    <tr><th>ND2A Effective Date (YYYY/MM/DD)</th><td>{fmt_date(row.get('nd2a_eff_date'))}</td></tr>
                    <tr><th>ND4 Effective Date (YYYY/MM/DD)</th><td>{fmt_date(row.get('nd4_eff_date'))}</td></tr>
                </table>
            </div>
        </div>"""
    html_content += "</body></html>"
    return HTML(string=html_content).write_pdf()

# --- 4. Dashboard (按鈕同一行，鎖定佈局) ---
if choice == "📊 Dashboard":
    st.header("📊 Compliance Overview")
    df_raw = pd.read_sql("SELECT * FROM companies", engine)
    groups = pd.read_sql("SELECT group_name FROM client_groups", engine)['group_name'].tolist()
    if not df_raw.empty:
        t1, t2, t3, t4 = st.columns([3, 2, 2, 5])
        filter_g = t1.selectbox("🔍 Filter", ["All Groups"] + groups)
        if t2.button("🔄 Refresh"): st.rerun()
        df_filtered = df_raw if filter_g == "All Groups" else df_raw[df_raw['client_group'] == filter_g]
        
        if 'sel_v84' not in st.session_state: st.session_state.sel_v84 = False
        if t3.button("✅ Select All"): st.session_state.sel_v84 = True; st.rerun()
        if t4.button("🧹 Clear All"): st.session_state.sel_v84 = False; st.rerun()
        
        df_display = df_filtered.copy()
        for col in ["incorp_date", "nd2a_eff_date", "nd4_eff_date"]:
            if col in df_display.columns: df_display[col] = pd.to_datetime(df_display[col], errors='coerce').dt.date
        df_display.insert(0, "Select", st.session_state.sel_v84)
        
        edit_df = st.data_editor(df_display, column_config={"Select": st.column_config.CheckboxColumn("Select", default=False)}, hide_index=True, use_container_width=True, key="dash_v84")
        selected = edit_df[edit_df["Select"] == True]
        
        if len(selected) > 0:
            act1, act2 = st.columns([3, 7])
            with act1:
                if st.button("📥 Export Selected PDF"):
                    st.download_button(label="Download Now", data=generate_custom_pdf(df_raw[df_raw['name_en'].isin(selected['name_en'])]), file_name="Report.pdf", mime="application/pdf")
            with act2.popover("🧨 BATCH DELETE"):
                st.error("🛑 DANGER ZONE"); conf_b = st.text_input("Type DELETE to confirm", key="batch_del_v84")
                if st.button("Confirm", disabled=(conf_b != "DELETE")):
                    df_raw[~df_raw["name_en"].isin(selected["name_en"].tolist())].to_sql('companies', engine, if_exists='replace', index=False); st.rerun()
    else: st.info("No records.")

# --- 5. Company Register (介面 1:1 還原 + 法定申報置底) ---
elif choice == "🏢 Company Register":
    st.header("🏢 Company Records Management")
    mode = st.radio("Mode", ["🆕 Add New", "✏️ Edit Existing", "📋 Copy Existing"], horizontal=True)
    df_all = pd.read_sql("SELECT * FROM companies", engine)
    groups = pd.read_sql("SELECT group_name FROM client_groups", engine)['group_name'].tolist()
    
    d = {'cg': "", 'en': "", 'ch': "", 'idate': None, 'place': "", 'p_oth': "", 'ci': "", 'br': "", 'type': "", 'ra': "", 'ca': "", 'rl': "", 'sl': "", 'cl': "", 'n2e': None, 'n2f': None, 'n2d': False, 'n4e': None, 'n4f': None, 'n4d': False, 'dis': None}
    target_name = None

    if mode in ["✏️ Edit Existing", "📋 Copy Existing"] and not df_all.empty:
        target_name = st.selectbox("Select Company", [""] + df_all['name_en'].tolist())
        if target_name != "":
            row = df_all[df_all['name_en'] == target_name].iloc[0]
            d = {'cg': row.get('client_group', ""), 'en': row.get('name_en', ""), 'ch': row.get('name_ch', ""), 'idate': row.get('incorp_date'), 'place': row.get('incorp_place', ""), 'p_oth': row.get('incorp_place_others', ""), 'ci': row.get('ci_no', ""), 'br': row.get('br_no', ""), 'type': row.get('co_type', ""), 'ra': row.get('reg_addr', ""), 'ca': row.get('corres_addr', ""), 'rl': row.get('round_loc', ""), 'sl': row.get('sign_loc', ""), 'cl': row.get('seal_loc', ""), 'n2e': row.get('nd2a_eff_date'), 'n2f': row.get('nd2a_file_date'), 'n2d': str(row.get('nd2a_download', "")) == 'True', 'n4e': row.get('nd4_eff_date'), 'n4f': row.get('nd4_file_date'), 'n4d': str(row.get('nd4_download', "")) == 'True', 'dis': row.get('dissolution_date')}
            if mode == "📋 Copy Existing": d['en'], d['ch'] = "", ""

    def rl(text, value): return f":red[⚠️ {text} (Required!)]" if not value or str(value).strip() == "" or value is None else text

    # --- UI Section 1: Registration ---
    st.subheader("Registration Details / 註冊詳情")
    client_group = st.selectbox(rl("Client Group / 客戶組別", d['cg']), [""] + groups, index=(groups.index(d['cg'])+1 if d['cg'] in groups else 0))
    c1, c2 = st.columns(2)
    name_en = c1.text_input(rl("English Name / 英文名稱", d['en']), value=d['en'])
    name_ch = c2.text_input(rl("Chinese Name / 中文名稱", d['ch']), value=d['ch'])
    c3, c4 = st.columns(2)
    inc_date = c3.date_input(rl("Incorp. Date (YYYY/MM/DD) / 成立日期", d['idate']), value=d['idate'])
    inc_place = c4.selectbox(rl("Incorp. Place / 成立地點", d['place']), ["", "HK", "BVI", "Others"], index=(["", "HK", "BVI", "Others"].index(d['place']) if d['place'] in ["", "HK", "BVI", "Others"] else 0))
    place_others = st.text_input(rl("Specify Others / 其他成立地點", d['p_oth']), value=d['p_oth']) if inc_place == "Others" else ""
    col_ci, col_br = st.columns(2)
    ci_no = col_ci.text_input(rl("CI No. / 公司註冊編號", d['ci']), value=d['ci'])
    br_no = col_br.text_input(rl("BR No. / 商業登記編號", d['br']), value=d['br'])
    co_type = st.selectbox("Company Type / 公司類別", ["", "Private Company", "Public Company", "Guarantee"], index=(["", "Private Company", "Public Company", "Guarantee"].index(d['type']) if d['type'] in ["", "Private Company", "Public Company", "Guarantee"] else 0))
    st.write("---")

    # --- UI Section 2: Addresses ---
    st.subheader("Addresses / 地址")
    ca1, ca2 = st.columns(2)
    reg_addr = ca1.text_area(rl("Registered Address / 註冊地址", d['ra']), value=d['ra'])
    corres_addr = ca2.text_area(rl("Correspondence Address / 通訊地址", d['ca']), value=d['ca'])

    # --- UI Section 3: Items Storage ---
    st.subheader("Items Storage / 物品存放位置")
    l1, l2, l3 = st.columns(3)
    round_l = l1.text_input(rl("Round Stamp / 小圓章", d['rl']), value=d['rl'])
    sign_l = l2.text_input(rl("Signature Chop / 簽名章", d['sl']), value=d['sl'])
    common_l = l3.text_input(rl("Common Seal / 鋼印", d['cl']), value=d['cl'])
    st.write("---")
    dis_date = st.date_input("Company Dissolution Date / 公司解散日期", value=d['dis'])

    # --- UI Section 4: Compliance Filings (UI 置底) ---
    st.write("---")
    st.subheader("Compliance Filings / 法定申報")
    # ND2A
    st.write("**📝 Company Secretary Appointment (ND2A)**")
    cc1, cc2, cc3, cc4 = st.columns([3, 3, 3, 1])
    n2e = cc1.date_input("ND2A Effective Date (YYYY/MM/DD)", value=d['n2e'], key="n2e_v84")
    n2f = cc2.date_input("Filing Date", value=d['n2f'], key="n2f_v84")
    n2_dl = (n2e + timedelta(days=15)) if n2e else ''
    cc3.info(f"Statutory Period: 15 days\n\n**Deadline: :red[{n2_dl}]**")
    n2d = cc4.checkbox("Downloaded", value=d['n2d'], key="n2d_v84")
    
    # ND4
    st.write("**📝 Company Secretary Resignation (ND4)**")
    cc5, cc6, cc7, cc8 = st.columns([3, 3, 3, 1])
    n4e = cc5.date_input("ND4 Effective Date (YYYY/MM/DD)", value=d['n4e'], key="n4e_v84")
    n4f = cc6.date_input("Filing Date", value=d['n4f'], key="n4f_v84")
    n4_dl = (n4e + timedelta(days=15)) if n4e else ''
    cc7.info(f"Statutory Period: 15 days\n\n**Deadline: :red[{n4_dl}]**")
    n4d = cc8.checkbox("Downloaded", value=d['n4d'], key="n4d_v84")
    st.write("---")

    # Save logic
    row_v84 = {'client_group': client_group, 'name_en': name_en, 'name_ch': name_ch, 'incorp_date': inc_date, 'incorp_place': inc_place, 'incorp_place_others': place_others, 'ci_no': ci_no, 'br_no': br_no, 'co_type': co_type, 'reg_addr': reg_addr, 'corres_addr': corres_addr, 'round_loc': round_l, 'sign_loc': sign_l, 'seal_loc': common_l, 'nd2a_eff_date': n2e, 'nd2a_file_date': n2f, 'nd2a_download': n2d, 'nd4_eff_date': n4e, 'nd4_file_date': n4f, 'nd4_download': n4d, 'dissolution_date': dis_date}

    if mode in ["🆕 Add New", "📋 Copy Existing"]:
        if st.button("💾 Save Record"): pd.DataFrame([row_v84]).to_sql('companies', engine, if_exists='append', index=False); st.rerun()
    else:
        u_col, d_col = st.columns(2)
        with u_col.popover("🆙 Update"):
            if st.button("Confirm"):
                df_all[df_all['name_en'] != target_name].to_sql('companies', engine, if_exists='replace', index=False)
                pd.DataFrame([row_v84]).to_sql('companies', engine, if_exists='append', index=False); st.rerun()
        with d_col.popover("🚨 DELETE"):
            st.error(f"Delete {target_name}?"); conf_s = st.text_input("Type DELETE", key="single_del_v84")
            if st.button("Confirm Delete", disabled=(conf_s != "DELETE")):
                df_all[df_all['name_en'] != target_name].to_sql('companies', engine, if_exists='replace', index=False); st.rerun()

# --- 6. Group Management (鎖定) ---
elif choice == "⚙️ Group Management":
    st.header("⚙️ Group Management")
    new_g = st.text_input("New Group Name")
    if st.button("Add Group"): pd.DataFrame([{'group_name': new_g}]).to_sql('client_groups', engine, if_exists='append', index=False); st.rerun()
    st.write("---")
    g_df = pd.read_sql("SELECT * FROM client_groups", engine)
    if not g_df.empty:
        target = st.selectbox("Select", g_df['group_name'].tolist())
        c1, c2 = st.columns(2)
        with c1.popover("✏️ Rename"):
            ren = st.text_input("New Name:"); conf_r = st.text_input("Type RENAME")
            if st.button("Confirm", disabled=(conf_r != "RENAME")):
                comp_df = pd.read_sql("SELECT * FROM companies", engine)
                comp_df.loc[comp_df['client_group'] == target, 'client_group'] = ren
                comp_df.to_sql('companies', engine, if_exists='replace', index=False)
                g_df.replace({target: ren}).to_sql('client_groups', engine, if_exists='replace', index=False); st.rerun()
        with c2.popover("🗑️ Delete"):
            if st.button("Confirm Delete"): g_df[g_df['group_name'] != target].to_sql('client_groups', engine, if_exists='replace', index=False); st.rerun()

# --- 7. Data Exchange (鎖定) ---
elif choice == "📤 Data Exchange":
    st.header("📤 Data Exchange & Backup")
    c1, c2 = st.columns(2)
    template_cols = ["client_group", "name_en", "name_ch", "incorp_date", "incorp_place", "incorp_place_others", "ci_no", "br_no", "co_type", "reg_addr", "corres_addr", "round_loc", "sign_loc", "seal_loc", "nd2a_eff_date", "nd2a_file_date", "nd2a_download", "nd4_eff_date", "nd4_file_date", "nd4_download", "dissolution_date"]
    buf_t = io.BytesIO(); pd.DataFrame(columns=template_cols).to_excel(buf_t, index=False); c1.download_button(label="📥 Template", data=buf_t.getvalue(), file_name="Template.xlsx")
    df_e = pd.read_sql("SELECT * FROM companies", engine); buf_e = io.BytesIO(); df_e.to_excel(buf_e, index=False); c2.download_button(label="📦 Export All", data=buf_e.getvalue(), file_name="Backup.xlsx")
    st.write("---")
    up = st.file_uploader("Upload", type=["xlsx"])
    if up and st.button("🚀 Confirm Bulk Upload"):
        try:
            up_df = pd.read_excel(up, engine='openpyxl', keep_default_na=False)
            mandatory = ["client_group", "name_en", "name_ch", "incorp_date", "ci_no", "br_no", "reg_addr"]
            invalid_rows = []
            for idx, row in up_df.iterrows():
                missing = [f for f in mandatory if not row.get(f) or str(row.get(f)).strip() == ""]
                if missing: invalid_rows.append(f"Row {idx+2} missing: {', '.join(missing)}")
            if invalid_rows:
                st.error("### 🛑 Upload Blocked"); [st.write(f"- {err}") for err in invalid_rows]; st.stop()
            for col in ["incorp_date", "nd2a_eff_date", "nd2a_file_date", "nd4_eff_date", "nd4_file_date", "dissolution_date"]:
                if col in up_df.columns: up_df[col] = pd.to_datetime(up_df[col], errors='coerce')
            up_df.to_sql('companies', engine, if_exists='append', index=False); st.success("✅ Uploaded!"); st.balloons()
        except Exception as e: st.error(f"Error: {e}")
