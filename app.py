import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import io
from weasyprint import HTML

# --- 1. Database Connection (持續健康檢查與底層報錯拦截) ---
try:
    if "DB_URL" not in st.secrets:
        st.error("❌ `DB_URL` missing in Streamlit Secrets! Please configure it in Settings -> Secrets.")
        st.stop()
    
    DB_URL = st.secrets["DB_URL"]
    engine = create_engine(DB_URL)
    
    # 測試連線握手
    with engine.connect() as conn:
        pass
except Exception as db_err:
    st.error("### 🛑 Database Connection Critical Failure")
    st.markdown("Your code is correct, but python failed to handshake with your Database.")
    st.info(f"**Actual Underlying Error Details:**\n`{str(db_err)}`")
    st.markdown("""
    💡 **Supabase (ENOTFOUND) 租戶未找到錯誤修復對策：**
    
    1. **最推薦做法（Direct Connection）**：
        請前往 Supabase 後台獲取 **Direct** 連線字串，將 Port 由 `6543` 修改回 **`5432`**，Host 改為直連域名（通常沒有 `pooler` 字眼），User 改回最純淨的 **`postgres`**。
    
    2. **Pooler 做法**：
        若必須使用 `6543`，請重新複製 Supabase 後台最新版本的字串。新版 Pooler 的 User 格式後面通常必須強制定義模式（例如 `.transaction`）。
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
st.set_page_config(page_title="ERP Cloud V128", layout="wide")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "⚙️ Group Management", "📤 Data Exchange"])

# --- 4. PDF 生成函式 (已針對 PDF 標籤進行精準修正) ---
def generate_custom_pdf(selected_df):
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    def fmt_date(val):
        d = to_date(val)
        return d.strftime('%Y/%m/%d') if d else "N/A"
    
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
                    <td class="footer-right">Generated on: """ + now + """</td>
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
                                <div class="section-bar">Registration Details / 註冊詳情</div>
                                <table class="info-table">
                                    <tr><th>Client Group / 客戶組別</th><td>__CLIENT_GROUP__</td></tr>
                                    <tr><th>Incorp. Date / 成立日期 (YYYY/MM/DD)</th><td>__INCORP_DATE__</td></tr>
                                    <tr><th>Incorp. Place / 成立地點</th><td>__INCORP_PLACE__</td></tr>
                                    <tr><th>CI No. / 公司註冊編號</th><td>__CI_NO__</td></tr>
                                    <tr><th>BR No. / 商業登記編號</th><td>__BR_NO__</td></tr>
                                    <tr><th>Company Type / 公司類別</th><td>__CO_TYPE__</td></tr>
                                    <tr><th>Cayman Incorp. Date (YYYY/MM/DD)</th><td>__CAYMAN_INCORP_DATE__</td></tr>
                                    <tr><th>Cayman CI No.</th><td>__CAYMAN_CI_NO__</td></tr>
                                </table>
                            </div>
                            <div class="section-group">
                                <div class="section-bar">Addresses / 地址</div>
                                <table class="info-table">
                                    <tr><th>Registered Address / 註冊地址</th><td>__REG_ADDR__</td></tr>
                                    <tr><th>Correspondence Address / 通訊地址</th><td>__CORRES_ADDR__</td></tr>
                                </table>
                            </div>
                            <div class="section-group">
                                <div class="section-bar">Items Storage / 物品存放位置</div>
                                <table class="info-table">
                                    <tr><th>Round Stamp / 小圓章</th><td>__ROUND_LOC__</td></tr>
                                    <tr><th>Signature Chop / 簽名章</th><td>__SIGN_LOC__</td></tr>
                                    <tr><th>Common Seal / 鋼印</th><td>__SEAL_LOC__</td></tr>
                                </table>
                            </div>
                            <div class="section-group">
                                <div class="section-bar">Compliance Filings / 法定申報</div>
                                <table class="info-table">
                                    <tr><th>ND2A Effective Date (YYYY/MM/DD)</th><td>__ND2A_EFF__</td></tr>
                                    <tr><th>ND4 Effective Date (YYYY/MM/DD)</th><td>__ND4_EFF__</td></tr>
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
        
        card = card_template
        card = card.replace("__NAME_EN__", str(row.get('name_en', '')))
        card = card.replace("__NAME_CH__", str(ch_name))
        card = card.replace("__CLIENT_GROUP__", str(row.get('client_group', '')))
        card = card.replace("__INCORP_DATE__", fmt_date(row.get('incorp_date')))
        card = card.replace("__INCORP_PLACE__", str(row.get('incorp_place', '')))
        card = card.replace("__CI_NO__", str(row.get('ci_no', '')))
        card = card.replace("__BR_NO__", str(row.get('br_no', '')))
        card = card.replace("__CO_TYPE__", str(row.get('co_type', '')))
        card = card.replace("__REG_ADDR__", str(row.get('reg_addr', '')))
        card = card.replace("__CORRES_ADDR__", str(row.get('corres_addr', '')))
        card = card.replace("__ROUND_LOC__", str(row.get('round_loc', '')))
        card = card.replace("__SIGN_LOC__", str(row.get('sign_loc', '')))
        card = card.replace("__SEAL_LOC__", str(row.get('seal_loc', '')))
        card = card.replace("__ND2A_EFF__", fmt_date(row.get('nd2a_eff_date')))
        card = card.replace("__ND4_EFF__", fmt_date(row.get('nd4_eff_date')))
        card = card.replace("__CAYMAN_INCORP_DATE__", fmt_date(row.get('cayman_incorp_date')))
        card = card.replace("__CAYMAN_CI_NO__", str(row.get('cayman_ci_no', '')))
        final_html += card

    final_html += "</body></html>"
    return HTML(string=final_html).write_pdf()

# --- 5. Dashboard ---
if choice == "📊 Dashboard":
    st.header("📊 Compliance Overview")
    df_raw = pd.read_sql("SELECT * FROM companies", engine)
    groups = pd.read_sql("SELECT group_name FROM client_groups", engine)['group_name'].tolist()
    
    if not df_raw.empty:
        for col in ["incorp_date", "cayman_incorp_date", "nd2a_eff_date", "nd4_eff_date", "nd2a_file_date", "nd4_file_date", "dissolution_date"]:
            if col in df_raw.columns
