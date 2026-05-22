import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta, date
import io
from weasyprint import HTML

# --- 1. Database Connection ---
try:
    if "DB_URL" not in st.secrets:
        st.error("❌ 系統錯誤：找不到資料庫連接 (DB_URL missing in Streamlit Secrets!)")
        st.stop()
    
    DB_URL = st.secrets["DB_URL"]
    engine = create_engine(DB_URL)
    
    with engine.connect() as conn:
        pass
except Exception as db_err:
    st.error("### 🛑 資料庫連接失敗 (Database Connection Critical Failure)")
    st.info(f"**錯誤詳情 (Error Details):**\n`{str(db_err)}`")
    st.stop()

# --- 2. 實用工具函式 ---
def to_date(val):
    try:
        if pd.isna(val) or val == "" or str(val).strip() == "" or str(val).lower() in ["none", "nat", "nan"]:
            return None
        return pd.to_datetime(val).date()
    except:
        return None

def clean_val(v):
    v = str(v).strip()
    if v.lower() in ["nat", "none", "nan", ""]: return ""
    if v.endswith(" 00:00:00"): return v.replace(" 00:00:00", "")
    return v

def get_anniv(year, month, day):
    try: return date(year, month, day)
    except ValueError: return date(year, month, day - 1)

# --- 3. 系統導航 (Navigation) ---
st.set_page_config(page_title="ERP Cloud V140", layout="wide")
choice = st.sidebar.radio("目錄導航 (Navigation)", ["📊 總覽儀表板 (Dashboard)", "🏢 公司名冊管理 (Company Register)", "⚙️ 客戶組別管理 (Group Management)", "📤 數據匯出與匯入 (Data Exchange)"])

TEMPLATE_COLS = [
    "client_group", "name_en", "name_ch", "incorp_place", "incorp_place_others", 
    "incorp_date", "ci_no", "is_hk_registered", "hk_incorp_date", "hk_ci_no", "br_no", 
    "co_type", "reg_addr", "corres_addr", "round_loc", "sign_loc", "seal_loc", 
    "nd2a_eff_date", "nd2a_file_date", "nd2a_download", "nd4_eff_date", "nd4_file_date", "nd4_download", 
    "br_paid_by", "last_br_resolved_date", "last_ar_filed_date", "dissolution_date"
]

# --- 4. 報告生成模組 (Report Generation) ---
def generate_custom_pdf(selected_df):
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    def fmt_date(val):
        d = to_date(val)
        return d.strftime('%Y/%m/%d') if d else "N/A"
    
    if not selected_df.empty:
        sort_cols = [c for c in ['client_group', 'name_en', 'incorp_place'] if c in selected_df.columns]
        selected_df = selected_df.sort_values(by=sort_cols, na_position='last')

    html_header = """
    <html>
    <head>
        <meta charset="UTF-8">
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap" rel="stylesheet">
        <style>
            @page { size: A4; margin: 15mm 10mm 25mm 10mm; }
            body { font-family: 'Noto Sans TC', sans-serif; color: #2c3e50; line-height: 1.4; background-color: #ffffff; text-align: justify; }
            #footer { position: fixed; bottom: -15mm; left: 0; right: 0; width: 100%; border-top: 1px solid #eee; padding-top: 5px; font-size: 9pt; color: #7f8c8d; }
            .footer-table { width: 100%; border-collapse: collapse; }
            .footer-left { text-align: left; width: 50%; }
            .footer-right { text-align: right; width: 50%; }
            .company-container { page-break-before: always; width: 100%; }
            .company-container:first-child { page-break-before: auto; }
            .main-table { width: 100%; border-collapse: collapse; }
            .main-table thead { display: table-header-group; }
            .header-content { text-align: center; border-bottom: 1px solid #eee; padding-bottom: 15px; margin-bottom: 20px; }
            .name-en { font-size: 20pt; font-weight: bold; color: #2980b9; text-align: center; }
            .name-ch { font-size: 15pt; color: #333333; margin-top: 5px; text-align: center; min-height: 20px; }
            .section-bar { background-color: #f1f4f6; padding: 8px 15px; font-weight: bold; font-size: 11pt; margin: 20px 0 10px 0; border-left: 5px solid #3498db; color: #2c3e50; text-align: left; }
            .section-group { page-break-inside: avoid; }
            .info-table { width: 100%; border-collapse: collapse; }
            .info-table tr { border-bottom: 1px solid #f1f2f6; }
            .info-table th { text-align: left; width: 45%; color: #7f8c8d; padding: 8px 0; font-weight: normal; font-size: 10.5pt; }
            .info-table td { text-align: justify; padding: 8px 0; color: #2c3e50; font-size: 10.5pt; font-weight: bold; }
        </style>
    </head>
    <body>
        <div id="footer">
            <table class="footer-table">
                <tr>
                    <td class="footer-left">Corporate Portfolio Report</td>
                    <td class="footer-right">生成時間 (Generated on): """ + now + """</td>
                </tr>
            </table>
        </div>
    """

    card_template = """
    <div class="company-container">
        <table class="main-table">
            <thead>
                <tr><td><div class="header-content"><div class="name-en">__NAME_EN__</div><div class="name-ch">__NAME_CH__</div></div></td></tr>
            </thead>
            <tbody>
                <tr>
                    <td>
                        <div class="company-card">
                            <div class="section-group">
                                <div class="section-bar">註冊詳情 (Registration Details)</div>
                                <table class="info-table">
                                    <tr><th>客戶組別 (Client Group)</th><td>__CLIENT_GROUP__</td></tr>
                                    <tr><th>成立地點 (Incorp. Place)</th><td>__INCORP_PLACE__</td></tr>
                                    __DYNAMIC_PLACE_ROWS__
                                    __DYNAMIC_HK_ROWS__
                                    <tr><th>公司類別 (Company Type)</th><td>__CO_TYPE__</td></tr>
                                </table>
                            </div>
                            <div class="section-group">
                                <div class="section-bar">地址 (Addresses)</div>
                                <table class="info-table">
                                    <tr><th>註冊地址 (Registered Address)</th><td>__REG_ADDR__</td></tr>
                                    <tr><th>通訊地址 (Correspondence Address)</th><td>__CORRES_ADDR__</td></tr>
                                </table>
                            </div>
                            <div class="section-group">
                                <div class="section-bar">物品存放位置 (Items Storage)</div>
                                <table class="info-table">
                                    <tr><th>小圓章 (Round Stamp)</th><td>__ROUND_LOC__</td></tr>
                                    <tr><th>簽名章 (Signature Chop)</th><td>__SIGN_LOC__</td></tr>
                                    <tr><th>鋼印 (Common Seal)</th><td>__SEAL_LOC__</td></tr>
                                </table>
                            </div>
                            <div class="section-group">
                                <div class="section-bar">法定申報紀錄 (Compliance Filings)</div>
                                <table class="info-table">
                                    __DYNAMIC_ANNUAL_ROWS__
                                    <tr><th>ND2A 委任日期 (Eff. Date)</th><td>__ND2A_EFF__</td></tr>
                                    <tr><th>ND4 辭任日期 (Eff. Date)</th><td>__ND4_EFF__</td></tr>
                                </table>
                            </div>
                        </div>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
    """

    final_html = html_header
    for _, row in selected_df.iterrows():
        ch_name = row.get('name_ch', '')
        if not ch_name or pd.isna(ch_name): ch_name = ''
        
        place = str(row.get('incorp_place', ''))
        is_hk_reg = str(row.get('is_hk_registered', 'False')) == 'True'
        
        dynamic_place_rows = ""
        display_place = place
        if place == 'Others':
            display_place = f"Others ({str(row.get('incorp_place_others', ''))})"
            
        dynamic_place_rows += f"<tr><th>{place} 成立日期 (Incorp. Date)</th><td>{fmt_date(row.get('incorp_date'))}</td></tr>"
        dynamic_place_rows += f"<tr><th>{place} 公司編號 (CI No.)</th><td>{str(row.get('ci_no', ''))}</td></tr>"

        dynamic_hk_rows = ""
        dynamic_annual_rows = ""
        
        br_paid_by_label = "本所處理 (Firm)" if str(row.get('br_paid_by', 'Firm')) == 'Firm' else "客戶自行處理 (Client)"
        
        if place == 'HK':
            dynamic_hk_rows += f"<tr><th>商業登記編號 (HK BR No.)</th><td>{str(row.get('br_no', ''))}</td></tr>"
            dynamic_annual_rows += f"<tr><th>BR 負責方 (BR Paid By)</th><td>{br_paid_by_label}</td></tr>"
            dynamic_annual_rows += f"<tr><th>BR 最近處理日期 (Last BR Resolved)</th><td>{fmt_date(row.get('last_br_resolved_date'))}</td></tr>"
            dynamic_annual_rows += f"<tr><th>AR 最近提交日期 (Last AR Filed)</th><td>{fmt_date(row.get('last_ar_filed_date'))}</td></tr>"
        elif is_hk_reg:
            dynamic_hk_rows += f"<tr><th>香港註冊日期 (HK Incorp. Date)</th><td>{fmt_date(row.get('hk_incorp_date'))}</td></tr>"
            dynamic_hk_rows += f"<tr><th>香港公司編號 (HK CI No.)</th><td>{str(row.get('hk_ci_no', ''))}</td></tr>"
            dynamic_hk_rows += f"<tr><th>商業登記編號 (HK BR No.)</th><td>{str(row.get('br_no', ''))}</td></tr>"
            dynamic_annual_rows += f"<tr><th>BR 負責方 (BR Paid By)</th><td>{br_paid_by_label}</td></tr>"
            dynamic_annual_rows += f"<tr><th>BR 最近處理日期 (Last BR Resolved)</th><td>{fmt_date(row.get('last_br_resolved_date'))}</td></tr>"
            dynamic_annual_rows += f"<tr><th>AR 最近提交日期 (Last AR Filed)</th><td>{fmt_date(row.get('last_ar_filed_date'))}</td></tr>"
        
        card = card_template
        card = card.replace("__NAME_EN__", str(row.get('name_en', '')))
        card = card.replace("__NAME_CH__", str(ch_name))
        card = card.replace("__CLIENT_GROUP__", str(row.get('client_group', '')))
        card = card.replace("__INCORP_PLACE__", display_place)
        card = card.replace("__DYNAMIC_PLACE_ROWS__", dynamic_place_rows)
        card = card.replace("__DYNAMIC_HK_ROWS__", dynamic_hk_rows)
        card = card.replace("__CO_TYPE__", str(row.get('co_type', '')))
        card = card.replace("__REG_ADDR__", str(row.get('reg_addr', '')))
        card = card.replace("__CORRES_ADDR__", str(row.get('corres_addr', '')))
        card = card.replace("__ROUND_LOC__", str(row.get('round_loc', '')))
        card = card.replace("__SIGN_LOC__", str(row.get('sign_loc', '')))
        card = card.replace("__SEAL_LOC__", str(row.get('seal_loc', '')))
        card = card.replace("__DYNAMIC_ANNUAL_ROWS__", dynamic_annual_rows)
        card = card.replace("__ND2A_EFF__", fmt_date(row.get('nd2a_eff_date')))
        card = card.replace("__ND4_EFF__", fmt_date(row.get('nd4_eff_date')))
        final_html += card

    final_html += "</body></html>"
    return HTML(string=final_html).write_pdf()

def generate_outstanding_pdf(df_alerts):
    now_str = datetime.now().strftime("%Y/%m/%d %H:%M")
    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap" rel="stylesheet">
        <style>
            @page {{ size: A4 landscape; margin: 15mm; background-color: #ffffff; }}
            body {{ font-family: 'Noto Sans TC', sans-serif; font-size: 10pt; color: #2c3e50; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th {{ background-color: #1f497d; color: white; padding: 8px; border: 1px solid #d9d9d9; font-size: 10.5pt; text-align: center; }}
            td {{ padding: 8px; border: 1px solid #d9d9d9; text-align: center; vertical-align: middle; }}
            tr:nth-child(even) {{ background-color: #f8f9fa; }}
            .text-left {{ text-align: left; font-weight: bold; color: #2980b9; }}
        </style>
    </head>
    <body>
        <h2 style="color: #1f497d; margin-bottom: 5px;">待辦常規申報清單 (Outstanding Compliance Report)</h2>
        <p style="color: #7f8c8d; font-size: 9pt; margin-top: 0;">報告生成時間: {now_str}</p>
        <table>
            <thead>
                <tr>
                    <th style="width:10%">客戶組別</th><th style="width:25%">公司英文名稱</th><th style="width:12%">成立地點</th>
                    <th style="width:10%">BR負責方</th><th style="width:10%">BR狀態</th><th style="width:11%">BR截止日</th>
                    <th style="width:11%">AR狀態</th><th style="width:11%">AR截止日</th>
                </tr>
            </thead>
            <tbody>
    """
    for _, r in df_alerts.iterrows():
        br_color = "#c00000" if "逾期" in str(r.get('BR 狀態', '')) else "#2c3e50"
        ar_color = "#c00000" if "逾期" in str(r.get('AR 狀態', '')) else ("#9c6500" if "即將" in str(r.get('AR 狀態', '')) else "#2c3e50")
        
        html += f"""
        <tr>
            <td>{r.get('客戶組別', '')}</td>
            <td class="text-left">{r.get('公司名稱', '')}</td>
            <td>{r.get('成立地點', '')}</td>
            <td>{r.get('BR負責方', '')}</td>
            <td style="color: {br_color}; font-weight: bold;">{r.get('BR 狀態', '')}</td>
            <td>{r.get('BR 截止日', '')}</td>
            <td style="color: {ar_color}; font-weight: bold;">{r.get('AR 狀態', '')}</td>
            <td>{r.get('AR 截止日', '')}</td>
        </tr>
        """
    html += "</tbody></table></body></html>"
    return HTML(string=html).write_pdf()

# --- 5. 總覽儀表板 (Dashboard) ---
if choice == "📊 總覽儀表板 (Dashboard)":
    st.header("📊 總覽與待辦事項 (Dashboard & Outstanding Tasks)")
    df_raw = pd.read_sql("SELECT * FROM companies", engine)
    groups = pd.read_sql("SELECT group_name FROM client_groups", engine)['group_name'].tolist()
    
    if not df_raw.empty:
        for col in ["incorp_date", "hk_incorp_date", "nd2a_eff_date", "nd4_eff_date", "nd2a_file_date", "nd4_file_date", "last_br_resolved_date", "last_ar_filed_date", "dissolution_date"]:
            if col in df_raw.columns: df_raw[col] = pd.to_datetime(df_raw[col], errors='coerce').dt.date
            
        today = datetime.now().date()
        current_year = today.year
        
        # 計算待辦清單邏輯
        outstanding_records = []
        for _, row in df_raw.iterrows():
            name = row.get('name_en', 'Unknown')
            group = row.get('client_group', '')
            place = str(row.get('incorp_place', ''))
            is_hk_reg = str(row.get('is_hk_registered', 'False')) == 'True'
            br_by = str(row.get('br_paid_by', 'Firm'))
            
            base_date = None
            if place == 'HK': base_date = to_date(row.get('incorp_date'))
            elif is_hk_reg: base_date = to_date(row.get('hk_incorp_date'))
                
            if not base_date: continue
            
            last_br = to_date(row.get('last_br_resolved_date'))
            last_ar = to_date(row.get('last_ar_filed_date'))
            
            br_dl = get_anniv(current_year, base_date.month, base_date.day)
            ar_dl = br_dl + timedelta(days=42)
            
            br_status, ar_status = "正常 (Normal)", "正常 (Normal)"
            br_dl_str = br_dl.strftime('%Y/%m/%d')
            ar_dl_str = ar_dl.strftime('%Y/%m/%d')
            is_alert = False
            
            if br_by == 'Client':
                br_status = "由客戶處理 (Client)"
                br_dl_str = "N/A"
            else:
                if not last_br or last_br.year < current_year:
                    days_diff = (br_dl - today).days
                    if days_diff < 0: br_status, is_alert = "逾期 (Overdue)", True
                    elif 0 <= days_diff <= 30: br_status, is_alert = "即將到期 (Due Soon)", True
            
            if not last_ar or last_ar.year < current_year:
                days_diff = (ar_dl - today).days
                if days_diff < 0: ar_status, is_alert = "逾期 (Overdue)", True
                elif 0 <= days_diff <= 30: ar_status, is_alert = "即將到期 (Due Soon)", True
                    
            if is_alert:
                outstanding_records.append({
                    "客戶組別": group,
                    "公司名稱": name,
                    "成立地點": place,
                    "BR負責方": br_by,
                    "BR 狀態": br_status,
                    "BR 截止日": br_dl_str,
                    "AR 狀態": ar_status,
                    "AR 截止日": ar_dl_str
                })

        # 雙分頁設計：總覽 vs 待辦
        tab1, tab2 = st.tabs(["📊 所有公司總覽 (All Companies)", "🚨 待辦合規清單 (Outstanding List)"])
        
        with tab1:
            sort_cols = [c for c in ['client_group', 'name_en', 'incorp_place'] if c in df_raw.columns]
            df_raw = df_raw.sort_values(by=sort_cols, na_position='last')
            
            sorted_groups = sorted([g for g in groups if isinstance(g, str)])
            t1, t2, t3, t4 = st.columns([3, 2, 2, 5])
            filter_g = t1.selectbox("🔍 篩選客戶組別 (Filter Group)", ["All Groups"] + sorted_groups)
            if t2.button("🔄 刷新 (Refresh)"): st.rerun()
            df_filtered = df_raw if filter_g == "All Groups" else df_raw[df_raw['client_group'] == filter_g]
            
            if 'sel_v140' not in st.session_state: st.session_state.sel_v140 = False
            if t3.button("✅ 全選 (Select All)"): st.session_state.sel_v140 = True; st.rerun()
            if t4.button("🧹 清除全選 (Clear All)"): st.session_state.sel_v140 = False; st.rerun()
            
            existing_cols = [c for c in TEMPLATE_COLS if c in df_filtered.columns]
            df_display = df_filtered[existing_cols].copy()
            df_display.insert(0, "Select", st.session_state.sel_v140)
            
            st.markdown(f"📈 顯示中公司數量 (Total View): **{len(df_filtered)}**")

            st.info("💡 **批量修改編輯器 (Batch Editor):** 您可以直接雙擊以下表格修改「BR負責方」及「最新處理日期」。完成後請點擊下方「儲存修改」按鈕。")
            
            disabled_cols = [c for c in df_display.columns if c not in ["Select", "br_paid_by", "last_br_resolved_date", "last_ar_filed_date"]]
            edit_df = st.data_editor(
                df_display, 
                column_config={
                    "Select": st.column_config.CheckboxColumn("選取 (Select)", default=False),
                    "br_paid_by": st.column_config.SelectboxColumn("BR 負責方", options=["Firm", "Client"], required=True),
                    "last_br_resolved_date": st.column_config.DateColumn("BR 最新處理日期"),
                    "last_ar_filed_date": st.column_config.DateColumn("AR 最新提交日期")
                }, 
                disabled=disabled_cols,
                hide_index=True, 
                use_container_width=True, 
                key="dash_v140"
            )
            
            if st.button("💾 儲存表格修改 (Save Batch Edits)", key="btn_save_grid_v140"):
                try:
                    with engine.begin() as conn:
                        for _, r in edit_df.iterrows():
                            name_en_val = r['name_en']
                            br_by = r.get('br_paid_by', 'Firm')
                            br_dt = r.get('last_br_resolved_date')
                            ar_dt = r.get('last_ar_filed_date')
                            
                            br_dt_str = "NULL" if br_by == 'Client' else (f"'{br_dt}'" if pd.notna(br_dt) and br_dt else "NULL")
                            ar_dt_str = f"'{ar_dt}'" if pd.notna(ar_dt) and ar_dt else "NULL"
                            
                            sql = f"""UPDATE companies SET br_paid_by = '{br_by}', last_br_resolved_date = {br_dt_str}, last_ar_filed_date = {ar_dt_str} WHERE name_en = '{name_en_val}'"""
                            conn.execute(sql)
                    st.success("✅ 修改已成功儲存 (Changes saved successfully!)")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 批量儲存失敗 (Batch save failed): {e}")
            
            selected = edit_df[edit_df["Select"] == True]
            if len(selected) > 0:
                st.info(f"✅ 已選取 **{len(selected)}** 間公司進行操作。")
                act1, act2 = st.columns([3, 7])
                with act1:
                    if st.button("📥 匯出選定公司之 PDF 檔案"):
                        final_data = df_raw[df_raw['name_en'].isin(selected['name_en'])]
                        st.download_button(label="立即下載報告 (Download Report)", data=generate_custom_pdf(final_data), file_name="Company_Report.pdf", mime="application/pdf")
                with act2.popover("🧨 批量刪除 (BATCH DELETE)"):
                    st.error("🛑 危險操作區域 (DANGER ZONE)"); conf_b = st.text_input("輸入 DELETE 以確認", key="batch_del_v140")
                    if st.button("確認批量刪除 (Confirm)", disabled=(conf_b != "DELETE"), key="btn_batch_del_v140"):
                        df_raw[~df_raw["name_en"].isin(selected["name_en"].tolist())].to_sql('companies', engine, if_exists='replace', index=False); st.rerun()

        with tab2:
            st.subheader("🚨 待辦常規申報清單 (Outstanding Compliance Tasks)")
            df_alerts = pd.DataFrame(outstanding_records)
            if not df_alerts.empty:
                st.dataframe(df_alerts, use_container_width=True, hide_index=True)
                c_ex1, c_ex2 = st.columns(2)
                
                # Excel 匯出
                buf_excel = io.BytesIO()
                df_alerts.to_excel(buf_excel, index=False, sheet_name="待辦清單")
                c_ex1.download_button("📥 匯出待辦 Excel (Export Excel)", data=buf_excel.getvalue(), file_name="Outstanding_Compliance.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                
                # PDF 匯出
                c_ex2.download_button("📥 匯出待辦 PDF (Export PDF)", data=generate_outstanding_pdf(df_alerts), file_name="Outstanding_Compliance.pdf", mime="application/pdf")
            else:
                st.success("🎉 目前沒有任何已逾期或即將到期之常規申報。 (No outstanding tasks at the moment!)")
    else: st.info("目前沒有紀錄 (No records found).")

# --- 6. 公司名冊管理 (Company Register) ---
elif choice == "🏢 公司名冊管理 (Company Register)":
    st.title("🏢 公司名冊管理 (Company Records Management)")
    mode = st.radio("操作模式 (Mode)", ["🆕 新增公司 (Add New)", "✏️ 編輯現有 (Edit Existing)", "📋 複製現有 (Copy Existing)"], horizontal=True)
    df_all = pd.read_sql("SELECT * FROM companies", engine)
    groups = pd.read_sql("SELECT group_name FROM client_groups", engine)['group_name'].tolist()
    sorted_groups = sorted([g for g in groups if isinstance(g, str)])
    MIN_DATE = datetime(1900, 1, 1)

    d = {'cg': "", 'en': "", 'ch': "", 'place': "", 'p_oth': "", 'idate': None, 'ci': "", 'is_hk_reg': False, 'hk_idate': None, 'hk_ci': "", 'br': "", 'br_paid_by': "Firm", 'type': "", 'ra': "", 'ca': "", 'rl': "", 'sl': "", 'cl': "", 'n2e': None, 'n2f': None, 'n2d': False, 'n4e': None, 'n4f': None, 'n4d': False, 'l_br': None, 'l_ar': None, 'dis': None}
    target_name = None
    if mode in ["✏️ 編輯現有 (Edit Existing)", "📋 複製現有 (Copy Existing)"] and not df_all.empty:
        df_all = df_all.sort_values(by=['name_en', 'incorp_place'], na_position='last')
        sorted_companies = df_all['name_en'].tolist()
        
        target_name = st.selectbox("選擇公司 (Select Company)", [""] + sorted_companies)
        if target_name != "":
            row = df_all[df_all['name_en'] == target_name].iloc[0]
            d = {'cg': row.get('client_group', ""), 'en': row.get('name_en', ""), 'ch': row.get('name_ch', ""), 'place': row.get('incorp_place', ""), 'p_oth': row.get('incorp_place_others', ""), 'idate': row.get('incorp_date'), 'ci': row.get('ci_no', ""), 'is_hk_reg': str(row.get('is_hk_registered', "")) == 'True', 'hk_idate': row.get('hk_incorp_date'), 'hk_ci': row.get('hk_ci_no', ""), 'br': row.get('br_no', ""), 'br_paid_by': row.get('br_paid_by', "Firm"), 'type': row.get('co_type', ""), 'ra': row.get('reg_addr', ""), 'ca': row.get('corres_addr', ""), 'rl': row.get('round_loc', ""), 'sl': row.get('sign_loc', ""), 'cl': row.get('seal_loc', ""), 'n2e': row.get('nd2a_eff_date'), 'n2f': row.get('nd2a_file_date'), 'n2d': str(row.get('nd2a_download', "")) == 'True', 'n4e': row.get('nd4_eff_date'), 'n4f': row.get('nd4_file_date'), 'n4d': str(row.get('nd4_download', "")) == 'True', 'l_br': row.get('last_br_resolved_date'), 'l_ar': row.get('last_ar_filed_date'), 'dis': row.get('dissolution_date')}
            if mode == "📋 複製現有 (Copy Existing)": d['en'], d['ch'] = "", ""

    st.header("📖 基本資料 (General Information)")
    c1, c2 = st.columns(2)
    with c1: st.markdown("⚠️ 公司英文名稱 (Company Name EN) :red[(必填)]"); name_en = st.text_input("EN", value=d['en'], label_visibility="collapsed")
    with c2: st.markdown("公司中文名稱 (Company Name CH)"); name_ch = st.text_input("CH", value=d['ch'], label_visibility="collapsed")
    st.markdown("⚠️ 選擇客戶組別 (Client Group) :red[(必填)]")
    client_group = st.selectbox("Group", [""] + sorted_groups, index=(sorted_groups.index(d['cg'])+1 if d['cg'] in sorted_groups else 0), label_visibility="collapsed")
    st.write("---") 
    
    place_options = ["", "HK", "BVI", "Cayman Island", "Others"]
    st.markdown("⚠️ 成立地點 (Place of Incorporation) :red[(必填)]")
    inc_place = st.selectbox("Place", place_options, index=(place_options.index(d['place']) if d['place'] in place_options else 0), label_visibility="collapsed")
    
    place_others = ""
    if inc_place == "Others": 
        st.markdown("⚠️ 詳細列明其他地點 (Specify Others) :red[(必填)]"); place_others = st.text_input("Others_Input", value=d['p_oth'], label_visibility="collapsed")
    
    if inc_place:
        disp_place = "Others" if inc_place == "Others" else inc_place
        c3, c4 = st.columns(2)
        with c3: st.markdown(f"⚠️ {disp_place} 成立日期 (Incorp. Date) :red[(必填)]"); inc_date = st.date_input("Date", value=to_date(d['idate']), min_value=MIN_DATE, label_visibility="collapsed")
        with c4: st.markdown(f"⚠️ {disp_place} 公司註冊編號 (CI Number) :red[(必填)]"); ci_no = st.text_input("CI", value=d['ci'], label_visibility="collapsed")
    else:
        inc_date = None
        ci_no = ""
    
    is_hk_reg, hk_idate, hk_ci, br_no = False, None, "", ""
    if inc_place == "HK":
        st.markdown("⚠️ 香港商業登記編號 (HK BR Number) :red[(必填)]")
        br_no = st.text_input("BR", value=d['br'], label_visibility="collapsed")
    elif inc_place in ["BVI", "Cayman Island", "Others"]:
        st.write("---")
        is_hk_reg = st.checkbox("是否於香港註冊為非香港公司 (Registered as Non-Hong Kong Company)?", value=d['is_hk_reg'])
        if is_hk_reg:
            st.info("📌 香港註冊詳情 (Hong Kong Registration Details)")
            hk1, hk2 = st.columns(2)
            with hk1: st.markdown("⚠️ 香港註冊日期 (HK Incorp. Date) :red[(必填)]"); hk_idate = st.date_input("HK_Date", value=to_date(d['hk_idate']), min_value=MIN_DATE, label_visibility="collapsed")
            with hk2: st.markdown("⚠️ 香港公司編號 (HK CI Number) :red[(必填)]"); hk_ci = st.text_input("HK_CI", value=d['hk_ci'], label_visibility="collapsed")
            st.markdown("⚠️ 香港商業登記編號 (HK BR Number) :red[(必填)]")
            br_no = st.text_input("BR", value=d['br'], label_visibility="collapsed")

    st.write("---") 
    type_options = ["", "Private Company", "Public Company", "Guarantee", "Individual Business", "Non-Hong Kong Company"]
    st.markdown("⚠️ 公司類別 (Company Type) :red[(必填)]"); co_type = st.selectbox("Type", type_options, index=(type_options.index(d['type']) if d['type'] in type_options else 0), label_visibility="collapsed")

    # ==================== 📅 年度常規申報 ====================
    if inc_place == "HK" or is_hk_reg:
        st.write("---"); st.header("📅 年度常規申報 (Annual Obligations)")
        
        base = hk_idate if is_hk_reg else inc_date
        if base:
            today_cal = datetime.now().date()
            current_year = today_cal.year
            
            nxt_br = get_anniv(current_year, base.month, base.day)
            nxt_ar = nxt_br + timedelta(days=42)
            br_days = (nxt_br - today_cal).days
            ar_days = (nxt_ar - today_cal).days
            
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                if d.get('br_paid_by') == "Client":
                    st.success(f"### 🟢 BR 商業登記費截止日期：**{nxt_br.strftime('%Y/%m/%d')}**\n\n✅ **由客戶自行處理 (Handled by Client)**")
                else:
                    if br_days < 0: st.error(f"### 🚨 BR 商業登記費截止日期：**{nxt_br.strftime('%Y/%m/%d')}**\n\n⚠️ **已經逾期 {abs(br_days)} 天！ (Overdue)**")
                    elif br_days <= 30: st.warning(f"### ⏳ BR 商業登記費截止日期：**{nxt_br.strftime('%Y/%m/%d')}**\n\n⏰ **即將到期（剩餘 {br_days} 天）**")
                    else: st.success(f"### 🟢 BR 商業登記費截止日期：**{nxt_br.strftime('%Y/%m/%d')}**\n\n✅ **狀態：正常 (Normal)**")
                        
            with col_m2:
                if ar_days < 0: st.error(f"### 🚨 AR 周年申報截止日期：**{nxt_ar.strftime('%Y/%m/%d')}**\n\n⚠️ **已經逾期 {abs(ar_days)} 天！ (Overdue)**")
                elif ar_days <= 30: st.warning(f"### ⏳ AR 周年申報截止日期：**{nxt_ar.strftime('%Y/%m/%d')}**\n\n⏰ **即將到期（剩餘 {ar_days} 天）**")
                else: st.success(f"### 🟢 AR 周年申報截止日期：**{nxt_ar.strftime('%Y/%m/%d')}**\n\n✅ **狀態：正常 (Normal)**")
        
        o1, o2, o3 = st.columns([3, 4, 4])
        with o1:
            st.markdown("BR 負責方 (BR Paid By)")
            br_paid_by_opts = ["Firm", "Client"]
            br_paid_by_idx = 1 if d.get('br_paid_by') == "Client" else 0
            br_paid_by = st.selectbox("BR_Paid_By_Sel", br_paid_by_opts, index=br_paid_by_idx, label_visibility="collapsed")
            
        with o2: 
            st.markdown("BR 最新處理日期 (Last BR Resolved Date)")
            if br_paid_by == "Client":
                st.text_input("BR_Paid_Disabled", value="N/A (交由客戶處理)", disabled=True, label_visibility="collapsed")
                l_br = None
            else:
                l_br = st.date_input("L_BR", value=to_date(d['l_br']), min_value=MIN_DATE, label_visibility="collapsed")
                
        with o3: 
            st.markdown("AR 最新提交日期 (Last AR Filed Date)")
            l_ar = st.date_input("L_AR", value=to_date(d['l_ar']), min_value=MIN_DATE, label_visibility="collapsed")
    else:
        br_paid_by, l_br, l_ar = "Firm", None, None

    st.write("---"); st.header("📝 法定申報紀錄 (Compliance Filings)")
    st.subheader("📑 秘書委任 (ND2A - Appointment)")
    cc1, cc2, cc3, cc4 = st.columns([3, 3, 3, 1])
    with cc1: n2e = st.date_input("委任生效日期 (Effective Date)", value=to_date(d['n2e']), min_value=MIN_DATE, key="n2e_v140")
    with cc2: n2f = st.date_input("提交日期 (Filing Date)", value=to_date(d['n2f']), min_value=MIN_DATE, key="n2f_v140")
    with cc3:
        st.info("法定日數 (Statutory Period): 15 days")
        if n2e: n2_deadline = (n2e + timedelta(days=15)); st.markdown(f"**最後限期 (Deadline): :red[{n2_deadline}]**") 
    with cc4: n2d = st.checkbox("已下載 (Downloaded)", value=d['n2d'], key="n2d_v140")
    
    st.subheader("📑 秘書辭任 (ND4 - Resignation)")
    cc5, cc6, cc7, cc8 = st.columns([3, 3, 3, 1])
    with cc5: n4e = st.date_input("辭任生效日期 (Effective Date)", value=to_date(d['n4e']), min_value=MIN_DATE, key="n4e_v140")
    with cc6: n4f = st.date_input("提交日期 (Filing Date)", value=to_date(d['n4f']), min_value=MIN_DATE, key="n4f_v140")
    with cc7:
        st.info("法定日數 (Statutory Period): 15 days")
        if n4e: n4_deadline = (n4e + timedelta(days=15)); st.markdown(f"**最後限期 (Deadline): :red[{n4_deadline}]**") 
    with cc8: n4d = st.checkbox("已下載 (Downloaded)", value=d['n4d'], key="n4d_v140")

    st.write("---"); st.subheader("📍 地址與聯絡 (Address & Contact)")
    ca1, ca2 = st.columns(2)
    with ca1: st.markdown("⚠️ 註冊地址 (Registered Office Address) :red[(必填)]"); reg_addr = st.text_area("Reg", value=d['ra'], label_visibility="collapsed")
    with ca2: st.markdown("⚠️ 通訊地址 (Correspondence Address) :red[(必填)]"); corres_addr = st.text_area("Corres", value=d['ca'], label_visibility="collapsed")
    st.subheader("📔 印章與物品存放 (Seal Storage)")
    l1, l2, l3 = st.columns(3)
    with l1: st.markdown("⚠️ 小圓章位置 (Round Chop Loc.) :red[(必填)]"); round_l = st.text_input("Round", value=d['rl'], label_visibility="collapsed")
    with l2: st.markdown("⚠️ 簽名章位置 (Signature Chop Loc.) :red[(必填)]"); sign_l = st.text_input("Sign", value=d['sl'], label_visibility="collapsed")
    with l3: st.markdown("⚠️ 鋼印位置 (Common Seal Loc.) :red[(必填)]"); common_l = st.text_input("Seal", value=d['cl'], label_visibility="collapsed")
    st.write("---"); st.markdown("公司解散日期 (Dissolution Date)"); dis_date = st.date_input("Dissolution", value=to_date(d['dis']), min_value=MIN_DATE, label_visibility="collapsed")
    
    row_v140 = {'client_group': client_group, 'name_en': name_en, 'name_ch': name_ch, 'incorp_place': inc_place, 'incorp_place_others': place_others, 'incorp_date': inc_date, 'ci_no': ci_no, 'is_hk_registered': is_hk_reg, 'hk_incorp_date': hk_idate, 'hk_ci_no': hk_ci, 'br_no': br_no, 'co_type': co_type, 'reg_addr': reg_addr, 'corres_addr': corres_addr, 'round_loc': round_l, 'sign_loc': sign_l, 'seal_loc': common_l, 'nd2a_eff_date': n2e, 'nd2a_file_date': n2f, 'nd2a_download': n2d, 'nd4_eff_date': n4e, 'nd4_file_date': n4f, 'nd4_download': n4d, 'br_paid_by': br_paid_by, 'last_br_resolved_date': l_br, 'last_ar_filed_date': l_ar, 'dissolution_date': dis_date}
    
    mandatory_fields = {"Client Group": client_group, "English Name": name_en, "Place": inc_place, "Company Type": co_type, "Registered Address": reg_addr, "Correspondence Address": corres_addr, "Round Chop Loc": round_l, "Signature Chop Loc": sign_l, "Common Seal Loc": common_l}
    
    if inc_place:
        mandatory_fields[f"{inc_place} Incorp Date"] = inc_date
        mandatory_fields[f"{inc_place} CI Number"] = ci_no
        if inc_place == "Others": mandatory_fields["Specify Others"] = place_others
        if inc_place == "HK": mandatory_fields["BR Number"] = br_no
        
    if is_hk_reg:
        mandatory_fields["HK Incorp Date"] = hk_idate
        mandatory_fields["HK CI Number"] = hk_ci
        mandatory_fields["HK BR Number"] = br_no
        
    missing = [k for k, v in mandatory_fields.items() if not v or str(v).strip() == ""]

    if mode in ["🆕 新增公司 (Add New)", "📋 複製現有 (Copy Existing)"]:
        if st.button("💾 儲存至雲端 (Save To Cloud)", key="btn_save_v140"):
            if missing: st.error(f"❌ 缺少必填項目 (Missing mandatory fields): {', '.join(missing)}")
            else:
                try:
                    pd.DataFrame([row_v140]).to_sql('companies', engine, if_exists='append', index=False)
                    st.success("✅ 成功儲存 (Success!)"); st.rerun()
                except Exception as save_err:
                    st.error(f"❌ 儲存失敗 (Save Failed!): {save_err}")
    else:
        u_col, d_col = st.columns(2)
        with u_col.popover("🆙 更新資料 (Update)"):
            if st.button("確認更新 (Confirm Update)", key="btn_update_v140"):
                if missing: st.error(f"❌ 缺少必填項目 (Missing mandatory fields): {', '.join(missing)}")
                else:
                    try:
                        df_backup = df_all.copy() 
                        df_all[df_all['name_en'] != target_name].to_sql('companies', engine, if_exists='replace', index=False)
                        pd.DataFrame([row_v140]).to_sql('companies', engine, if_exists='append', index=False)
                        st.success("✅ 成功更新 (Updated!)"); st.rerun()
                    except Exception as trans_err:
                        df_backup.to_sql('companies', engine, if_exists='replace', index=False)
                        st.error(f"🛑 系統攔截錯誤並已復原資料 (Rollback completed). Details: {trans_err}")
        with d_col.popover("🚨 刪除公司 (DELETE)"):
            st.error(f"確定刪除 (Delete) {target_name}?"); conf_s = st.text_input("輸入 DELETE 確認", key="single_del_v140")
            if st.button("確認刪除 (Confirm Delete)", disabled=(conf_s != "DELETE"), key="btn_del_single_v140"):
                df_all[df_all['name_en'] != target_name].to_sql('companies', engine, if_exists='replace', index=False); st.rerun()

# --- 7. 客戶組別管理 (Group Management) ---
elif choice == "⚙️ 客戶組別管理 (Group Management)":
    st.header("⚙️ 客戶組別管理 (Group Management)")
    new_g = st.text_input("輸入新組別名稱 (New Group Name)", key="new_group_input_v140")
    if st.button("新增組別 (Add Group)", key="btn_add_group_v140"): pd.DataFrame([{'group_name': new_g}]).to_sql('client_groups', engine, if_exists='append', index=False); st.rerun()
    st.write("---")
    g_df = pd.read_sql("SELECT * FROM client_groups", engine)
    if not g_df.empty:
        g_df = g_df.sort_values(by=['group_name'], na_position='last')
        target = st.selectbox("選擇組別 (Select Group)", g_df['group_name'].tolist(), key="select_group_manage_v140")
        c1, c2 = st.columns(2)
        with c1.popover("✏️ 重新命名 (Rename)"):
            ren = st.text_input("新名稱 (New Name):", key="rename_input_v140")
            conf_r = st.text_input("輸入 RENAME 確認", key="rename_confirm_text_v140")
            if st.button("確認更改 (Confirm Rename)", disabled=(conf_r != "RENAME"), key="btn_group_rename_v140"):
                comp_df = pd.read_sql("SELECT * FROM companies", engine)
                comp_df.loc[comp_df['client_group'] == target, 'client_group'] = ren
                comp_df.to_sql('companies', engine, if_exists='replace', index=False)
                g_df.replace({target: ren}).to_sql('client_groups', engine, if_exists='replace', index=False); st.rerun()
        with c2.popover("🗑️ 刪除組別 (Delete)"):
            if st.button("確認刪除 (Confirm Delete)", key="btn_group_delete_v140"): 
                g_df[g_df['group_name'] != target].to_sql('client_groups', engine, if_exists='replace', index=False); st.rerun()

# --- 8. 數據匯出與匯入 (Data Exchange) ---
elif choice == "📤 數據匯出與匯入 (Data Exchange)":
    st.header("📤 數據匯出與匯入 (Data Exchange)")
    c1, c2 = st.columns(2)
    
    buf_t = io.BytesIO(); pd.DataFrame(columns=TEMPLATE_COLS).to_excel(buf_t, index=False); c1.download_button(label="📥 下載空白範本 (Template)", data=buf_t.getvalue(), file_name="Template.xlsx")
    
    df_db = pd.read_sql("SELECT * FROM companies", engine); df_export = df_db.copy()
    sort_cols = [c for c in ['client_group', 'name_en', 'incorp_place'] if c in df_export.columns]
    df_export = df_export.sort_values(by=sort_cols, na_position='last')
    
    existing_cols = [c for c in TEMPLATE_COLS if c in df_export.columns]
    df_export = df_export[existing_cols] 
    
    for col in ["incorp_date", "hk_incorp_date", "nd2a_eff_date", "nd2a_file_date", "nd4_eff_date", "nd4_file_date", "last_br_resolved_date", "last_ar_filed_date", "dissolution_date"]:
        if col in df_export.columns: df_export[col] = pd.to_datetime(df_export[col], errors='coerce').dt.strftime('%Y-%m-%d')
    buf_e = io.BytesIO(); df_export.to_excel(buf_e, index=False)
    c2.download_button(label="📦 完整資料備份匯出 (Export All)", data=buf_e.getvalue(), file_name="Backup.xlsx", key="btn_export_all_v140")
    st.write("---")
    
    up = st.file_uploader("上傳 Excel 更新資料 (Upload XLSX to Sync)", type=["xlsx"], key="file_uploader_v140")
    if up:
        try:
            up_df = pd.read_excel(up, engine='openpyxl', keep_default_na=False)
            existing_df = pd.read_sql("SELECT * FROM companies", engine)
            
            for col in ["incorp_date", "hk_incorp_date", "nd2a_eff_date", "nd2a_file_date", "nd4_eff_date", "nd4_file_date", "last_br_resolved_date", "last_ar_filed_date", "dissolution_date"]:
                if col in up_df.columns: up_df[col] = pd.to_datetime(up_df[col], errors='coerce').dt.date
                if col in existing_df.columns: existing_df[col] = pd.to_datetime(existing_df[col], errors='coerce').dt.date

            validation_errors = []
            for idx, row_new in up_df.iterrows():
                excel_row = idx + 2 
                name_en = str(row_new.get('name_en', 'Unknown')).strip()
                place = str(row_new.get('incorp_place', '')).strip()
                is_hk_reg = str(row_new.get('is_hk_registered', 'False')).strip().lower() in ['true', 'yes', 'y', '1']
                
                missing_fields = []
                if not str(row_new.get('client_group', '')).strip(): missing_fields.append("Client Group")
                if not name_en: missing_fields.append("English Name")
                if not place: missing_fields.append("Place of Incorporation")
                if not str(row_new.get('co_type', '')).strip(): missing_fields.append("Company Type")
                if not str(row_new.get('reg_addr', '')).strip(): missing_fields.append("Registered Address")
                if not str(row_new.get('corres_addr', '')).strip(): missing_fields.append("Correspondence Address")
                if not str(row_new.get('round_loc', '')).strip(): missing_fields.append("Round Chop Loc")
                if not str(row_new.get('sign_loc', '')).strip(): missing_fields.append("Signature Chop Loc")
                if not str(row_new.get('seal_loc', '')).strip(): missing_fields.append("Common Seal Loc")
                
                if place:
                    if pd.isnull(row_new.get('incorp_date')): missing_fields.append(f"{place} Incorp Date")
                    if not str(row_new.get('ci_no', '')).strip(): missing_fields.append(f"{place} CI Number")
                    if place == 'Others' and not str(row_new.get('incorp_place_others', '')).strip(): missing_fields.append("Specify Others")
                    if place == 'HK' and not str(row_new.get('br_no', '')).strip(): missing_fields.append("HK BR Number")
                
                if is_hk_reg:
                    if pd.isnull(row_new.get('hk_incorp_date')): missing_fields.append("HK Incorp Date")
                    if not str(row_new.get('hk_ci_no', '')).strip(): missing_fields.append("HK CI Number")
                    if not str(row_new.get('br_no', '')).strip(): missing_fields.append("HK BR Number")
                
                if missing_fields: validation_errors.append(f"**第 {excel_row} 行 ({name_en})** - 缺少必填項目: :red[{', '.join(missing_fields)}]")

            if validation_errors:
                st.error("🛑 **上傳失敗：Excel 檔案內缺少必填資料，請修正後重新上傳。 (Upload Failed: Missing mandatory fields)**")
                for err in validation_errors: st.markdown(f"- {err}")
            else:
                def get_anchor(r):
                    place = str(r.get('incorp_place', '')).strip()
                    name = str(r.get('name_en', '')).strip()
                    return f"NAME_{name}_PLACE_{place}"

                up_df['_anchor'] = up_df.apply(get_anchor, axis=1)
                existing_df['_anchor'] = existing_df.apply(get_anchor, axis=1)
                
                diff_list = []
                for _, row_new in up_df.iterrows():
                    anchor_val = row_new['_anchor']
                    en_name = row_new.get('name_en', 'Unknown')
                    old_row = existing_df[existing_df['_anchor'] == anchor_val]
                    if not old_row.empty:
                        old_row = old_row.iloc[0]
                        for col in TEMPLATE_COLS:
                            old_v = clean_val(old_row.get(col, ""))
                            new_v = clean_val(row_new.get(col, ""))
                            if old_v != new_v:
                                diff_list.append({"公司名稱": en_name, "內部識別碼": anchor_val, "變更欄位": col, "舊數值": old_v if old_v else "N/A", "新數值": new_v if new_v else "N/A"})
                    else:
                        diff_list.append({"公司名稱": en_name, "內部識別碼": anchor_val, "變更欄位": "新增公司 (NEW RECORD)", "舊數值": "N/A", "新數值": "將被新增"})

                if diff_list:
                    st.subheader("🔍 變更預覽 (Review Changes)")
                    st.table(pd.DataFrame(diff_list))
                    if st.button("🚀 確認並寫入資料庫 (Confirm & Apply Changes)", key="btn_final_sync_v140"):
                        combined_df = pd.concat([existing_df, up_df]).drop_duplicates(subset=['_anchor'], keep='last')
                        combined_df = combined_df.drop(columns=['_anchor'])
                        if 'br_paid_by' in combined_df.columns:
                            combined_df['br_paid_by'] = combined_df['br_paid_by'].replace('', 'Firm')
                        if 'br_paid_by' in combined_df.columns and 'last_br_resolved_date' in combined_df.columns:
                            combined_df.loc[combined_df['br_paid_by'] == 'Client', 'last_br_resolved_date'] = None
                            
                        combined_df.to_sql('companies', engine, if_exists='replace', index=False)
                        st.success("✅ 同步完成 (Sync Completed!)"); st.balloons(); st.rerun()
                else: st.info("沒有偵測到任何變更 (No differences found).")
        except Exception as e: st.error(f"系統錯誤 (Error): {e}")
