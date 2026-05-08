import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import io
from weasyprint import HTML  # 請確保環境已安裝此套件

# --- 1. Database Connection (鎖定 V28) ---
try:
    DB_URL = st.secrets["DB_URL"]
    engine = create_engine(DB_URL)
except:
    st.error("❌ Please check DB_URL in Secrets")
    st.stop()

# --- 2. Navigation ---
st.set_page_config(page_title="ERP Cloud V33", layout="wide")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "⚙️ Group Management", "📤 Data Exchange"])

# --- PDF 生成函式 ---
def generate_pdf_report(df):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    html_content = f"""
    <html>
    <head>
        <style>
            @page {{ size: A4; margin: 15mm; }}
            body {{ font-family: 'Arial', sans-serif; color: #2c3e50; line-height: 1.4; }}
            .header {{ text-align: center; border-bottom: 2px solid #34495e; padding-bottom: 10px; margin-bottom: 20px; }}
            .company-card {{ page-break-inside: avoid; border: 1px solid #dcdde1; border-radius: 5px; padding: 15px; margin-bottom: 20px; background-color: #f9f9f9; }}
            .name-en {{ font-size: 14pt; font-weight: bold; color: #2980b9; }}
            .name-ch {{ font-size: 12pt; color: #34495e; margin-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; font-size: 9pt; }}
            th {{ text-align: left; width: 30%; color: #7f8c8d; border-bottom: 1px solid #eee; padding: 4px 0; }}
            td {{ border-bottom: 1px solid #eee; padding: 4px 0; }}
            .section-title {{ background: #ebf3f9; padding: 3px 8px; font-weight: bold; font-size: 10pt; margin: 10px 0 5px 0; border-radius: 3px; }}
        </style>
    </head>
    <body>
        <div class="header"><h1>Corporate Portfolio Report</h1><p>Generated: {now}</p></div>
    """
    for _, row in df.iterrows():
        html_content += f"""
        <div class="company-card">
            <div class="name-en">{row.get('name_en','')}</div>
            <div class="name-ch">{row.get('name_ch','')}</div>
            <div class="section-title">Registration Info</div>
            <table>
                <tr><th>Group</th><td>{row.get('client_group','')}</td></tr>
                <tr><th>Incorp. Date</th><td>{row.get('incorp_date','')} ({row.get('incorp_place','')})</td></tr>
                <tr><th>CI / BR No.</th><td>{row.get('ci_no','')} / {row.get('br_no','')}</td></tr>
            </table>
            <div class="section-title">Addresses</div>
            <table>
                <tr><th>Registered</th><td>{row.get('reg_addr','')}</td></tr>
                <tr><th>Correspondence</th><td>{row.get('corres_addr','')}</td></tr>
            </table>
            <div class="section-title">Items Location</div>
            <table>
                <tr><th>Round / Sign / Seal</th><td>{row.get('round_loc','')} / {row.get('sign_loc','')} / {row.get('seal_loc','')}</td></tr>
            </table>
        </div>"""
    html_content += "</body></html>"
    return HTML(string=html_content).write_pdf()

# --- 3. Data Exchange (新增 PDF 導出) ---
if choice == "📤 Data Exchange":
    st.header("📤 Data Exchange & Backup")
    
    st.subheader("1. PDF Portfolio Report")
    if st.button("📄 Prepare PDF Report"):
        df_all = pd.read_sql("SELECT * FROM companies", engine)
        if not df_all.empty:
            pdf_data = generate_pdf_report(df_all)
            st.download_button(label="📥 Download PDF Report", data=pdf_data, file_name=f"Company_Report_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf")
        else:
            st.warning("No data to export.")

    st.write("---")
    st.subheader("2. Excel Backup & Templates")
    col_ex1, col_ex2 = st.columns(2)
    # ... (保留原本的 Excel 備份功能代碼，同 V32) ...
    df_all_export = pd.read_sql("SELECT * FROM companies", engine)
    buffer_all = io.BytesIO()
    with pd.ExcelWriter(buffer_all, engine='xlsxwriter') as writer:
        df_all_export.to_excel(writer, index=False)
    col_ex2.download_button(label="📦 Export All Data (Excel)", data=buffer_all.getvalue(), file_name="Full_Backup.xlsx")

# --- 其餘部分 (Dashboard, Register 等) 保持 V32 的鎖定邏輯 ---
# ... (請將 V32 的其餘代碼合併至此) ...
