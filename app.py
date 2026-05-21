import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import io
from weasyprint import HTML

# (資料庫連線與工具函式保持不變)
try:
    if "DB_URL" not in st.secrets:
        st.error("❌ `DB_URL` missing in Streamlit Secrets!")
        st.stop()
    DB_URL = st.secrets["DB_URL"]
    engine = create_engine(DB_URL)
    with engine.connect() as conn: pass
except Exception as db_err:
    st.error(f"連線錯誤: {db_err}"); st.stop()

def to_date(val):
    try:
        if pd.isna(val) or val == "" or str(val).strip() == "" or str(val).lower() in ["none", "nat"]: return None
        return pd.to_datetime(val).date()
    except: return None

# --- PDF 生成函式 (【V130】：全面統一所有日期顯示為「年月日」格式) ---
def generate_custom_pdf(selected_df):
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    
    # 徹底統一格式化函數
    def fmt_all_dates(val):
        d = to_date(val)
        return d.strftime('%Y年%m月%d日') if d else "N/A"
    
    html_header = """... (HTML/CSS 內容不變) ..."""
    html_header = html_header.replace("__NOW__", now)

    card_template = """... (HTML 卡片結構不變) ..."""

    final_html = html_header
    for _, row in selected_df.iterrows():
        ch_name = row.get('name_ch', '')
        if not ch_name or pd.isna(ch_name): ch_name = ''
        
        card = card_template
        card = card.replace("__NAME_EN__", str(row.get('name_en', '')))
        card = card.replace("__NAME_CH__", str(ch_name))
        card = card.replace("__CLIENT_GROUP__", str(row.get('client_group', '')))
        
        # 【V130 修正】：所有日期欄位統一應用年月日格式
        card = card.replace("__INCORP_DATE__", fmt_all_dates(row.get('incorp_date')))
        card = card.replace("__ND2A_EFF__", fmt_all_dates(row.get('nd2a_eff_date')))
        card = card.replace("__ND4_EFF__", fmt_all_dates(row.get('nd4_eff_date')))
        
        card = card.replace("__INCORP_PLACE__", str(row.get('incorp_place', '')))
        card = card.replace("__CI_NO__", str(row.get('ci_no', '')))
        card = card.replace("__BR_NO__", str(row.get('br_no', '')))
        card = card.replace("__CO_TYPE__", str(row.get('co_type', '')))
        card = card.replace("__REG_ADDR__", str(row.get('reg_addr', '')))
        card = card.replace("__CORRES_ADDR__", str(row.get('corres_addr', '')))
        card = card.replace("__ROUND_LOC__", str(row.get('round_loc', '')))
        card = card.replace("__SIGN_LOC__", str(row.get('sign_loc', '')))
        card = card.replace("__SEAL_LOC__", str(row.get('seal_loc', '')))
        final_html += card

    final_html += "</body></html>"
    return HTML(string=final_html).write_pdf()

# --- (其餘 Dashboard, Register, Group, Exchange 邏輯保持 V129 原貌) ---
# (為了確保你睇到修正，我上面簡化咗部分顯示，你原本個程式碼後半部不用改)
