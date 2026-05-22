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
            body { font-family: 'Noto Sans TC', sans-serif; color: #2c3e50; line-height: 1.4; background
