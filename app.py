import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
import io
from weasyprint import HTML

# 確保連線正常
engine = create_engine(st.secrets["DB_URL"])

# 核心工具函式
def to_date(val):
    try:
        if pd.isna(val) or val == "" or str(val).lower() in ["none", "nat"]: return None
        return pd.to_datetime(val).date()
    except: return None

def fmt_date(val):
    d = to_date(val)
    return d.strftime('%Y/%m/%d') if d else "N/A"

# PDF 生成函式 (完全保留 V128 排版，僅修改標籤名稱)
def generate_custom_pdf(selected_df):
    html_header = """<html><head><meta charset="UTF-8"><style>
        @page { size: A4; margin: 15mm; }
        body { font-family: sans-serif; }
        .section-bar { background: #f1f4f6; padding: 5px; font-weight: bold; border-left: 5px solid #3498db; margin: 10px 0; }
        .info-table { width: 100%; border-collapse: collapse; }
        th { text-align: left; width: 45%; color: #7f8c8d; padding: 5px; }
        td { padding: 5px; }
    </style></head><body>"""
    
    final_html = html_header
    for _, row in selected_df.iterrows():
        # 這裡嚴格跟足 V128 的所有欄位，一個都唔少
        card = f"""
        <div class="company-container">
            <h2>{row.get('name_en', '')}</h2>
            <p>{row.get('name_ch', '')}</p>
            <div class="section-bar">Registration Details / 註冊詳情</div>
            <table class="info-table">
                <tr><th>Client Group</th><td>{row.get('client_group', '')}</td></tr>
                <tr><th>Incorp. Date (YYYY/MM/DD)</th><td>{fmt_date(row.get('incorp_date'))}</td></tr>
                <tr><th>Incorp. Place</th><td>{row.get('incorp_place', '')}</td></tr>
                <tr><th>CI No.</th><td>{row.get('ci_no', '')}</td></tr>
                <tr><th>BR No.</th><td>{row.get('br_no', '')}</td></tr>
                <tr><th>Co. Type</th><td>{row.get('co_type', '')}</td></tr>
            </table>
            <div class="section-bar">Addresses / 地址</div>
            <table class="info-table">
                <tr><th>Reg. Address</th><td>{row.get('reg_addr', '')}</td></tr>
                <tr><th>Corres. Address</th><td>{row.get('corres_addr', '')}</td></tr>
            </table>
            <div class="section-bar">Items Storage</div>
            <table class="info-table">
                <tr><th>Round Stamp</th><td>{row.get('round_loc', '')}</td></tr>
                <tr><th>Signature Chop</th><td>{row.get('sign_loc', '')}</td></tr>
                <tr><th>Common Seal</th><td>{row.get('seal_loc', '')}</td></tr>
            </table>
            <div class="section-bar">Compliance Filings / 法定申報</div>
            <table class="info-table">
                <tr><th>ND2A Effective Date (YYYY/MM/DD)</th><td>{fmt_date(row.get('nd2a_eff_date'))}</td></tr>
                <tr><th>ND4 Effective Date (YYYY/MM/DD)</th><td>{fmt_date(row.get('nd4_eff_date'))}</td></tr>
            </table>
        </div><br><hr><br>"""
        final_html += card
    final_html += "</body></html>"
    return HTML(string=final_html).write_pdf()

# --- 恢復原本的按鈕邏輯 ---
# 檢查你的 Dashboard 頁面中，這段程式碼是否還在：
if st.button("📥 Export Selected PDF"):
    final_data = df_raw[df_raw['name_en'].isin(selected['name_en'])]
    st.download_button(
        label="Download PDF", 
        data=generate_custom_pdf(final_data), 
        file_name="Report.pdf", 
        mime="application/pdf"
    )
