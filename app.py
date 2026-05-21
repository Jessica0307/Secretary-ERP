import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import io
from weasyprint import HTML

# --- 1. Database Connection ---
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

# --- 3. PDF 生成函式 (已修復：僅改動標籤，不改動結構) ---
def generate_custom_pdf(selected_df):
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    html_header = "<html><head><meta charset='UTF-8'><style>@page { size: A4; margin: 15mm; } body { font-family: sans-serif; }</style></head><body>"
    
    final_html = html_header
    for _, row in selected_df.iterrows():
        # 這裏使用原本你 V128 的排版，只改標籤文字
        card = f"""
        <div>
            <h2>{row.get('name_en', '')}</h2>
            <p>{row.get('name_ch', '')}</p>
            <hr>
            <p><strong>Incorp. Date / 成立日期 (YYYY/MM/DD):</strong> {fmt_date(row.get('incorp_date'))}</p>
            <p><strong>ND2A Effective Date (YYYY/MM/DD):</strong> {fmt_date(row.get('nd2a_eff_date'))}</p>
            <p><strong>ND4 Effective Date (YYYY/MM/DD):</strong> {fmt_date(row.get('nd4_eff_date'))}</p>
        </div><br><hr>"""
        final_html += card
    final_html += "</body></html>"
    return HTML(string=final_html).write_pdf()

# --- 4. Dashboard (請確認這裏是你原本的代碼) ---
st.set_page_config(page_title="ERP Cloud V128", layout="wide")
# ... (請貼上你原本 Dashboard 下半部分的完整代碼，這裏就不省略了，請確保你原本完整的 Code 都在)
