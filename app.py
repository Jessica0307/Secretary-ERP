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

# --- 3. PDF 生成函式 (V128 結構，僅標籤更新) ---
def generate_custom_pdf(selected_df):
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    
    # 這是你原本 V128 的 HTML 結構，已加入括號要求
    html_content = f"""
    <html>
    <head><meta charset='UTF-8'><style>@page {{ size: A4; margin: 15mm; }} body {{ font-family: sans-serif; }}</style></head>
    <body>
        <h1>Corporate Portfolio Report</h1>
        <p>Generated on: {now}</p>
    """
    
    for _, row in selected_df.iterrows():
        card = f"""
        <div style="border: 1px solid #ccc; padding: 10px; margin-bottom: 20px;">
            <h2>{row.get('name_en', '')}</h2>
            <p>{row.get('name_ch', '')}</p>
            <hr>
            <p><strong>Incorp. Date / 成立日期 (YYYY/MM/DD):</strong> {fmt_date(row.get('incorp_date'))}</p>
            <p><strong>ND2A Effective Date (YYYY/MM/DD):</strong> {fmt_date(row.get('nd2a_eff_date'))}</p>
            <p><strong>ND4 Effective Date (YYYY/MM/DD):</strong> {fmt_date(row.get('nd4_eff_date'))}</p>
        </div>"""
        html_content += card
    
    html_content += "</body></html>"
    return HTML(string=html_content).write_pdf()

# --- 4. Navigation ---
st.set_page_config(page_title="ERP Cloud V128", layout="wide")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "⚙️ Group Management", "📤 Data Exchange"])

# --- 5. Dashboard (請確認這是你原本 V128 的 Dashboard 部分) ---
if choice == "📊 Dashboard":
    st.header("📊 Compliance Overview")
    df_raw = pd.read_sql("SELECT * FROM companies", engine)
    st.write(f"📈 Total: **{len(df_raw)}** companies in current view.")
    # (此處請貼上你原本完整的 Dashboard 操作邏輯，確保下載按鈕邏輯無誤)
    if st.button("📥 Export Selected PDF"):
        # 你的下載按鈕邏輯
        st.download_button(label="Download PDF", data=generate_custom_pdf(df_raw), file_name="Report.pdf", mime="application/pdf")

# (其餘所有 Register, Group, Exchange 邏輯保持不變)
