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
st.set_page_config(page_title="ERP Cloud V39", layout="wide")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "⚙️ Group Management", "📤 Data Exchange"])

# --- PDF 生成函式 (每頁標題 + 一公司一頁) ---
def generate_custom_pdf(selected_df):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    def fmt_date(val):
        if pd.isna(val) or str(val).strip().lower() in ["none", "nan", "n/a", ""]:
            return "N/A"
        try:
            return pd.to_datetime(val).strftime('%Y-%m-%d')
        except:
            return str(val)

    # CSS 增加分頁與頁首控制
    html_content = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{ 
                size: A4; 
                margin: 15mm; 
                @top-center {{
                    content: element(header);
                }}
            }}
            body {{ 
                font-family: 'Arial', 'Microsoft JhengHei', 'PingFang TC', sans-serif; 
                color: #2c3e50; 
                line-height: 1.5; 
            }}
            /* 讓 Header 在每頁重複出現 */
            .report-header {{ 
                display: table-header-group;
                text-align: center; 
                width: 100%;
            }}
            .header-content {{
                border-bottom: 2px solid #34495e; 
                padding-bottom: 10px; 
                margin-bottom: 20px;
                text-align: center;
            }}
            /* 公司卡片：強制每間公司完結後分頁，且內部不拆分 */
            .company-card {{ 
                page-break-after: always; 
                page-break-inside: avoid; 
                border: 1px solid #dcdde1; 
                border-radius: 8px; 
                padding: 20px; 
                background-color: #fbfbfb;
            }}
            /* 最後一間公司不需要額外的空白頁 */
            .company-card:last-child {{
                page-break-after: auto;
            }}
            .name-en {{ font-size: 18pt; font-weight: bold; color: #2980b9; }}
            .name-ch {{ font-size: 15pt; color: #333; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 5px; font-size: 10pt; }}
            th {{ text-align: left; width: 45%; color: #7f8c8d; border-bottom: 1px solid #f1f2f6; padding: 7px 0; font-weight: bold; }}
            td {{ border-bottom: 1px solid #f1f2f6; padding: 7px 0; color: #2c3e50; }}
            .section-title {{ background: #f1f4f6; padding: 5px 12px; font-weight: bold; font-size: 11pt; margin-top: 15px; border-left: 4px solid #3498db; }}
        </style>
    </head>
    <body>
        <table style="width: 100%;">
            <thead class="report-header">
                <tr>
                    <td>
                        <div class="header-content">
                            <h1 style="margin: 0; font-size: 20pt;">Corporate Portfolio Report</h1>
                            <p style="margin: 5px 0; font-size: 10pt; color: #7f8c8d;">Generated on: {now}</p>
                        </div>
                    </td>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>
    """
    
    for _, row in selected_df.iterrows():
        html_content += f"""
        <div class="company-card">
            <div class="name-en">{row.get('name_en','')}</div>
            <div class="name-ch">{row.get('name_ch','')}</div>
            
            <div class="section-title">Registration Details / 註冊詳情</div>
            <table>
                <tr><th>Client Group / 客戶組別</th><td>{row.get('client_group','')}</td></tr>
                <tr><th>Incorp. Date / 成立日期</th><td>{fmt_date(row.get('incorp_date'))}</td></tr>
                <tr><th>Incorp. Place / 成立地點</th><td>{row.get('incorp_place','')}</td></tr>
                <tr><th>CI No. / 公司註冊編號</th><td>{row.get('ci_no','')}</td></tr>
                <tr><th>BR No. / 商業登記編號</th><td>{row.get('br_no','')}</td></tr>
                <tr><th>Company Type / 公司類別</th><td>{row.get('co_type','')}</td></tr>
            </table>

            <div class="section-title">Compliance Filings / 法定申報</div>
            <table>
                <tr><th>ND2A Effective Date</th><td>{fmt_date(row.get('nd2a_eff_date'))}</td></tr>
                <tr><th>ND4 Effective Date</th><td>{fmt_date(row.get('nd4_eff_date'))}</td></tr>
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
        
    html_content += """
                    </td>
                </tr>
            </tbody>
        </table>
    </body>
    </html>
    """
    return HTML(string=html_content).write_pdf()

# --- 5. Dashboard (維持 V38 的純日期顯示邏輯) ---
elif choice == "📊 Dashboard":
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
                    st.download_button(label="Click to Download PDF", data=pdf_bytes, file_name=f"Portfolio_Report_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf")
            
            with act2.popover("🧨 BATCH DELETE"):
                st.error("### 🛑 DANGER ZONE")
                user_conf = st.text_input("Type DELETE to confirm", key="batch_del_input")
                if st.button("🔥 Confirm Delete", disabled=(user_conf != "DELETE")):
                    to_del = selected_rows["name_en"].tolist()
                    df_raw[~df_raw["name_en"].isin(to_del)].to_sql('companies', engine, if_exists='replace', index=False)
                    st.success("Deleted!"); st.rerun()
    else: st.info("No records.")
