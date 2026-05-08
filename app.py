import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import io

# --- 1. Database Connection ---
try:
    DB_URL = st.secrets["DB_URL"]
    engine = create_engine(DB_URL)
except:
    st.error("❌ Please check DB_URL in Secrets")
    st.stop()

# --- 2. Navigation (LOCK V23 Layout) ---
st.set_page_config(page_title="ERP Cloud V34", layout="wide")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "⚙️ Group Management", "📤 Data Exchange"])

# 定義必填欄位 (用於上傳驗證)
REQUIRED_COLS = ["client_group", "name_en", "name_ch", "incorp_date", "incorp_place", "ci_no", "br_no", "co_type", "reg_addr", "corres_addr", "round_loc", "sign_loc", "seal_loc"]

# --- 3. Data Exchange (解決日期格式與 N/A 豁免) ---
if choice == "📤 Data Exchange":
    st.header("📤 Data Exchange & Backup")
    
    st.subheader("1. Download & Backup")
    col_ex1, col_ex2 = st.columns(2)
    
    template_cols = ["client_group", "name_en", "name_ch", "incorp_date", "incorp_place", "incorp_place_others", "ci_no", "br_no", "co_type", "reg_addr", "corres_addr", "round_loc", "sign_loc", "seal_loc", "nd2a_eff_date", "nd2a_file_date", "nd2a_download", "nd4_eff_date", "nd4_file_date", "nd4_download", "dissolution_date"]
    
    # 下載空白範本
    tmp_df = pd.DataFrame(columns=template_cols)
    buffer_tmp = io.BytesIO()
    with pd.ExcelWriter(buffer_tmp, engine='xlsxwriter') as writer:
        tmp_df.to_excel(writer, index=False)
    col_ex1.download_button(label="📥 Download Blank Template", data=buffer_tmp.getvalue(), file_name="Company_Record_Template.xlsx", mime="application/vnd.ms-excel")

    # 備份 (Export)
    df_all_export = pd.read_sql("SELECT * FROM companies", engine)
    buffer_all = io.BytesIO()
    with pd.ExcelWriter(buffer_all, engine='xlsxwriter') as writer:
        df_all_export.to_excel(writer, index=False)
    col_ex2.download_button(label="📦 Export All Data (Backup)", data=buffer_all.getvalue(), file_name=f"Full_Backup_{datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.ms-excel")

    st.write("---")
    st.subheader("2. Upload & Bulk Import")
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
    
    if uploaded_file:
        try:
            # 讀取 Excel
            up_df = pd.read_excel(uploaded_file, engine='openpyxl', keep_default_na=False)
            st.write("Preview (First 5 rows):")
            st.dataframe(up_df.head())
            
            if st.button("🚀 Confirm Upload to Cloud"):
                # A. 深度清洗日期欄位，防止 InvalidDatetimeFormat 錯誤
                date_cols = ["incorp_date", "nd2a_eff_date", "nd2a_file_date", "nd4_eff_date", "nd4_file_date", "dissolution_date"]
                for col in date_cols:
                    if col in up_df.columns:
                        # 將空白字串或 n/a 字眼轉為真正的 NaT (NULL)
                        up_df[col] = up_df[col].apply(lambda x: None if str(x).strip().lower() in ["", "nan", "n/a", "none", "nil"] else x)
                        up_df[col] = pd.to_datetime(up_df[col], errors='coerce')

                # B. 必填檢查
                error_logs = []
                for i, row in up_df.iterrows():
                    missing = []
                    for c in REQUIRED_COLS:
                        val = row[c]
                        # 檢查：如果是空值 (NaN/NaT) 或空白字串，就報錯
                        if pd.isna(val) or str(val).strip() == "":
                            missing.append(c)
                    if missing:
                        error_logs.append(f"Row {i+2}: 缺少 {', '.join(missing)}")
                
                if error_logs:
                    st.error("❌ 上傳攔截：有必填格仔未填 (或格式錯誤)")
                    for log in error_logs[:10]: st.write(log)
                else:
                    with st.spinner("Saving to database..."):
                        # 確保 DataFrame 只有資料庫有的欄位
                        # 如果 Excel 有多了 status 欄位，這裡會過濾掉
                        cols_in_db = pd.read_sql("SELECT * FROM companies LIMIT 0", engine).columns.tolist()
                        final_up_df = up_df[[c for c in up_df.columns if c in cols_in_db]]
                        
                        final_up_df.to_sql('companies', engine, if_exists='append', index=False)
                        st.success("✅ 匯入成功！")
                        st.rerun()
        except Exception as e:
            st.error(f"Upload Error: {e}")

# --- 4. Company Register (100% 鎖定第 23 版邏輯) ---
elif choice == "🏢 Company Register":
    st.header("🏢 Company Records Management")
    mode = st.radio("Mode", ["🆕 Add New", "✏️ Edit Existing", "📋 Copy Existing"], horizontal=True)
    
    df_all = pd.read_sql("SELECT * FROM companies", engine)
    groups = pd.read_sql("SELECT group_name FROM client_groups", engine)['group_name'].tolist()
    
    d = {'cg': "", 'en': "", 'ch': "", 'idate': None, '
