import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta, date
import io
from weasyprint import HTML

# --- 1. Database Connection ---
try:
    if "DB_URL" not in st.secrets:
        st.error("❌ `DB_URL` missing in Streamlit Secrets!")
        st.stop()
    engine = create_engine(st.secrets["DB_URL"])
except Exception as db_err:
    st.error(f"Database Connection Error: {db_err}")
    st.stop()

# --- 2. 工具函式 ---
def to_date(val):
    try:
        if pd.isna(val) or val == "" or str(val).strip() == "" or str(val).lower() in ["none", "nat", "nan"]: return None
        return pd.to_datetime(val).date()
    except: return None

def clean_val(v):
    v = str(v).strip()
    if v.lower() in ["nat", "none", "nan", ""]: return ""
    if v.endswith(" 00:00:00"): return v.replace(" 00:00:00", "")
    return v

def get_anniv(year, month, day):
    try: return date(year, month, day)
    except ValueError: return date(year, month, day - 1)

# --- 3. Navigation ---
st.set_page_config(page_title="ERP Cloud V137", layout="wide")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "⚙️ Group Management", "📤 Data Exchange"])

TEMPLATE_COLS = [
    "client_group", "name_en", "name_ch", "incorp_place", "incorp_place_others", 
    "incorp_date", "ci_no", "is_hk_registered", "hk_incorp_date", "hk_ci_no", "br_no", "br_paid_by",
    "co_type", "reg_addr", "corres_addr", "round_loc", "sign_loc", "seal_loc", 
    "nd2a_eff_date", "nd2a_file_date", "nd2a_download", "nd4_eff_date", "nd4_file_date", "nd4_download", 
    "last_br_resolved_date", "last_ar_filed_date", "dissolution_date"
]

# --- 4. PDF 生成函式 ---
def generate_custom_pdf(selected_df):
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    def fmt_date(val):
        d = to_date(val)
        return d.strftime('%Y/%m/%d') if d else "N/A"
    
    if not selected_df.empty:
        sort_cols = [c for c in ['client_group', 'name_en', 'incorp_place'] if c in selected_df.columns]
        selected_df = selected_df.sort_values(by=sort_cols, na_position='last')

    html_header = """
    <html><head><meta charset="UTF-8"><style>@page { size: A4; margin: 15mm; } body { font-family: sans-serif; }</style></head><body>
    """
    card_template = """
    <div style="border: 1px solid #ddd; padding: 10px; margin-bottom: 20px;">
        <h3>__NAME_EN__</h3>
        <p>Incorp Place: __INCORP_PLACE__</p>
        <p>BR Paid By: __BR_PAID_BY__</p>
        <p>Last BR Date: __L_BR__ | Last AR Date: __L_AR__</p>
    </div>
    """
    final_html = html_header
    for _, row in selected_df.iterrows():
        card = card_template.replace("__NAME_EN__", str(row.get('name_en', ''))).replace("__INCORP_PLACE__", str(row.get('incorp_place', ''))).replace("__BR_PAID_BY__", str(row.get('br_paid_by', ''))).replace("__L_BR__", fmt_date(row.get('last_br_resolved_date'))).replace("__L_AR__", fmt_date(row.get('last_ar_filed_date')))
        final_html += card
    final_html += "</body></html>"
    return HTML(string=final_html).write_pdf()

# --- 5. Dashboard (批量編輯) ---
if choice == "📊 Dashboard":
    st.header("📊 Compliance Dashboard")
    df_raw = pd.read_sql("SELECT * FROM companies", engine)
    
    if not df_raw.empty:
        # 顯示可編輯表格
        st.write("### 📝 Batch Compliance Editor")
        edit_cols = ['name_en', 'br_paid_by', 'last_br_resolved_date', 'last_ar_filed_date']
        df_edit = df_raw[edit_cols].copy()
        
        edited_df = st.data_editor(df_edit, column_config={"br_paid_by": st.column_config.SelectboxColumn("BR Paid By", options=["Firm", "Client"])}, use_container_width=True, key="dash_v137")
        
        if st.button("💾 Save Compliance Updates"):
            for _, row in edited_df.iterrows():
                query = f"UPDATE companies SET br_paid_by='{row['br_paid_by']}', last_br_resolved_date='{row['last_br_resolved_date']}', last_ar_filed_date='{row['last_ar_filed_date']}' WHERE name_en='{row['name_en']}'"
                engine.execute(query)
            st.success("Updated!"); st.rerun()

# --- 6. Company Register (Metric + 雙軌輸入) ---
elif choice == "🏢 Company Register":
    # ... [保留原 V136 邏輯，加返 st.metric] ...
    # 喺 Annual Obligations 區塊：
    if inc_place == "HK" or is_hk_reg:
        base = hk_idate if is_hk_reg else inc_date
        anniv = get_anniv(today_cal.year, base.month, base.day)
        nxt_br = anniv if today_cal <= anniv else get_anniv(today_cal.year + 1, base.month, base.day)
        nxt_ar = (anniv if today_cal <= anniv else get_anniv(today_cal.year + 1, base.month, base.day)) + timedelta(days=42)
        
        col1, col2 = st.columns(2)
        col1.metric("Next BR Deadline", nxt_br.strftime('%Y/%m/%d'))
        col2.metric("Next AR Deadline", nxt_ar.strftime('%Y/%m/%d'))
        
        st.markdown("BR Paid By")
        br_paid_by = st.selectbox("BR_By", ["Firm", "Client"], index=(0 if d.get('br_paid_by')=="Firm" else 1), label_visibility="collapsed")
        # ... [繼續填入日期欄位] ...
