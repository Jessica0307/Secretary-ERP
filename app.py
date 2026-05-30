import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta, date
import calendar
import io
import json
from weasyprint import HTML
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# --- 1. Database Connection ---
try:
    if "DB_URL" not in st.secrets:
        st.error("❌ `DB_URL` missing in Streamlit Secrets! Please configure it in Settings -> Secrets.")
        st.stop()
    
    DB_URL = st.secrets["DB_URL"]
    engine = create_engine(DB_URL)
    with engine.connect() as conn: pass
except Exception as db_err:
    st.error("### 🛑 Database Connection Critical Failure")
    st.info(f"**Error Details:**\n`{str(db_err)}`")
    st.stop()

# --- 2. Utility Functions & Dynamic Years ---
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

def clean_status(val):
    v = str(val)
    for emo in ["🔴 ", "🟡 ", "🟢 ", "✅ ", "⚪ "]: v = v.replace(emo, "")
    return v

def add_one_month(dt):
    if not dt: return None
    month = dt.month + 1
    year = dt.year
    if month > 12:
        month = 1
        year += 1
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)

def get_base_date(row_dict):
    place = str(row_dict.get('incorp_place', ''))
    is_hk_reg = str(row_dict.get('is_hk_registered', 'False')).strip().lower() in ['true', 'yes', 'y', '1']
    if place == 'HK': return to_date(row_dict.get('incorp_date'))
    if is_hk_reg: return to_date(row_dict.get('hk_incorp_date'))
    return None

current_system_year = datetime.now().year
active_years = list(range(2025, current_system_year + 1))

# --- 3. Navigation ---
st.set_page_config(page_title="ERP Cloud V158", layout="wide")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "⚙️ Group Management", "📤 Data Exchange"])

TEMPLATE_COLS = [
    "client_group", "name_en", "name_ch", "incorp_place", "incorp_place_others", 
    "incorp_date", "ci_no", "is_hk_registered", "hk_incorp_date", "hk_ci_no", "br_no", 
    "co_type", "reg_addr", "corres_addr", "round_loc", "sign_loc", "seal_loc", 
    "nd2a_eff_date", "nd2a_file_date", "nd2a_download", "nd4_eff_date", "nd4_file_date", "nd4_download", 
    "nn6_eff_date", "nn6_file_date", "nn6_download",
    "dissolution_date", "remark"
]

# --- 4. Report Generation ---
def generate_custom_pdf(selected_df):
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    def fmt_date(val):
        d = to_date(val)
        return d.strftime('%Y/%m/%d') if d else "N/A"
    
    if not selected_df.empty:
        sort_cols = [c for c in ['client_group', 'name_en', 'incorp_place'] if c in selected_df.columns]
        selected_df = selected_df.sort_values(by=sort_cols, na_position='last')

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
            .info-table tr { border-bottom: 1px solid #f1f2f6; page-break-inside: avoid; }
            .info-table th { text-align: left; width: 45%; color: #7f8c8d; padding: 8px 0; font-weight: normal; font-size: 10.5pt; }
            .info-table td { text-align: justify; padding: 8
