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

# --- PDF 生成函式 (純日期、逐項列出) ---
def generate_custom_pdf(selected_df):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    def fmt_date(val):
        if pd.isna(val) or str(val).strip().lower() in ["none", "nan", "n/a", ""]:
            return "N/A"
        try:
            return pd.to_datetime(val).strftime('%Y-%m-%d')
        except:
            return str(val)

    html_content = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{ size: A4; margin: 15mm; }}
            body {{ font-family: 'Arial', 'Microsoft JhengHei', 'PingFang TC', sans-serif; color: #2c3e50; line-height: 1.6; }}
            .header {{ text-align: center; border-bottom: 2px solid #34495e; padding-bottom: 10px; margin-bottom: 20px; }}
            .company-card {{ page-break-inside: avoid; border: 1px solid #dcdde1; border-radius: 8px; padding: 25px; margin-bottom: 30px; background-color: #fbfbfb; }}
            .name-en {{ font-size: 18pt; font-weight: bold; color: #2980b9; }}
            .name-ch {{ font-size: 15pt; color: #333; margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 5px; font-size: 10pt; }}
            th {{ text-align: left; width: 45%; color: #7f8c8d; border-bottom: 1px solid #f1f2f6; padding: 8px 0; font-weight: bold; }}
            td {{ border-bottom: 1px solid #f1f2f6; padding: 8px 0; color: #2c3e50; }}
            .section-title {{ background: #f1f4f6; padding: 5px 12px; font-weight: bold; font-size: 11pt; margin-top: 20px; border-left: 4px solid #3498db; }}
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

# --- 5. Dashboard (全面移除時間顯示) ---
elif choice == "📊 Dashboard":
    st.header("📊 Compliance Overview")
    df_raw = pd.read_sql("SELECT * FROM companies", engine)
    groups = pd.read_sql("SELECT group_name FROM client_groups", engine)['group_name'].tolist()
    
    if not df_raw.empty:
        # 工具列
        t1, t2, t3, t4 = st.columns([3, 2, 2, 5])
        filter_g = t1.selectbox("🔍 Filter by Group", ["All Groups"] + groups)
        if t2.button("🔄 Refresh"): st.rerun()
        
        df_filtered = df_raw if filter_g == "All Groups" else df_raw[df_raw['client_group'] == filter_g]
        
        # 批量選取
        if 'select_state' not in st.session_state: st.session_state.select_state = False
        if t3.button("✅ Select All Shown"): st.session_state.select_state = True; st.rerun()
        if t4.button("🧹 Clear All"): st.session_state.select_state = False; st.rerun()

        # --- 重要：格式化顯示數據，移除所有時間 ---
        df_display = df_filtered.copy()
        date_cols = ["incorp_date", "nd2a_eff_date", "nd2a_file_date", "nd4_eff_date", "nd4_file_date", "dissolution_date"]
        for col in date_cols:
            if col in df_display.columns:
                # 轉換為日期對象，這會讓 UI 自動隱藏 00:00:00
                df_display[col] = pd.to_datetime(df_display[col], errors='coerce').dt.date

        df_display.insert(0, "Select", st.session_state.select_state)
        
        # 使用 DateColumn 配置進一步確保介面簡潔
        edited_df = st.data_editor(
            df_display, 
            column_config={
                "Select": st.column_config.CheckboxColumn("Select", default=False),
                "incorp_date": st.column_config.DateColumn("Incorp Date", format="YYYY-MM-DD"),
                "nd2a_eff_date": st.column_config.DateColumn("ND2A Eff", format="YYYY-MM-DD"),
                "nd4_eff_date": st.column_config.DateColumn("ND4 Eff", format="YYYY-MM-DD"),
            }, 
            disabled=[c for c in df_display.columns if c != "Select"], 
            hide_index=True, use_container_width=True, key="dashboard_editor_v38"
        )
        
        selected_rows = edited_df[edited_df["Select"] == True]
        
        if len(selected_rows) > 0:
            st.info(f"已選取 {len(selected_rows)} 筆紀錄")
            act1, act2 = st.columns([3, 7])
            with act1:
                if st.button("📥 Export Selected to PDF"):
                    final_selected = df_raw[df_raw['name_en'].isin(selected_rows['name_en'])]
                    pdf_bytes = generate_custom_pdf(final_selected)
                    st.download_button(label="Click to Download PDF", data=pdf_bytes, file_name="Selected_Portfolio.pdf", mime="application/pdf")
            
            with act2.popover("🧨 BATCH DELETE"):
                st.error("### 🛑 DANGER ZONE")
                user_conf = st.text_input("Type DELETE to confirm", key="batch_del_input")
                if st.button("🔥 Confirm Delete", disabled=(user_conf != "DELETE")):
                    to_del = selected_rows["name_en"].tolist()
                    df_raw[~df_raw["name_en"].isin(to_del)].to_sql('companies', engine, if_exists='replace', index=False)
                    st.success("Deleted!"); st.rerun()
    else: st.info("No records.")

# --- 其他部分保持鎖定 V32 的純淨度 ---
# ... (Register, Group, Exchange 保持 V32 的紅框必填與邏輯，日期欄位在 Add New 時本來就是 date_input) ...
