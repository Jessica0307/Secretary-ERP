import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
import io
from weasyprint import HTML

# --- 1. Database Connection (鎖定) ---
try:
    DB_URL = st.secrets["DB_URL"]
    engine = create_engine(DB_URL)
except:
    st.error("❌ Please check DB_URL in Secrets")
    st.stop()

# --- 2. Navigation ---
st.set_page_config(page_title="ERP Cloud V51", layout="wide")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "⚙️ Group Management", "📤 Data Exchange"])

# --- PDF 生成函式 (鎖定 V42 規格：逐項列出 + YYYY/MM/DD) ---
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
            @page {{ size: A4; margin: 15mm; }}
            body {{ font-family: 'Noto Sans TC', sans-serif; color: #2c3e50; line-height: 1.5; }}
            .report-header {{ display: table-header-group; text-align: center; width: 100%; }}
            .header-content {{ border-bottom: 2px solid #34495e; padding-bottom: 10px; margin-bottom: 20px; text-align: center; }}
            .company-card {{ page-break-after: always; page-break-inside: avoid; border: 1px solid #dcdde1; border-radius: 8px; padding: 25px; background-color: #fbfbfb; }}
            .company-card:last-child {{ page-break-after: auto; }}
            .name-en {{ font-size: 18pt; font-weight: bold; color: #2980b9; }}
            .name-ch {{ font-size: 15pt; color: #333; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 5px; font-size: 10pt; }}
            th {{ text-align: left; width: 48%; color: #7f8c8d; border-bottom: 1px solid #f1f2f6; padding: 8px 0; font-weight: bold; }}
            td {{ border-bottom: 1px solid #f1f2f6; padding: 8px 0; color: #2c3e50; }}
            .section-title {{ background: #f1f4f6; padding: 5px 12px; font-weight: bold; font-size: 11pt; margin-top: 15px; border-left: 4px solid #3498db; }}
        </style>
    </head>
    <body>
        <table style="width: 100%;">
            <thead class="report-header">
                <tr><td><div class="header-content"><h1 style="margin: 0; font-size: 20pt;">Corporate Portfolio Report</h1>
                <p style="margin: 5px 0; font-size: 10pt; color: #7f8c8d;">Generated on: {now}</p></div></td></tr>
            </thead>
            <tbody><tr><td>
    """
    for _, row in selected_df.iterrows():
        html_content += f"""
        <div class="company-card">
            <div class="name-en">{row.get('name_en','')}</div>
            <div class="name-ch">{row.get('name_ch','')}</div>
            <div class="section-title">Registration Details / 註冊詳情</div>
            <table>
                <tr><th>Client Group / 客戶組別</th><td>{row.get('client_group','')}</td></tr>
                <tr><th>Incorp. Date (YYYY/MM/DD) / 成立日期</th><td>{fmt_date(row.get('incorp_date'))}</td></tr>
                <tr><th>Incorp. Place / 成立地點</th><td>{row.get('incorp_place','')}</td></tr>
                <tr><th>CI No. / 公司註冊編號</th><td>{row.get('ci_no','')}</td></tr>
                <tr><th>BR No. / 商業登記編號</th><td>{row.get('br_no','')}</td></tr>
                <tr><th>Company Type / 公司類別</th><td>{row.get('co_type','')}</td></tr>
            </table>
            <div class="section-title">Compliance Filings / 法定申報</div>
            <table>
                <tr><th>ND2A Effective Date (YYYY/MM/DD)</th><td>{fmt_date(row.get('nd2a_eff_date'))}</td></tr>
                <tr><th>ND4 Effective Date (YYYY/MM/DD)</th><td>{fmt_date(row.get('nd4_eff_date'))}</td></tr>
            </table>
            <div class="section-title">Addresses / 地址</div>
            <table>
                <tr><th>Registered Address / 註冊地址</th><td>{row.get('reg_addr','')}</td></tr>
                <tr><th>Correspondence Address / 通訊地址</th><td>{row.get('corres_addr','')}</td></tr>
            </table>
            <div class="section-title">Items Storage / 物品存放位置</div>
            <table>
                <tr><th>Round Stamp / 小圓章</th><td>{row.get('round_loc','')}</td></tr>
                <tr><th>Signature Chop / 簽名章</th><td>{row.get('sign_loc','')}</td></tr>
                <tr><th>Common Seal / 鋼印</th><td>{row.get('seal_loc','')}</td></tr>
            </table>
        </div>"""
    html_content += "</td></tr></tbody></table></body></html>"
    return HTML(string=html_content).write_pdf()

# --- 3. Dashboard ---
if choice == "📊 Dashboard":
    st.header("📊 Compliance Overview")
    df_raw = pd.read_sql("SELECT * FROM companies", engine)
    groups = pd.read_sql("SELECT group_name FROM client_groups", engine)['group_name'].tolist()
    if not df_raw.empty:
        t1, t2, t3, t4 = st.columns([3, 2, 2, 5])
        filter_g = t1.selectbox("🔍 Filter by Group", ["All Groups"] + groups)
        if t2.button("🔄 Refresh"): st.rerun()
        df_filtered = df_raw if filter_g == "All Groups" else df_raw[df_raw['client_group'] == filter_g]
        if 'select_state' not in st.session_state: st.session_state.select_state = False
        if t3.button("✅ Select All Shown"): st.session_state.select_state = True; st.rerun()
        if t4.button("🧹 Clear All"): st.session_state.select_state = False; st.rerun()
        df_display = df_filtered.copy()
        for col in ["incorp_date", "nd2a_eff_date", "nd4_eff_date"]:
            if col in df_display.columns: df_display[col] = pd.to_datetime(df_display[col], errors='coerce').dt.date
        df_display.insert(0, "Select", st.session_state.select_state)
        edited_df = st.data_editor(df_display, column_config={"Select": st.column_config.CheckboxColumn("Select", default=False)}, hide_index=True, use_container_width=True, key="dashboard_v51")
        selected_rows = edited_df[edited_df["Select"] == True]
        if len(selected_rows) > 0:
            if st.button("📥 Export Selected to PDF"):
                final_selected = df_raw[df_raw['name_en'].isin(selected_rows['name_en'])]
                st.download_button(label="Download PDF", data=generate_custom_pdf(final_selected), file_name="Report.pdf", mime="application/pdf")
    else: st.info("No records.")

# --- 4. Company Register (UI 鎖定截圖與紅框) ---
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

    def red_label(text, value): return f":red[⚠️ {text} (Required!)]" if not value or str(value).strip() == "" or value is None else text

    # Form Fields
    client_group = st.selectbox(red_label("Group", d['cg']), [""] + groups, index=(groups.index(d['cg'])+1 if d['cg'] in groups else 0))
    c1, c2 = st.columns(2)
    name_en = c1.text_input(red_label("English Name", d['en']), value=d['en'])
    name_ch = c2.text_input(red_label("Chinese Name", d['ch']), value=d['ch'])
    c3, c4 = st.columns(2)
    inc_date = c3.date_input(red_label("Incorp Date", d['idate']), value=d['idate'])
    places = ["", "HK", "BVI", "Others"]; inc_place = c4.selectbox(red_label("Place", d['place']), places, index=(places.index(d['place']) if d['place'] in places else 0))
    place_others = st.text_input(red_label("Specify Others", d['p_oth']), value=d['p_oth']) if inc_place == "Others" else ""
    col_ci, col_br = st.columns(2)
    ci_no = col_ci.text_input(red_label("CI No.", d['ci']), value=d['ci']); br_no = col_br.text_input(red_label("BR No.", d['br']), value=d['br'])
    types = ["", "Private Company", "Public Company", "Company Limited by Guarantee"]; co_type = st.selectbox(red_label("Company Type", d['type']), types, index=(types.index(d['type']) if d['type'] in types else 0))
    st.write("---")

    # ND2A & ND4 (鎖定截圖佈局)
    st.subheader("📝 Company Secretary Appointment (ND2A)")
    cc1, cc2, cc3, cc4 = st.columns([3, 3, 3, 1])
    n2e = cc1.date_input("Effective Date (Appt)", value=d['n2e'])
    n2f = cc2.date_input("Filing Date (ND2A)", value=d['n2f'])
    cc3.info("Statutory Period: 15 days")
    n2d = cc4.checkbox("Downloaded", value=d['n2d'], key="n2d_v51")
    st.subheader("📝 Company Secretary Resignation (ND4)")
    cc5, cc6, cc7, cc8 = st.columns([3, 3, 3, 1])
    n4e = cc5.date_input("Effective Date (Resign)", value=d['n4e'])
    n4f = cc6.date_input("Filing Date (ND4)", value=d['n4f'])
    cc7.info("Statutory Period: 15 days")
    n4d = cc8.checkbox("Downloaded", value=d['n4d'], key="n4d_v51")
    st.write("---")

    # Address & Seal
    st.subheader("📍 Address & Contact")
    ca1, ca2 = st.columns(2)
    reg_addr = ca1.text_area(red_label("Registered Office Address", d['ra']), value=d['ra'])
    corres_addr = ca2.text_area(red_label("Correspondence Address", d['ca']), value=d['ca'])
    st.subheader("📔 Seal Storage")
    l1, l2, l3 = st.columns(3)
    round_l = l1.text_input(red_label("Round Chop Location", d['rl']), value=d['rl'])
    sign_l = l2.text_input(red_label("Signature Chop Location", d['sl']), value=d['sl'])
    common_l = l3.text_input(red_label("Common Seal Location", d['cl']), value=d['cl'])
    st.write("---")
    dis_date = st.date_input("Company Dissolution Date", value=d['dis'])

    # Save
    with st.popover("💾 Save To Cloud"):
        if st.button("Confirm Save"):
            row = {'client_group': client_group, 'name_en': name_en, 'name_ch': name_ch, 'incorp_date': inc_date, 'incorp_place': inc_place, 'incorp_place_others': place_others, 'ci_no': ci_no, 'br_no': br_no, 'co_type': co_type, 'reg_addr': reg_addr, 'corres_addr': corres_addr, 'round_loc': round_l, 'sign_loc': sign_l, 'seal_loc': common_l, 'nd2a_eff_date': n2e, 'nd2a_file_date': n2f, 'nd2a_download': n2d, 'nd4_eff_date': n4e, 'nd4_file_date': n4f, 'nd4_download': n4d, 'dissolution_date': dis_date}
            if mode == "✏️ Edit Existing": df_all[df_all['name_en'] != target_name].to_sql('companies', engine, if_exists='replace', index=False)
            pd.DataFrame([row]).to_sql('companies', engine, if_exists='append', index=False); st.rerun()

# --- 5. Group Management (連動改名) ---
elif choice == "⚙️ Group Management":
    st.header("⚙️ Client Group Management")
    new_g = st.text_input("New Name"); 
    if st.button("Add"): pd.DataFrame([{'group_name': new_g}]).to_sql('client_groups', engine, if_exists='append', index=False); st.rerun()
    st.write("---")
    g_df = pd.read_sql("SELECT * FROM client_groups", engine)
    if not g_df.empty:
        target = st.selectbox("Select", g_df['group_name'].tolist())
        c1, c2 = st.columns(2)
        with c1.popover("✏️ Rename"):
            ren = st.text_input("New:"); conf = st.text_input("Type RENAME")
            if st.button("Rename", disabled=(conf != "RENAME")):
                pd.read_sql("SELECT * FROM companies", engine).replace({target: ren}).to_sql('companies', engine, if_exists='replace', index=False)
                g_df.replace({target: ren}).to_sql('client_groups', engine, if_exists='replace', index=False); st.rerun()
        with c2.popover("🗑️ Delete"):
            if st.button("Delete"): g_df[g_df['group_name'] != target].to_sql('client_groups', engine, if_exists='replace', index=False); st.rerun()

# --- 6. Data Exchange (恢復完整 2 欄佈局 + 模板 + 備份 + 上傳) ---
elif choice == "📤 Data Exchange":
    st.header("📤 Data Exchange & Backup")
    
    st.subheader("1. Download & Backup")
    col_ex1, col_ex2 = st.columns(2)
    # 左：模板
    template_cols = ["client_group", "name_en", "name_ch", "incorp_date", "incorp_place", "incorp_place_others", "ci_no", "br_no", "co_type", "reg_addr", "corres_addr", "round_loc", "sign_loc", "seal_loc", "nd2a_eff_date", "nd2a_file_date", "nd2a_download", "nd4_eff_date", "nd4_file_date", "nd4_download", "dissolution_date"]
    tmp_df = pd.DataFrame(columns=template_cols)
    buf_tmp = io.BytesIO()
    with pd.ExcelWriter(buf_tmp, engine='xlsxwriter') as writer: tmp_df.to_excel(writer, index=False)
    col_ex1.download_button(label="📥 Download Blank Template", data=buf_tmp.getvalue(), file_name="Template.xlsx")
    
    # 右：全備份
    df_all_export = pd.read_sql("SELECT * FROM companies", engine)
    buf_all = io.BytesIO()
    with pd.ExcelWriter(buf_all, engine='xlsxwriter') as writer: df_all_export.to_excel(writer, index=False)
    col_ex2.download_button(label="📦 Export All Backup", data=buf_all.getvalue(), file_name=f"Full_Backup_{datetime.now().strftime('%Y%m%d')}.xlsx")
    
    st.write("---")
    # 下：上傳
    st.subheader("2. Upload & Bulk Import")
    up = st.file_uploader("Upload Excel File", type=["xlsx"])
    if up:
        try:
            up_df = pd.read_excel(up, engine='openpyxl', keep_default_na=False)
            if st.button("🚀 Confirm Bulk Upload"):
                for col in ["incorp_date", "nd2a_eff_date", "nd2a_file_date", "nd4_eff_date", "nd4_file_date", "dissolution_date"]:
                    if col in up_df.columns: up_df[col] = pd.to_datetime(up_df[col], errors='coerce')
                up_df.to_sql('companies', engine, if_exists='append', index=False); st.success("Uploaded!"); st.rerun()
        except Exception as e: st.error(f"Error: {e}")
