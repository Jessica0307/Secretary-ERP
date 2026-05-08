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
st.set_page_config(page_title="ERP Cloud V36", layout="wide")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "⚙️ Group Management", "📤 Data Exchange"])

# --- PDF 生成函式 (加入中文字型支援) ---
def generate_custom_pdf(selected_df):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # CSS 中加入了微軟正黑體、萍方等常用中文字型
    html_content = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{ size: A4; margin: 15mm; }}
            body {{ 
                font-family: 'Arial', 'Microsoft JhengHei', 'PingFang TC', 'Noto Sans TC', sans-serif; 
                color: #2c3e50; 
                line-height: 1.4; 
            }}
            .header {{ text-align: center; border-bottom: 2px solid #34495e; padding-bottom: 10px; margin-bottom: 20px; }}
            .company-card {{ page-break-inside: avoid; border: 1px solid #dcdde1; border-radius: 8px; padding: 20px; margin-bottom: 25px; background-color: #fbfbfb; }}
            .name-en {{ font-size: 16pt; font-weight: bold; color: #2980b9; }}
            .name-ch {{ font-size: 14pt; color: #333; margin-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 10pt; }}
            th {{ text-align: left; width: 35%; color: #7f8c8d; border-bottom: 1px solid #eee; padding: 6px 0; }}
            td {{ border-bottom: 1px solid #eee; padding: 6px 0; color: #2c3e50; }}
            .section-title {{ background: #ebf3f9; padding: 5px 10px; font-weight: bold; font-size: 11pt; margin-top: 15px; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="header"><h1>Corporate Portfolio Report</h1><p>Records: {len(selected_df)} | Generated: {now}</p></div>
    """
    for _, row in selected_df.iterrows():
        html_content += f"""
        <div class="company-card">
            <div class="name-en">{row.get('name_en','')}</div>
            <div class="name-ch">{row.get('name_ch','')}</div>
            <div class="section-title">Registration & Legal / 註冊資料</div>
            <table>
                <tr><th>Client Group</th><td>{row.get('client_group','')}</td></tr>
                <tr><th>Incorp. Date / Place</th><td>{row.get('incorp_date','')} ({row.get('incorp_place','')})</td></tr>
                <tr><th>CI No. / BR No.</th><td>{row.get('ci_no','')} / {row.get('br_no','')}</td></tr>
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

# --- 5. Dashboard (維持 V35 優化，修正 PDF 中文) ---
elif choice == "📊 Dashboard":
    st.header("📊 Compliance Overview & Batch Actions")
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
        df_display.insert(0, "Select", st.session_state.select_state)
        
        edited_df = st.data_editor(df_display, column_config={"Select": st.column_config.CheckboxColumn("Select", default=False)}, disabled=[c for c in df_display.columns if c != "Select"], hide_index=True, use_container_width=True, key="dashboard_editor_v36")
        
        selected_rows = edited_df[edited_df["Select"] == True]
        
        if len(selected_rows) > 0:
            st.info(f"已選取 {len(selected_rows)} 筆紀錄")
            act1, act2 = st.columns([3, 7])
            with act1:
                if st.button("📥 Export Selected to PDF"):
                    pdf_bytes = generate_custom_pdf(selected_rows)
                    st.download_button(label="Click to Download PDF", data=pdf_bytes, file_name=f"Selected_Report_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf")
            
            # 批量刪除邏輯 (維持 V32 安全鎖)
            with act2.popover("🧨 CRITICAL: BATCH DELETE"):
                st.error("### 🛑 DANGER ZONE")
                user_conf = st.text_input(f"請輸入 **DELETE** 確認", key="batch_del_input")
                if st.button("🔥 確認永久刪除", disabled=(user_conf != "DELETE")):
                    to_del = selected_rows["name_en"].tolist()
                    df_raw[~df_raw["name_en"].isin(to_del)].to_sql('companies', engine, if_exists='replace', index=False)
                    st.success("已清理紀錄！"); st.rerun()
    else: st.info("No records.")

# --- 其他 Section (Register, Group, Exchange) 均保持 V32/V35 鎖定邏輯 ---
# ... (請參考前一版本代碼完整合併) ...
