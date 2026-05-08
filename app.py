import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import io
from weasyprint import HTML

# --- 1. Database Connection (鎖定 V32 穩定邏輯) ---
try:
    DB_URL = st.secrets["DB_URL"]
    engine = create_engine(DB_URL)
except:
    st.error("❌ Please check DB_URL in Secrets")
    st.stop()

# --- 2. Navigation ---
st.set_page_config(page_title="ERP Cloud V39", layout="wide")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "⚙️ Group Management", "📤 Data Exchange"])

# 定義必填欄位
REQUIRED_COLS = ["client_group", "name_en", "name_ch", "incorp_date", "incorp_place", "ci_no", "br_no", "co_type", "reg_addr", "corres_addr", "round_loc", "sign_loc", "seal_loc"]

# --- 3. PDF 生成函式 (修復中文 + 強化標題) ---
def generate_custom_pdf(selected_df):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    def fmt_date(val):
        if pd.isna(val) or str(val).strip().lower() in ["none", "nan", "n/a", ""]:
            return "N/A"
        try:
            return pd.to_datetime(val).strftime('%Y-%m-%d')
        except:
            return str(val)

    # 加入 Google Fonts 連結解決雲端環境無中文字型問題
    html_content = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+HK:wght@400;700&display=swap" rel="stylesheet">
        <style>
            @page {{ size: A4; margin: 15mm; }}
            body {{ 
                font-family: 'Noto Sans HK', sans-serif; 
                color: #2c3e50; 
                line-height: 1.6; 
            }}
            .header {{ text-align: center; border-bottom: 3px solid #34495e; padding-bottom: 10px; margin-bottom: 25px; }}
            .header h1 {{ font-size: 24pt; margin: 0; }}
            .company-card {{ page-break-inside: avoid; border: 1px solid #dcdde1; border-radius: 10px; padding: 30px; margin-bottom: 35px; background-color: #fbfbfb; }}
            .name-en {{ font-size: 22pt; font-weight: bold; color: #2980b9; margin: 0; }}
            .name-ch {{ font-size: 18pt; font-weight: bold; color: #333; margin-top: 5px; margin-bottom: 20px; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 11pt; }}
            th {{ text-align: left; width: 45%; color: #7f8c8d; border-bottom: 1px solid #f1f2f6; padding: 10px 0; font-weight: 700; }}
            td {{ border-bottom: 1px solid #f1f2f6; padding: 10px 0; color: #2c3e50; }}
            .section-title {{ background: #f1f4f6; padding: 8px 15px; font-weight: bold; font-size: 13pt; margin-top: 25px; border-left: 6px solid #3498db; color: #2c3e50; }}
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
            <div class="section-title">Registration Details</div>
            <table>
                <tr><th>Client Group / 客戶組別</th><td>{row.get('client_group','')}</td></tr>
                <tr><th>Incorp. Date / 成立日期</th><td>{fmt_date(row.get('incorp_date'))}</td></tr>
                <tr><th>Incorp. Place / 成立地點</th><td>{row.get('incorp_place','')}</td></tr>
                <tr><th>CI No. / 公司註冊編號</th><td>{row.get('ci_no','')}</td></tr>
                <tr><th>BR No. / 商業登記編號</th><td>{row.get('br_no','')}</td></tr>
                <tr><th>Company Type / 公司類別</th><td>{row.get('co_type','')}</td></tr>
            </table>
            <div class="section-title">Compliance Filings</div>
            <table>
                <tr><th>ND2A Effective Date</th><td>{fmt_date(row.get('nd2a_eff_date'))}</td></tr>
                <tr><th>ND4 Effective Date</th><td>{fmt_date(row.get('nd4_eff_date'))}</td></tr>
            </table>
            <div class="section-title">Addresses & Items</div>
            <table>
                <tr><th>Registered Address</th><td>{row.get('reg_addr','')}</td></tr>
                <tr><th>Correspondence Address</th><td>{row.get('corres_addr','')}</td></tr>
                <tr><th>Round Stamp Location</th><td>{row.get('round_loc','')}</td></tr>
                <tr><th>Signature Chop Location</th><td>{row.get('sign_loc','')}</td></tr>
                <tr><th>Common Seal Location</th><td>{row.get('seal_loc','')}</td></tr>
            </table>
        </div>"""
    html_content += "</body></html>"
    return HTML(string=html_content).write_pdf()

# --- 4. Dashboard (去時間化 + 自選 PDF) ---
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
        date_cols = ["incorp_date", "nd2a_eff_date", "nd2a_file_date", "nd4_eff_date", "nd4_file_date", "dissolution_date"]
        for col in date_cols:
            if col in df_display.columns:
                df_display[col] = pd.to_datetime(df_display[col], errors='coerce').dt.date

        df_display.insert(0, "Select", st.session_state.select_state)
        edited_df = st.data_editor(
            df_display, 
            column_config={
                "Select": st.column_config.CheckboxColumn("Select", default=False),
                "incorp_date": st.column_config.DateColumn("Incorp Date", format="YYYY-MM-DD"),
                "nd2a_eff_date": st.column_config.DateColumn("ND2A Eff", format="YYYY-MM-DD"),
                "nd4_eff_date": st.column_config.DateColumn("ND4 Eff", format="YYYY-MM-DD"),
            }, 
            disabled=[c for c in df_display.columns if c != "Select"], 
            hide_index=True, use_container_width=True, key="dashboard_editor_v39"
        )
        
        selected_rows = edited_df[edited_df["Select"] == True]
        
        if len(selected_rows) > 0:
            st.info(f"已選取 {len(selected_rows)} 筆紀錄")
            act1, act2 = st.columns([3, 7])
            with act1:
                if st.button("📥 Export Selected to PDF"):
                    final_selected = df_raw[df_raw['name_en'].isin(selected_rows['name_en'])]
                    pdf_bytes = generate_custom_pdf(final_selected)
                    st.download_button(label="Click to Download PDF", data=pdf_bytes, file_name="Portfolio_Report.pdf", mime="application/pdf")
            with act2.popover("🧨 BATCH DELETE"):
                st.error("### 🛑 DANGER ZONE")
                user_conf = st.text_input("Type DELETE to confirm", key="batch_del_input")
                if st.button("🔥 Confirm Delete", disabled=(user_conf != "DELETE")):
                    to_del = selected_rows["name_en"].tolist()
                    df_raw[~df_raw["name_en"].isin(to_del)].to_sql('companies', engine, if_exists='replace', index=False)
                    st.success("Deleted!"); st.rerun()
    else: st.info("No records.")

# --- 5. Company Register (維持鎖定) ---
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
        with cb2.popover("🚨 DELETE"):
            confirm_text = st.text_input("Type DELETE to confirm", key="single_del_input")
            if st.button("🔥 DELETE NOW", disabled=(confirm_text != "DELETE")):
                df_all[df_all['name_en'] != target_name].to_sql('companies', engine, if_exists='replace', index=False)
                st.warning("Deleted."); st.rerun()

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
            conf = st.text_input("Type DELETE to confirm", key="group_del_input")
            if st.button("Confirm Delete Group", disabled=(conf != "DELETE")):
                g_df[g_df['group_name'] != target_g].to_sql('client_groups', engine, if_exists='replace', index=False)
                st.rerun()

# --- 7. Data Exchange ---
elif choice == "📤 Data Exchange":
    st.header("📤 Data Exchange & Backup")
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
    col_ex2.download_button(label="📦 Export All Data (Backup)", data=buffer_all.getvalue(), file_name="Full_Backup.xlsx")

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
