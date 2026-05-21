import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import io
from weasyprint import HTML

# --- 1. Database Connection (持續監控 handshake) ---
try:
    if "DB_URL" not in st.secrets:
        st.error("❌ `DB_URL` missing in Streamlit Secrets! Please configure it in Settings -> Secrets.")
        st.stop()
    
    DB_URL = st.secrets["DB_URL"]
    engine = create_engine(DB_URL)
    
    # 測試連線
    with engine.connect() as conn:
        pass
except Exception as db_err:
    st.error("### 🛑 Database Connection Critical Failure")
    st.markdown("Your code is correct, but python failed to handshake with your Database.")
    st.info(f"**Actual Underlying Error Details:**\n`{str(db_err)}`")
    st.markdown("""
    💡 **Supabase Tenant Not Found 專用修復指南：**
    
    1. **最快解決方案**：去 Supabase 攞 **Direct Connection** 嘅條字串，將 Port 由 `6543` 改返做 **`5432`**，User 改返做純 **`postgres`**。
    2. **Pooling 解決方案**：如果你一定要用 `6543`，請去 Supabase Database Settings 重新複製最新嘅 Connection String。Supabase 近期更新咗 Pooler 嘅 User 命名規則（後面通常要加多個字尾）。
    """)
    st.stop()

# --- 2. 工具函式：日期純化 (鎖定) ---
def to_date(val):
    try:
        if pd.isna(val) or val == "" or str(val).strip() == "" or str(val).lower() in ["none", "nat"]:
            return None
        return pd.to_datetime(val).date()
    except:
        return None

# --- 3. Navigation ---
st.set_page_config(page_title="ERP Cloud V121", layout="wide")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "⚙️ Group Management", "📤 Data Exchange"])

# --- 4. PDF 生成函式 (維持 V120 樣式邏輯) ---
def generate_custom_pdf(selected_df):
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    def fmt_date(val):
        d = to_date(val)
        return d.strftime('%Y/%m/%d') if d else "N/A"
    
    html_content = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap" rel="stylesheet">
        <style>
            @page {{ size: A4; margin: 15mm 10mm 25mm 10mm; }}
            body {{ font-family: 'Noto Sans TC', sans-serif; color: #2c3e50; line-height: 1.4; background-color: #ffffff; text-align: justify; }}
            #footer {{ position: fixed; bottom: -15mm; left: 0; right: 0; width: 100%; border-top: 1px solid #eee; padding-top: 5px; font-size: 9pt; color: #7f8c8d; }}
            .footer-table {{ width: 100%; border-collapse: collapse; }}
            .footer-left {{ text-align: left; width: 50%; }}
            .footer-right {{ text-align: right; width: 50%; }}
            .company-container {{ page-break-before: always; width: 100%; }}
            .company-container:first-child {{ page-break-before: auto; }}
            .main-table {{ width: 100%; border-collapse: collapse; }}
            .main-table thead {{ display: table-header-group; }}
            .header-content {{ text-align: center; border-bottom: 1px solid #eee; padding-bottom: 15px; margin-bottom: 20px; }}
            .name-en {{ font-size: 20pt; font-weight: bold; color: #2980b9; text-align: center; }}
            .name-ch {{ font-size: 15pt; color: #333333; margin-top: 5px; text-align: center; min-height: 20px; }}
            .section-bar {{ background-color: #f1f4f6; padding: 8px 15px; font-weight: bold; font-size: 11pt; margin: 20px 0 10px 0; border-left: 5px solid #3498db; color: #2c3e50; text-align: left; }}
            .section-group {{ page-break-inside: avoid; }}
            .info-table {{ width: 100%; border-collapse: collapse; }}
            .info-table tr {{ border-bottom: 1px solid #f1f2f6; }}
            .info-table th {{ text-align: left; width: 45%; color: #7f8c8d; padding: 8px 0; font-weight: normal; font-size: 10.5pt; }}
            .info-table td {{ text-align: justify; padding: 8px 0; color: #2c3e50; font-size: 10.5pt; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div id="footer"><table class="footer-table"><tr><td class="footer-left">Corporate Portfolio Report</td><td class="footer-right">Generated on: {now}</td></tr></table></div>
    """
    for _, row in selected_df.iterrows():
        html_content += f"""
        <div class="company-container">
            <table class="main-table">
                <thead><tr><td><div class="header-content"><div class="name-en">{row.get('name_en','')}</div><div class="name-ch">{row.get('name_ch','') if row.get('name_ch') else ''}</div></div></td></tr></thead>
                <tbody><tr><td><div class="company-card">
                    <div class="section-group"><div class="section-bar">Registration Details / 註冊詳情</div><table class="info-table">
                        <tr><th>Client Group / 客戶組別</th><td>{row.get('client_group','')}</td></tr>
                        <tr><th>Incorp. Date / 成立日期</th><td>{fmt_date(row.get('incorp_date'))}</td></tr>
                        <tr><th>Incorp. Place / 成立地點</th><td>{row.get('incorp_place','')}</td></tr>
                        <tr><th>CI No. / 公司註冊編號</th><td>{row.get('ci_no','')}</td></tr>
                        <tr><th>BR No. / 商業登記編號</th><td>{row.get('br_no','')}</td></tr>
                        <tr><th>Company Type / 公司類別</th><td>{row.get('co_type','')}</td></tr>
                    </table></div>
                    <div class="section-group"><div class="section-bar">Addresses / 地址</div><table class="info-table">
                        <tr><th>Registered Address / 註冊地址</th><td>{row.get('reg_addr','')}</td></tr>
                        <tr><th>Correspondence Address / 通訊地址</th><td>{row.get('corres_addr','')}</td></tr>
                    </table></div>
                    <div class="section-group"><div class="section-bar">Items Storage / 物品存放位置</div><table class="info-table">
                        <tr><th>Round Stamp / 小圓章</th><td>{row.get('round_loc','')}</td></tr>
                        <tr><th>Signature Chop / 簽名章</th><td>{row.get('sign_loc','')}</td></tr>
                        <tr><th>Common Seal / 鋼印</th><td>{row.get('seal_loc','')}</td></tr>
                    </table></div>
                    <div class="section-group"><div class="section-bar">Compliance Filings / 法定申報</div><table class="info-table">
                        <tr><th>ND2A Effective Date (YYYY/MM/DD)</th><td>{fmt_date(row.get('nd2a_eff_date'))}</td></tr>
                        <tr><th>ND4 Effective Date (YYYY/MM/DD)</th><td>{fmt_date(row.get('nd4_eff_date'))}</td></tr>
                    </table></div>
                </div></td></tr></tbody>
            </table>
        </div>"""
    html_content += "</body></html>"
    return HTML(string=html_content).write_pdf()

# --- 5. Dashboard ---
if choice == "📊 Dashboard":
    st.header("📊 Compliance Overview")
    df_raw = pd.read_sql("SELECT * FROM companies", engine)
    groups = pd.read_sql("SELECT group_name FROM client_groups", engine)['group_name'].tolist()
    
    if not df_raw.empty:
        for col in ["incorp_date", "nd2a_eff_date", "nd4_eff_date", "nd2a_file_date", "nd4_file_date", "dissolution_date"]:
            if col in df_raw.columns: df_raw[col] = pd.to_datetime(df_raw[col], errors='coerce').dt.date
        
        t1, t2, t3, t4 = st.columns([3, 2, 2, 5])
        filter_g = t1.selectbox("🔍 Filter Group", ["All Groups"] + groups)
        if t2.button("🔄 Refresh"): st.rerun()
        df_filtered = df_raw if filter_g == "All Groups" else df_raw[df_raw['client_group'] == filter_g]
        
        if 'sel_v121' not in st.session_state: st.session_state.sel_v121 = False
        if t3.button("✅ Select All"): st.session_state.sel_v121 = True; st.rerun()
        if t4.button("🧹 Clear All"): st.session_state.sel_v121 = False; st.rerun()
        
        df_display = df_filtered.copy()
        df_display.insert(0, "Select", st.session_state.sel_v121)
        
        total_count = len(df_filtered)
        st.markdown(f"📈 Total: **{total_count}** companies in current view.")

        edit_df = st.data_editor(df_display, column_config={"Select": st.column_config.CheckboxColumn("Select", default=False)}, hide_index=True, use_container_width=True, key="dash_v121")
        
        selected = edit_df[edit_df["Select"] == True]
        selected_count = len(selected)
        
        if selected_count > 0:
            st.info(f"✅ **{selected_count}** companies selected for action.")
            act1, act2 = st.columns([3, 7])
            with act1:
                if st.button("📥 Export Selected PDF"):
                    final_data = df_raw[df_raw['name_en'].isin(selected['name_en'])]
                    st.download_button(label="Download Now", data=generate_custom_pdf(final_data), file_name="Report.pdf", mime="application/pdf")
            with act2.popover("🧨 BATCH DELETE"):
                st.error("🛑 DANGER ZONE"); conf_b = st.text_input("Type DELETE", key="batch_del_v121")
                if st.button("Confirm Batch Delete", disabled=(conf_b != "DELETE"), key="btn_batch_del_v121"):
                    df_raw[~df_raw["name_en"].isin(selected["name_en"].tolist())].to_sql('companies', engine, if_exists='replace', index=False); st.rerun()
    else: st.info("No records.")

# --- 6. Company Register ---
elif choice == "🏢 Company Register":
    st.title("🏢 Company Records Management")
    mode = st.radio("Mode", ["🆕 Add New", "✏️ Edit Existing", "📋 Copy Existing"], horizontal=True)
    df_all = pd.read_sql("SELECT * FROM companies", engine)
    groups = pd.read_sql("SELECT group_name FROM client_groups", engine)['group_name'].tolist()
    MIN_DATE = datetime(1900, 1, 1)

    d = {'cg': "", 'en': "", 'ch': "", 'idate': None, 'place': "", 'p_oth': "", 'ci': "", 'br': "", 'type': "", 'ra': "", 'ca': "", 'rl': "", 'sl': "", 'cl': "", 'n2e': None, 'n2f': None, 'n2d': False, 'n4e': None, 'n4f': None, 'n4d': False, 'dis': None}
    target_name = None
    if mode in ["✏️ Edit Existing", "📋 Copy Existing"] and not df_all.empty:
        target_name = st.selectbox("Select Company", [""] + df_all['name_en'].tolist())
        if target_name != "":
            row = df_all[df_all['name_en'] == target_name].iloc[0]
            d = {'cg': row.get('client_group', ""), 'en': row.get('name_en', ""), 'ch': row.get('name_ch', ""), 'idate': row.get('incorp_date'), 'place': row.get('incorp_place', ""), 'p_oth': row.get('incorp_place_others', ""), 'ci': row.get('ci_no', ""), 'br': row.get('br_no', ""), 'type': row.get('co_type', ""), 'ra': row.get('reg_addr', ""), 'ca': row.get('corres_addr', ""), 'rl': row.get('round_loc', ""), 'sl': row.get('sign_loc', ""), 'cl': row.get('seal_loc', ""), 'n2e': row.get('nd2a_eff_date'), 'n2f': row.get('nd2a_file_date'), 'n2d': str(row.get('nd2a_download', "")) == 'True', 'n4e': row.get('nd4_eff_date'), 'n4f': row.get('nd4_file_date'), 'n4d': str(row.get('nd4_download', "")) == 'True', 'dis': row.get('dissolution_date')}
            if mode == "📋 Copy Existing": d['en'], d['ch'] = "", ""

    st.header("General Information")
    st.markdown("⚠️ Select Client Group :red[(Required!)]")
    client_group = st.selectbox("Group", [""] + groups, index=(groups.index(d['cg'])+1 if d['cg'] in groups else 0), label_visibility="collapsed")
    c1, c2 = st.columns(2)
    with c1: st.markdown("⚠️ Company English Name :red[(Required!)]"); name_en = st.text_input("EN", value=d['en'], label_visibility="collapsed")
    with c2: st.markdown("Company Chinese Name"); name_ch = st.text_input("CH", value=d['ch'], label_visibility="collapsed")
    c3, c4 = st.columns(2)
    with c3: st.markdown("⚠️ Date of Incorporation :red[(Required!)]"); inc_date = st.date_input("Date", value=to_date(d['idate']), min_value=MIN_DATE, label_visibility="collapsed")
    with c4: st.markdown("⚠️ Place of Incorporation :red[(Required!)]"); inc_place = st.selectbox("Place", ["", "HK", "BVI", "Others"], index=(["", "HK", "BVI", "Others"].index(d['place']) if d['place'] in ["", "HK", "BVI", "Others"] else 0), label_visibility="collapsed")
    if inc_place == "Others": st.markdown("⚠️ Specify Others :red[(Required!)]"); place_others = st.text_input("Others_Input", value=d['p_oth'], label_visibility="collapsed")
    else: place_others = ""
    st.write("---") 
    c5, c6 = st.columns(2)
    with c5: st.markdown("⚠️ CI Number :red[(Required!)]"); ci_no = st.text_input("CI", value=d['ci'], label_visibility="collapsed")
    with c6: st.markdown("⚠️ BR Number :red[(Required!)]"); br_no = st.text_input("BR", value=d['br'], label_visibility="collapsed")
    st.markdown("⚠️ Company Type :red[(Required!)]"); co_type = st.selectbox("Type", ["", "Private Company", "Public Company", "Guarantee"], index=(["", "Private Company", "Public Company", "Guarantee"].index(d['type']) if d['type'] in ["", "Private Company", "Public Company", "Guarantee"] else 0), label_visibility="collapsed")

    st.write("---"); st.header("📝 Compliance Filings")
    st.subheader("📑 Company Secretary Appointment (ND2A)")
    cc1, cc2, cc3, cc4 = st.columns([3, 3, 3, 1])
    with cc1: n2e = st.date_input("Effective Date (Appt)", value=to_date(d['n2e']), min_value=MIN_DATE, key="n2e_v121")
    with cc2: n2f = st.date_input("Filing Date (ND2A)", value=to_date(d['n2f']), min_value=MIN_DATE, key="n2f_v121")
    with cc3:
        st.info("Statutory Period: 15 days")
        if n2e: n2_deadline = (n2e + timedelta(days=15)); st.markdown(f"**Deadline: :red[{n2_deadline}]**") 
    with cc4: n2d = st.checkbox("Downloaded", value=d['n2d'], key="n2d_v121")
    st.subheader("📑 Company Secretary Resignation (ND4)")
    cc5, cc6, cc7, cc8 = st.columns([3, 3, 3, 1])
    with cc5: n4e = st.date_input("Effective Date (Resign)", value=to_date(d['n4e']), min_value=MIN_DATE, key="n4e_v121")
    with cc6: n4f = st.date_input("Filing Date (ND4)", value=to_date(d['n4f']), min_value=MIN_DATE, key="n4f_v121")
    with cc7:
        st.info("Statutory Period: 15 days")
        if n4e: n4_deadline = (n4e + timedelta(days=15)); st.markdown(f"**Deadline: :red[{n4_deadline}]**") 
    with cc8: n4d = st.checkbox("Downloaded", value=d['n4d'], key="n4d_v121")

    st.write("---"); st.subheader("📍 Address & Contact")
    ca1, ca2 = st.columns(2)
    with ca1: st.markdown("⚠️ Registered Office Address :red[(Required!)]"); reg_addr = st.text_area("Reg", value=d['ra'], label_visibility="collapsed")
    with ca2: st.markdown("⚠️ Correspondence Address :red[(Required!)]"); corres_addr = st.text_area("Corres", value=d['ca'], label_visibility="collapsed")
    st.subheader("📔 Seal Storage")
    l1, l2, l3 = st.columns(3)
    with l1: st.markdown("⚠️ Round Chop Location :red[(Required!)]"); round_l = st.text_input("Round", value=d['rl'], label_visibility="collapsed")
    with l2: st.markdown("⚠️ Signature Chop Location :red[(Required!)]"); sign_l = st.text_input("Sign", value=d['sl'], label_visibility="collapsed")
    with l3: st.markdown("⚠️ Common Seal Location :red[(Required!)]"); common_l = st.text_input("Seal", value=d['cl'], label_visibility="collapsed")
    st.write("---"); st.markdown("Company Dissolution Date"); dis_date = st.date_input("Dissolution", value=to_date(d['dis']), min_value=MIN_DATE, label_visibility="collapsed")
    
    row_v121 = {'client_group': client_group, 'name_en': name_en, 'name_ch': name_ch, 'incorp_date': inc_date, 'incorp_place': inc_place, 'incorp_place_others': place_others, 'ci_no': ci_no, 'br_no': br_no, 'co_type': co_type, 'reg_addr': reg_addr, 'corres_addr': corres_addr, 'round_loc': round_l, 'sign_loc': sign_l, 'seal_loc': common_l, 'nd2a_eff_date': n2e, 'nd2a_file_date': n2f, 'nd2a_download': n2d, 'nd4_eff_date': n4e, 'nd4_file_date': n4f, 'nd4_download': n4d, 'dissolution_date': dis_date}
    mandatory_fields = {"Client Group": client_group, "English Name": name_en, "CI Number": ci_no, "BR Number": br_no, "Company Type": co_type, "Registered Address": reg_addr, "Correspondence Address": corres_addr, "Round Chop Location": round_l, "Signature Chop Location": sign_l, "Common Seal Location": common_l}
    if inc_place == "Others": mandatory_fields["Specify Others"] = place_others
    missing = [k for k, v in mandatory_fields.items() if not v or str(v).strip() == ""]

    if mode in ["🆕 Add New", "📋 Copy Existing"]:
        if st.button("💾 Save To Cloud", key="btn_save_v121"):
            if missing: st.error(f"❌ Missing: {', '.join(missing)}")
            else: pd.DataFrame([row_v121]).to_sql('companies', engine, if_exists='append', index=False); st.success("✅ Success!"); st.rerun()
    else:
        u_col, d_col = st.columns(2)
        with u_col.popover("🆙 Update"):
            if st.button("Confirm Update", key="btn_update_v121"):
                if missing: st.error(f"❌ Missing: {', '.join(missing)}")
                else:
                    df_all[df_all['name_en'] != target_name].to_sql('companies', engine, if_exists='replace', index=False)
                    pd.DataFrame([row_v121]).to_sql('companies', engine, if_exists='append', index=False); st.success("✅ Updated!"); st.rerun()
        with d_col.popover("🚨 DELETE"):
            st.error(f"Delete {target_name}?"); conf_s = st.text_input("Type DELETE", key="single_del_v121")
            if st.button("Confirm Delete Company", disabled=(conf_s != "DELETE"), key="btn_del_single_v121"):
                df_all[df_all['name_en'] != target_name].to_sql('companies', engine, if_exists='replace', index=False); st.rerun()

# --- 7. Group Management ---
elif choice == "⚙️ Group Management":
    st.header("⚙️ Group Management")
    new_g = st.text_input("New Group Name", key="new_group_input_v121")
    if st.button("Add Group", key="btn_add_group_v121"): pd.DataFrame([{'group_name': new_g}]).to_sql('client_groups', engine, if_exists='append', index=False); st.rerun()
    st.write("---")
    g_df = pd.read_sql("SELECT * FROM client_groups", engine)
    if not g_df.empty:
        target = st.selectbox("Select Group", g_df['group_name'].tolist(), key="select_group_manage_v121")
        c1, c2 = st.columns(2)
        with c1.popover("✏️ Rename Group"):
            ren = st.text_input("New Name:", key="rename_input_v121")
            conf_r = st.text_input("Type RENAME", key="rename_confirm_text_v121")
            if st.button("Confirm Rename", disabled=(conf_r != "RENAME"), key="btn_group_rename_v121"):
                comp_df = pd.read_sql("SELECT * FROM companies", engine)
                comp_df.loc[comp_df['client_group'] == target, 'client_group'] = ren
                comp_df.to_sql('companies', engine, if_exists='replace', index=False)
                g_df.replace({target: ren}).to_sql('client_groups', engine, if_exists='replace', index=False); st.rerun()
        with c2.popover("🗑️ Delete Group"):
            if st.button("Confirm Delete Group", key="btn_group_delete_v121"): 
                g_df[g_df['group_name'] != target].to_sql('client_groups', engine, if_exists='replace', index=False); st.rerun()

# --- 8. Data Exchange ---
elif choice == "📤 Data Exchange":
    st.header("📤 Data Exchange")
    c1, c2 = st.columns(2)
    template_cols = ["client_group", "name_en", "name_ch", "incorp_date", "incorp_place", "incorp_place_others", "ci_no", "br_no", "co_type", "reg_addr", "corres_addr", "round_loc", "sign_loc", "seal_loc", "nd2a_eff_date", "nd2a_file_date", "nd2a_download", "nd4_eff_date", "nd4_file_date", "nd4_download", "dissolution_date"]
    buf_t = io.BytesIO(); pd.DataFrame(columns=template_cols).to_excel(buf_t, index=False); c1.download_button(label="📥 Template", data=buf_t.getvalue(), file_name="Template.xlsx")
    
    df_db = pd.read_sql("SELECT * FROM companies", engine); df_export = df_db.copy()
    for col in ["incorp_date", "nd2a_eff_date", "nd2a_file_date", "nd4_eff_date", "nd4_file_date", "dissolution_date"]:
        if col in df_export.columns: df_export[col] = pd.to_datetime(df_export[col], errors='coerce').dt.strftime('%Y-%m-%d')
    buf_e = io.BytesIO(); df_export.to_excel(buf_e, index=False)
    c2.download_button(label="📦 Export All", data=buf_e.getvalue(), file_name="Backup.xlsx", key="btn_export_all_v121")
    st.write("---")
    
    up = st.file_uploader("Upload XLSX to Review Changes", type=["xlsx"], key="file_uploader_v121")
    if up:
        try:
            up_df = pd.read_excel(up, engine='openpyxl', keep_default_na=False)
            existing_df = pd.read_sql("SELECT * FROM companies", engine)
            up_df['br_no'] = up_df['br_no'].astype(str).str.strip()
            existing_df['br_no'] = existing_df['br_no'].astype(str).str.strip()
            
            for col in ["incorp_date", "nd2a_eff_date", "nd2a_file_date", "nd4_eff_date", "nd4_file_date", "dissolution_date"]:
                if col in up_df.columns: up_df[col] = pd.to_datetime(up_df[col], errors='coerce').dt.date
                if col in existing_df.columns: existing_df[col] = pd.to_datetime(existing_df[col], errors='coerce').dt.date
            
            diff_list = []
            cols_to_compare = ["client_group", "name_en", "name_ch", "incorp_date", "ci_no", "br_no", "co_type", "reg_addr", "corres_addr", "round_loc", "sign_loc", "seal_loc"]
            
            for _, row_new in up_df.iterrows():
                br_num = row_new['br_no']
                en_name = row_new.get('name_en', 'Unknown')
                old_row = existing_df[existing_df['br_no'] == br_num]
                if not old_row.empty:
                    old_row = old_row.iloc[0]
                    for col in cols_to_compare:
                        old_val = str(old_row.get(col, "")).strip()
                        new_val = str(row_new.get(col, "")).strip()
                        if old_val != new_val:
                            diff_list.append({"Company": en_name, "BR Number": br_num, "Field": col, "Old Value": old_val, "New Value": new_val})
                else:
                    diff_list.append({"Company": en_name, "BR Number": br_num, "Field": "NEW RECORD", "Old Value": "N/A", "New Value": "Will be added"})

            if diff_list:
                st.subheader("🔍 Review Changes (Based on BR Number)")
                st.table(pd.DataFrame(diff_list))
                if st.button("🚀 Confirm & Apply Changes", key="btn_final_sync_v121"):
                    combined_df = pd.concat([existing_df, up_df]).drop_duplicates(subset=['br_no'], keep='last')
                    combined_df.to_sql('companies', engine, if_exists='replace', index=False)
                    st.success("✅ Sync Completed!"); st.balloons(); st.rerun()
            else: st.info("No differences found.")
        except Exception as e: st.error(f"Error: {e}")
