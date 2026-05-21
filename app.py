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
    with engine.connect() as conn: pass
except Exception as db_err:
    st.error(f"連線錯誤: {db_err}"); st.stop()

# --- 2. 工具函式 ---
def to_date(val):
    try:
        if pd.isna(val) or val == "" or str(val).strip() == "" or str(val).lower() in ["none", "nat"]:
            return None
        return pd.to_datetime(val).date()
    except: return None

def fmt_date(val):
    d = to_date(val)
    return d.strftime('%Y/%m/%d') if d else "N/A"

# --- 3. Navigation ---
st.set_page_config(page_title="ERP Cloud V128", layout="wide")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "⚙️ Group Management", "📤 Data Exchange"])

# --- 4. PDF 生成函式 (已修復標籤，結構完全還原 V128) ---
def generate_custom_pdf(selected_df):
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    html_header = """<html><head><meta charset="UTF-8"><style>
        @page { size: A4; margin: 15mm; }
        body { font-family: sans-serif; color: #2c3e50; }
        .section-bar { background: #f1f4f6; padding: 5px; font-weight: bold; border-left: 5px solid #3498db; margin: 10px 0; }
        .info-table { width: 100%; border-collapse: collapse; }
        th { text-align: left; width: 45%; color: #7f8c8d; padding: 5px; }
        td { padding: 5px; font-weight: bold; }
    </style></head><body>"""
    
    final_html = html_header
    for _, row in selected_df.iterrows():
        # 這裏維持 V128 原狀，僅修改了 Incorp. Date 標籤
        card = f"""
        <div class="company-container">
            <h2>{row.get('name_en', '')}</h2>
            <p>{row.get('name_ch', '')}</p>
            <div class="section-bar">Registration Details / 註冊詳情</div>
            <table class="info-table">
                <tr><th>Client Group</th><td>{row.get('client_group', '')}</td></tr>
                <tr><th>Incorp. Date / 成立日期 (YYYY/MM/DD)</th><td>{fmt_date(row.get('incorp_date'))}</td></tr>
                <tr><th>Incorp. Place</th><td>{row.get('incorp_place', '')}</td></tr>
                <tr><th>CI No.</th><td>{row.get('ci_no', '')}</td></tr>
                <tr><th>BR No.</th><td>{row.get('br_no', '')}</td></tr>
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

# --- 5. Dashboard ---
if choice == "📊 Dashboard":
    st.header("📊 Compliance Overview")
    df_raw = pd.read_sql("SELECT * FROM companies", engine)
    groups = pd.read_sql("SELECT group_name FROM client_groups", engine)['group_name'].tolist()
    if not df_raw.empty:
        for col in ["incorp_date", "nd2a_eff_date", "nd4_eff_date", "nd2a_file_date", "nd4_file_date", "dissolution_date"]:
            if col in df_raw.columns: df_raw[col] = pd.to_datetime(df_raw[col], errors='coerce').dt.date
        t1, t2, t3, t4 = st.columns([3, 2, 2, 5])
        filter_g = t1.selectbox("🔍 Filter Group", ["All Groups"] + groups)
        if t2.button("🔄 Refresh"): st.rerun()
        df_filtered = df_raw if filter_g == "All Groups" else df_raw[df_raw['client_group'] == filter_g]
        if 'sel_v128' not in st.session_state: st.session_state.sel_v128 = False
        if t3.button("✅ Select All"): st.session_state.sel_v128 = True; st.rerun()
        if t4.button("🧹 Clear All"): st.session_state.sel_v128 = False; st.rerun()
        df_display = df_filtered.copy()
        df_display.insert(0, "Select", st.session_state.sel_v128)
        edit_df = st.data_editor(df_display, hide_index=True, use_container_width=True, key="dash_v128")
        selected = edit_df[edit_df["Select"] == True]
        if len(selected) > 0:
            if st.button("📥 Export Selected PDF"):
                st.download_button("Download PDF", data=generate_custom_pdf(selected), file_name="Report.pdf", mime="application/pdf")
            if st.button("🧨 BATCH DELETE"): pass # (維持你原本的邏輯)

# --- (其餘邏輯請直接貼回你原本的代碼) ---
