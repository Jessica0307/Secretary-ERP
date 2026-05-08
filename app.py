import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import io

# 嘗試匯入 weasyprint，如果未裝好就出提示
try:
    from weasyprint import HTML
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

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

# 定義必填欄位
REQUIRED_COLS = ["client_group", "name_en", "name_ch", "incorp_date", "incorp_place", "ci_no", "br_no", "co_type", "reg_addr", "corres_addr", "round_loc", "sign_loc", "seal_loc"]

# --- 3. Data Exchange (V32 基礎 + PDF 匯出功能) ---
if choice == "📤 Data Exchange":
    st.header("📤 Data Exchange & Backup")
    
    st.subheader("1. PDF Portfolio Report (專業排版)")
    if not PDF_SUPPORT:
        st.error("❌ PDF 模組未安裝成功。請確保 requirements.txt 有 weasyprint，且有 packages.txt。")
    else:
        if st.button("📄 Generate Professional PDF Report"):
            df_all = pd.read_sql("SELECT * FROM companies", engine)
            if not df_all.empty:
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                html_string = f"""
                <html>
                <head>
                    <style>
                        @page {{ size: A4; margin: 15mm; }}
                        body {{ font-family: sans-serif; color: #2c3e50; }}
                        .header {{ text-align: center; border-bottom: 2px solid #34495e; padding-bottom: 10px; }}
                        .company-card {{ page-break-inside: avoid; border: 1px solid #dcdde1; padding: 15px; margin-top: 20px; background: #f9f9f9; border-radius: 5px; }}
                        .name-en {{ font-size: 16pt; font-weight: bold; color: #2980b9; }}
                        .name-ch {{ font-size: 14pt; color: #34495e; }}
                        .info {{ width: 100%; font-size: 10pt; margin-top: 10px; }}
                        .info th {{ text-align: left; width: 30%; color: #7f8c8d; border-bottom: 1px solid #eee; }}
                        .info td {{ border-bottom: 1px solid #eee; padding: 3px 0; }}
                    </style>
                </head>
                <body>
                    <div class="header"><h1>Corporate Portfolio Report</h1><p>Generated: {now}</p></div>
                """
                for _, row in df_all.iterrows():
                    html_string += f"""
                    <div class="company-card">
                        <div class="name-en">{row.get('name_en','')}</div>
                        <div class="name-ch">{row.get('name_ch','')}</div>
                        <table class="info">
                            <tr><th>Group</th><td>{row.get('client_group','')}</td></tr>
                            <tr><th>Incorp. Date</th><td>{row.get('incorp_date','')} ({row.get('incorp_place','')})</td></tr>
                            <tr><th>CI / BR No.</th><td>{row.get('ci_no','')} / {row.get('br_no','')}</td></tr>
                            <tr><th>Reg. Address</th><td>{row.get('reg_addr','')}</td></tr>
                            <tr><th>Chops Location</th><td>{row.get('round_loc','')} / {row.get('sign_loc','')} / {row.get('seal_loc','')}</td></tr>
                        </table>
                    </div>"""
                html_string += "</body></html>"
                pdf_file = HTML(string=html_string).write_pdf()
                st.download_button("📥 Download PDF Report", data=pdf_file, file_name="Company_Portfolio.pdf", mime="application/pdf")
            else:
                st.warning("No data found.")

    st.write("---")
    st.subheader("2. Excel Backup & Templates (V32)")
    col_ex1, col_ex2 = st.columns(2)
    template_cols = ["client_group", "name_en", "name_ch", "incorp_date", "incorp_place", "incorp_place_others", "ci_no", "br_no", "co_type", "reg_addr", "corres_addr", "round_loc", "sign_loc", "seal_loc", "nd2a_eff_date", "nd2a_file_date", "nd2a_download", "nd4_eff_date", "nd4_file_date", "nd4_download", "dissolution_date"]
    tmp_df = pd.DataFrame(columns=template_cols)
    buf_tmp = io.BytesIO()
    with pd.ExcelWriter(buf_tmp, engine='xlsxwriter') as wr: tmp_df.to_excel(wr, index=False)
    col_ex1.download_button("📥 Download Template", data=buf_tmp.getvalue(), file_name="Template.xlsx")
    
    df_all_export = pd.read_sql("SELECT * FROM companies", engine)
    buf_all = io.BytesIO()
    with pd.ExcelWriter(buf_all, engine='xlsxwriter') as wr: df_all_export.to_excel(wr, index=False)
    col_ex2.download_button("📦 Backup All (Excel)", data=buf_all.getvalue(), file_name="Backup.xlsx")

    st.write("---")
    st.subheader("3. Upload")
    uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"])
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
                st.success("✅ Success!"); st.rerun()
        except Exception as e: st.error(f"Error: {e}")

# --- 4. Company Register (100% 鎖定第 32 版安全確認邏輯) ---
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
    c1, c2 = st.columns(2); name_en = c1.text_input(red_label("English Name", d['en']), value=d['en']); name_ch = c2.text_input(red_label("Chinese Name", d['ch']), value=d['ch'])
    c3, c4 = st.columns(2); inc_date = c3.date_input(red_label("Incorp Date", d['idate']), value=d['idate']); places = ["", "HK", "BVI", "Cayman Island", "Others"]; p_idx = places.index(d['place']) if d['place'] in places else 0; inc_place = c4.selectbox(red_label("Place", d['place']), places, index=p_idx); place_others = st.text_input("Specify", value=d['p_oth']) if inc_place == "Others" else ""
    st.write("---")
    ci_no = st.text_input(red_label("CI", d['ci']), value=d['ci']); br_no = st.text_input(red_label("BR", d['br']), value=d['br']); types = ["", "Private Company", "Public Company", "Company Limited by Guarantee"]; t_idx = types.index(d['type']) if d['type'] in types else 0; co_type = st.selectbox(red_label("Type", d['type']), types, index=t_idx)
    st.write("---")
    n2e = st.date_input("ND2A Eff", value=d['n2e']); n4e = st.date_input("ND4 Eff", value=d['n4e'])
    st.write("---")
    reg_addr = st.text_area(red_label("Reg Addr", d['ra']), value=d['ra']); corres_addr = st.text_area(red_label("Cor Addr", d['ca']), value=d['ca'])
    l1, l2, l3 = st.columns(3); round_l = l1.text_input(red_label("Round", d['rl']), value=d['rl']); sign_l = l2.text_input(red_label("Sign", d['sl']), value=d['sl']); common_l = l3.text_input(red_label("Common", d['cl']), value=d['cl'])
    
    if mode in ["🆕 Add New", "📋 Copy Existing"]:
        if st.button("💾 Save Record"):
            pd.DataFrame([{'client_group': client_group, 'name_en': name_en, 'name_ch': name_ch, 'incorp_date': inc_date, 'incorp_place': inc_place, 'incorp_place_others': place_others, 'ci_no': ci_no, 'br_no': br_no, 'co_type': co_type, 'reg_addr': reg_addr, 'corres_addr': corres_addr, 'round_loc': round_l, 'sign_loc': sign_l, 'seal_loc': common_l, 'nd2a_eff_date': n2e, 'nd4_eff_date': n4e}]).to_sql('companies', engine, if_exists='append', index=False)
            st.success("Saved!"); st.rerun()
    else:
        cb1, cb2 = st.columns(2)
        if cb1.button("🆙 Update"):
            df_f = df_all[df_all['name_en'] != target_name]
            up_r = {'client_group': client_group, 'name_en': name_en, 'name_ch': name_ch, 'incorp_date': inc_date, 'incorp_place': inc_place, 'incorp_place_others': place_others, 'ci_no': ci_no, 'br_no': br_no, 'co_type': co_type, 'reg_addr': reg_addr, 'corres_addr': corres_addr, 'round_loc': round_l, 'sign_loc': sign_l, 'seal_loc': common_l, 'nd2a_eff_date': n2e, 'nd4_eff_date': n4e}
            pd.concat([df_f, pd.DataFrame([up_r])]).to_sql('companies', engine, if_exists='replace', index=False); st.success("Updated!"); st.rerun()
        with cb2.popover("🚨 DELETE"):
            conf = st.text_input("Type DELETE to confirm")
            if st.button("🔥 Confirm Delete", disabled=(conf != "DELETE")):
                df_all[df_all['name_en'] != target_name].to_sql('companies', engine, if_exists='replace', index=False); st.rerun()

# --- 5. Dashboard (V32 批量刪除邏輯) ---
elif choice == "📊 Dashboard":
    st.header("📊 Compliance Overview")
    df = pd.read_sql("SELECT * FROM companies", engine)
    if not df.empty:
        if 'select_all' not in st.session_state: st.session_state.select_all = False
        c1, c2, c3 = st.columns([2, 2, 8])
        if c1.button("✅ Select All"): st.session_state.select_all = True; st.rerun()
        if c2.button("🧹 Clear All"): st.session_state.select_all = False; st.rerun()
        df.insert(0, "Select", st.session_state.select_all)
        edited_df = st.data_editor(df, column_config={"Select": st.column_config.CheckboxColumn("Select", default=False)}, disabled=[c for c in df.columns if c != "Select"], hide_index=True, use_container_width=True)
        selected = edited_df[edited_df["Select"] == True]
        if len(selected) > 0:
            with st.popover("🧨 BATCH DELETE"):
                st.error(f"Delete {len(selected)} records?")
                user_conf = st.text_input("Type DELETE to confirm batch delete", key="batch_del")
                if st.button("🔥 DELETE SELECTED", disabled=(user_conf != "DELETE")):
                    to_del = selected["name_en"].tolist()
                    latest = pd.read_sql("SELECT * FROM companies", engine)
                    latest[~latest["name_en"].isin(to_del)].to_sql('companies', engine, if_exists='replace', index=False)
                    st.success("Purged!"); st.rerun()
    else: st.info("Empty database.")

# --- 6. Group Management ---
elif choice == "⚙️ Group Management":
    st.header("⚙️ Group Management")
    new_g = st.text_input("New Group")
    if st.button("Add"):
        pd.DataFrame([{'group_name': new_g}]).to_sql('client_groups', engine, if_exists='append', index=False); st.rerun()
