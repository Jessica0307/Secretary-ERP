import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import io
from weasyprint import HTML

# --- 1. Database Connection ---
engine = create_engine(st.secrets["DB_URL"])

def to_date(val):
    try:
        if pd.isna(val) or val == "" or str(val).lower() in ["none", "nat"]: return None
        return pd.to_datetime(val).date()
    except: return None

def fmt_date(val):
    d = to_date(val)
    return d.strftime('%Y/%m/%d') if d else "N/A"

# --- PDF 生成函式 (V128 原汁原味，僅修改標籤文字) ---
def generate_custom_pdf(selected_df):
    html_content = "<html><head><meta charset='UTF-8'><style>@page { size: A4; margin: 15mm; } body { font-family: sans-serif; }</style></head><body>"
    for _, row in selected_df.iterrows():
        card = f"""
        <div>
            <h2>{row.get('name_en', '')}</h2>
            <p>{row.get('name_ch', '')}</p>
            <hr>
            <p><strong>Incorp. Date / 成立日期 (YYYY/MM/DD):</strong> {fmt_date(row.get('incorp_date'))}</p>
            <p><strong>ND2A Effective Date (YYYY/MM/DD):</strong> {fmt_date(row.get('nd2a_eff_date'))}</p>
            <p><strong>ND4 Effective Date (YYYY/MM/DD):</strong> {fmt_date(row.get('nd4_eff_date'))}</p>
        </div><br><hr>"""
        html_content += card
    html_content += "</body></html>"
    return HTML(string=html_content).write_pdf()

# --- Dashboard 邏輯 (請將你原本完整的 Dashboard 內容貼在下面) ---
# 確保你原本的 'st.download_button' 邏輯維持原樣，不要改動
