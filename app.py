import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import io
from weasyprint import HTML

# --- 1. Database Connection ---
if "DB_URL" not in st.secrets:
    st.error("❌ `DB_URL` missing in Streamlit Secrets!")
    st.stop()
engine = create_engine(st.secrets["DB_URL"])

# --- 2. 工具函式 ---
def to_date(val):
    try:
        if pd.isna(val) or val == "" or str(val).lower() in ["none", "nat"]: return None
        return pd.to_datetime(val).date()
    except: return None

def fmt_date(val):
    d = to_date(val)
    return d.strftime('%Y/%m/%d') if d else "N/A"

# --- 3. PDF 生成 (V128 結構 + 嚴格 YYYY/MM/DD) ---
def generate_custom_pdf(selected_df):
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    html_header = """<html><head><meta charset="UTF-8"><style>
        @page { size: A4; margin: 15mm; }
        body { font-family: sans-serif; }
        .section-bar { background: #f1f4f6; padding: 5px; font-weight: bold; }
        .info-table { width: 100%; border-collapse: collapse; }
        th { text-align: left; width: 40%; color: #7f8c8d; }
    </style></head><body>"""
    
    final_html = html_header
    for _, row in selected_df.iterrows():
        card = f"""
        <div class="company-container">
            <h3>{row.get('name_en', '')}</h3>
            <p>{row.get('name_ch', '')}</p>
            <div class="section-bar">Registration Details / 註冊詳情</div>
            <table class="info-table">
                <tr><th>Client Group</th><td>{row.get('client_group', '')}</td></tr>
                <tr><th>Incorp. Date (YYYY/MM/DD)</th><td>{fmt_date(row.get('incorp_date'))}</td></tr>
                <tr><th>CI No.</th><td>{row.get('ci_no', '')}</td></tr>
                <tr><th>BR No.</th><td>{row.get('br_no', '')}</td></tr>
            </table>
            <div class="section-bar">Compliance Filings / 法定申報</div>
            <table class="info-table">
                <tr><th>ND2A Effective Date (YYYY/MM/DD)</th><td>{fmt_date(row.get('nd2a_eff_date'))}</td></tr>
                <tr><th>ND4 Effective Date (YYYY/MM/DD)</th><td>{fmt_date(row.get('nd4_eff_date'))}</td></tr>
            </table>
        </div>"""
        final_html += card
    final_html += "</body></html>"
    return HTML(string=final_html).write_pdf()

# --- 4. Dashboard (保持原有運作) ---
st.set_page_config(page_title="ERP V128", layout="wide")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "⚙️ Group Management", "📤 Data Exchange"])

if choice == "📊 Dashboard":
    df_raw = pd.read_sql("SELECT * FROM companies", engine)
    st.write(f"📈 Total: **{len(df_raw)}** companies.")
    # (其餘 Dashboard 邏輯維持 V128 不變)
    # 這裡省略過長代碼，請保留你原本 V128 Dashboard 的部分
