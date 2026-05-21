import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import io
from weasyprint import HTML

# --- 1. Database Connection ---
try:
    if "DB_URL" not in st.secrets:
        st.error("❌ `DB_URL` missing in Streamlit Secrets!")
        st.stop()
    DB_URL = st.secrets["DB_URL"]
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        pass
except Exception as db_err:
    st.error(f"連線錯誤: {db_err}")
    st.stop()

# --- 2. 工具函式 ---
def to_date(val):
    try:
        if pd.isna(val) or val == "" or str(val).strip() == "" or str(val).lower() in ["none", "nat"]:
            return None
        return pd.to_datetime(val).date()
    except:
        return None

def fmt_date(val):
    d = to_date(val)
    return d.strftime('%Y/%m/%d') if d else "N/A"

# --- 3. Navigation ---
st.set_page_config(page_title="ERP Cloud V128", layout="wide")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "⚙️ Group Management", "📤 Data Exchange"])

# --- 4. PDF 生成函式 (已修復成立日期標籤) ---
def generate_custom_pdf(selected_df):
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    
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
            .header-content { text-align: center; border-bottom: 1px solid #eee; padding-bottom: 15px; margin-bottom: 20px; }
            .name-en { font-size: 20pt; font-weight: bold; color: #2980b9; text-align: center; }
            .name-ch { font-size: 15pt; color: #333333; margin-top: 5px; text-align: center; min-height: 20px; }
            .section-bar { background-color: #f1f4f6; padding: 8px 15px; font-weight: bold; font-size: 11pt; margin: 20px 0 10px 0; border-left: 5px solid #3498db; color: #2c3e50; text-align: left; }
            .info-table { width: 100%; border-collapse: collapse; }
            .info-table th { text-align: left; width: 45%; color: #7f8c8d; padding: 8px 0; font-weight: normal; font-size: 10.5pt; }
            .info-table td { text-align: justify; padding: 8px 0; color: #2c3e50; font-size: 10.5pt; font-weight: bold; }
        </style>
    </head>
    <body>
        <div id="footer">
            <table class="footer-table">
                <tr>
                    <td class="footer-left">Corporate Portfolio Report</td>
                    <td class="footer-right">Generated on: """ + now + """</td>
                </tr>
            </table>
        </div>
    """

    final_html = html_header
    for _, row in selected_df.iterrows():
        card = f"""
        <div class="company-container">
            <table class="main-table">
                <thead><tr><td><div class="header-content"><div class="name-en">{row.get('name_en','')}</div><div class="name-ch">{row.get('name_ch','') if row.get('name_ch') else ''}</div></div></td></tr></thead>
                <tbody><tr><td>
                    <div class="section-bar">Registration Details / 註冊詳情</div>
                    <table class="info-table">
                        <tr><th>Client Group / 客戶組別</th><td>{row.get('client_group','')}</td></tr>
                        <tr><th>Incorp. Date / 成立日期 (YYYY/MM/DD)</th><td>{fmt_date(row.get('incorp_date'))}</td></tr>
                        <tr><th>Incorp. Place / 成立地點</th><td>{row.get('incorp_place','')}</td></tr>
                        <tr><th>CI No. / 公司註冊編號</th><td>{row.get('ci_no','')}</td></tr>
                        <tr><th>BR No. / 商業登記編號</th><td>{row.get('br_no','')}</td></tr>
                        <tr><th>Company Type / 公司類別</th><td>{row.get('co_type','')}</td></tr>
                    </table>
                    <div class="section-bar">Addresses / 地址</div>
                    <table class="info-table">
                        <tr><th>Registered Address / 註冊地址</th><td>{row.get('reg_addr','')}</td></tr>
                        <tr><th>Correspondence Address / 通訊地址</th><td>{row.get('corres_addr','')}</td></tr>
                    </table>
                    <div class="section-bar">Items Storage / 物品存放位置</div>
                    <table class="info-table">
                        <tr><th>Round Stamp / 小圓章</th><td>{row.get('round_loc','')}</td></tr>
                        <tr><th>Signature Chop / 簽名章</th><td>{row.get('sign_loc','')}</td></tr>
                        <tr><th>Common Seal / 鋼印</th><td>{row.get('seal_loc','')}</td></tr>
                    </table>
                    <div class="section-bar">Compliance Filings / 法定申報</div>
                    <table class="info-table">
                        <tr><th>ND2A Effective Date (YYYY/MM/DD)</th><td>{fmt_date(row.get('nd2a_eff_date'))}</td></tr>
                        <tr><th>ND4 Effective Date (YYYY/MM/DD)</th><td>{fmt_date(row.get('nd4_eff_date'))}</td></tr>
                    </table>
                </td></tr></tbody>
            </table>
        </div>"""
        final_html += card
    final_html += "</body></html>"
    return HTML(string=final_html).write_pdf()

# --- (保持你原本所有的 Dashboard, Register, Group, Exchange 邏輯不變，省略以節省篇幅) ---
# ... (請將此處貼上你原始檔案從 Dashboard 到 Data Exchange 的所有代碼)
