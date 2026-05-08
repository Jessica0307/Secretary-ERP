import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
import io
from weasyprint import HTML

# --- 1. Database Connection ---
try:
    DB_URL = st.secrets["DB_URL"]
    engine = create_engine(DB_URL)
except:
    st.error("❌ Please check DB_URL in Secrets")
    st.stop()

# --- 2. Navigation ---
st.set_page_config(page_title="ERP Cloud V49", layout="wide")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "⚙️ Group Management", "📤 Data Exchange"])

# --- PDF 生成函式 (鎖定 V42 規格) ---
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
            <div class="section-title">Registration Details</div>
            <table>
                <tr><th>Client Group</th><td>{row.get('client_group','')}</td></tr>
                <tr><th>Incorp. Date (YYYY/MM/DD)</th><td>{fmt_date(row.get('incorp_date'))}</td></tr>
                <tr><th>CI No. / BR No.</th><td>{row.get('ci_no','')} / {row.get('br_no','')}</td></tr>
            </table>
            <div class="section-title">Addresses</div>
            <table>
                <tr><th>Registered Address</th><td>{row.get('reg_addr','')}</td></tr>
                <tr><th>Correspondence Address</th><td>{row.get('corres_addr','')}</td></tr>
            </table>
            <div class="section-title">Items Storage</div>
            <table>
                <tr><th>Round Stamp / Sign / Common Seal</th><td>{row.get('round_loc','')} / {row.get('sign_loc','')} / {row.get('seal_loc','')}</td></tr>
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
        df_display = df_filtered.copy()
        for col in ["incorp_date", "nd2a_eff_date", "nd4_eff_date"]:
            if col in df_display.columns: df_display[col] = pd.to_datetime(df_display[col], errors='coerce').dt.date
        st.data_editor(df_display, hide_index=True, use_container_width=True)
    else: st.info("No records.")

# --- 4. Company Register (根據截圖 100% 復原) ---
elif choice == "🏢 Company Register":
    st.header("🏢 Company Records Management")
    mode = st.radio("Mode", ["🆕 Add New", "✏️ Edit Existing", "📋 Copy Existing"], horizontal=True)
    df_all = pd.read_sql("SELECT * FROM companies", engine)
    groups = pd.read_sql("SELECT group_name FROM client_groups", engine)['group_name'].tolist()
    
    # 基礎數據與模式預載
    d = {'cg': "", 'en': "", 'ch': "", 'idate': None, 'place': "", 'p_oth': "", 'ci': "", 'br': "", 'type': "", 'ra': "", 'ca': "", 'rl': "", 'sl': "", 'cl': "", 'n2e': None, 'n2f': None, 'n2d': False, 'n4e': None, 'n4f': None, 'n4d': False, 'dis': None}
    target_name = None
    if mode in ["✏️ Edit Existing", "📋 Copy Existing"] and not df_all.empty:
        target_name = st.selectbox("Select Company", [""] + df_all['name_en'].tolist())
        if target_name != "":
            row = df_all[df_all['name_en'] == target_name].iloc[0]
            d = {'cg': row.get('client_group', ""), 'en': row.get('name_en', ""), 'ch': row.get('name_ch', ""), 'idate': row.get('incorp_date'), 'place': row.get('incorp_place', ""), 'p_oth': row.get('incorp_place_others', ""), 'ci': row.get('ci_no', ""), 'br': row.get('br_no', ""), 'type': row.get('co_type', ""), 'ra': row.get('reg_addr', ""), 'ca': row.get('corres_addr', ""), 'rl': row.get('round_loc', ""), 'sl': row.get('sign_loc', ""), 'cl': row.get('seal_loc', ""), 'n2e': row.get('nd2a_eff_date'), 'n2f': row.get('nd2a_file_date'), 'n2d': str(row.get('nd2a_download', "")) == 'True', 'n4e': row.get('nd4_eff_date'), 'n4f': row.get('nd4_file_date'), 'n4d': str(row.get('nd4_download', "")) == 'True', 'dis': row.get('dissolution_date')}
            if mode == "📋 Copy Existing": d['en'], d['ch'] = "", ""

    def red_label(text, value): return f":red[⚠️ {text} (Required!)]" if not value or str(value).strip() == "" or value is None else text

    # --- Part 1: Basic Info ---
    client_group = st.selectbox(red_label("Group", d['cg']), [""] + groups, index=(groups.index(d['cg'])+1 if d['cg'] in groups else 0))
    c1, c2 = st.columns(2)
    name_en = c1.text_input(red_label("English Name", d['en']), value=d['en'])
    name_ch = c2.text_input(red_label("Chinese Name", d['ch']), value=d['ch'])
    c3, c4 = st.columns(2)
    inc_date = c3.date_input(red_label("Incorp Date", d['idate']), value=d['idate'])
    places = ["", "HK", "BVI", "Others"]; inc_place = c4.selectbox(red_label("Place", d['place']), places, index=(places.index(d['place']) if d['place'] in places else 0))
    place_others = st.text_input(red_label("Specify Others", d['p_oth']), value=d['p_oth']) if inc_place == "Others" else ""
    col_ci, col_br = st.columns(2)
    ci_no = col_ci.text_input(red_label("CI", d['ci']), value=d['ci']); br_no = col_br.text_input(red_label("BR", d['br']), value=d['br'])
    types = ["", "Private Company", "Public Company", "Company Limited by Guarantee"]; co_type = st.selectbox(red_label("Type", d['type']), types, index=(types.index(d['type']) if d['type'] in types else 0))
    st.write("---")

    # --- Part 2: ND2A & ND4 (完全對應截圖) ---
    st.subheader("📝 Company Secretary Appointment (ND2A)")
    cc1, cc2, cc3, cc4 = st.columns([3, 3, 3, 1])
    n2e = cc1.date_input("Effective Date (Appt)", value=d['n2e'])
    n2f = cc2.date_input("Filing Date (ND2A)", value=d['n2f'])
    cc3.info("Statutory Period: 15 days")
    n2d = cc4.checkbox("Downloaded", value=d['n2d'], key="n2d_chk")

    st.subheader("📝 Company Secretary Resignation (ND4)")
    cc5, cc6, cc7, cc8 = st.columns([3, 3, 3, 1])
    n4e = cc5.date_input("Effective Date (Resign)", value=d['n4e'])
    n4f = cc6.date_input("Filing Date (ND4)", value=d['n4f'])
    cc7.info("Statutory Period: 15 days")
    n4d = cc8.checkbox("Downloaded", value=d['n4d'], key="n4d_chk")
    st.write("---")

    # --- Part 3: Address & Seal (完全對應截圖) ---
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

    # --- Part 4: Save Actions ---
    if mode in ["🆕 Add New", "📋 Copy Existing"]:
        with st.popover("💾 Save To Cloud"):
            if st.button("Confirm Save Now"):
                pd.DataFrame([{'client_group': client_group, 'name_en': name_en, 'name_ch': name_ch, 'incorp_date': inc_date, 'incorp_place': inc_place, 'incorp_place_others': place_others, 'ci_no': ci_no, 'br_no': br_no, 'co_type': co_type, 'reg_addr': reg_addr, 'corres_addr': corres_addr, 'round_loc': round_l, 'sign_loc': sign_l, 'seal_loc': common_l, 'nd2a_eff_date': n2e, 'nd2a_file_date': n2f, 'nd2a_download': n2d, 'nd4_eff_date': n4e, 'nd4_file_date': n4f, 'nd4_download': n4d, 'dissolution_date': dis_date}]).to_sql('companies', engine, if_exists='append', index=False); st.rerun()
    else:
        btn_c1, btn_c2 = st.columns(2)
        with btn_c1.popover("🆙 Update Record"):
            if st.button("Confirm Update Now"):
                df_f = df_all[df_all['name_en'] != target_name]
                up_r = {'client_group': client_group, 'name_en': name_en, 'name_ch': name_ch, 'incorp_date': inc_date, 'incorp_place': inc_place, 'incorp_place_others': place_others, 'ci_no': ci_no, 'br_no': br_no, 'co_type': co_type, 'reg_addr': reg_addr, 'corres_addr': corres_addr, 'round_loc': round_l, 'sign_loc': sign_l, 'seal_loc': common_l, 'nd2a_eff_date': n2e, 'nd2a_file_date': n2f, 'nd2a_download': n2d, 'nd4_eff_date': n4e, 'nd4_file_date': n4f, 'nd4_download': n4d, 'dissolution_date': dis_date}
                pd.concat([df_f, pd.DataFrame([up_r])], ignore_index=True).to_sql('companies', engine, if_exists='replace', index=False); st.rerun()
        with btn_c2.popover("🚨 DELETE Record"):
            st.error(f"Delete: {target_name}?"); conf = st.text_input("Type DELETE to confirm")
            if st.button("Delete Permanently", disabled=(conf != "DELETE")):
                df_all[df_all['name_en'] != target_name].to_sql('companies', engine, if_exists='replace', index=False); st.rerun()

# --- 其他 Section (鎖定 V42/V45 原貌) ---
# ... (Group, Exchange 保持不變) ...
