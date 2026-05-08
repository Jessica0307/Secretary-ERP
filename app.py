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

# --- 2. Navigation ---
st.set_page_config(page_title="ERP Cloud V34", layout="wide")
choice = st.sidebar.radio("Navigation", ["📊 Dashboard", "🏢 Company Register", "⚙️ Group Management", "📤 Data Exchange"])

# 定義系統必填欄位 (用於 Upload 檢查)
REQUIRED_COLS = ["client_group", "name_en", "name_ch", "incorp_date", "incorp_place", "ci_no", "br_no", "co_type", "reg_addr", "corres_addr"]

# --- 3. Data Exchange (新功能：匯入/匯出) ---
if choice == "📤 Data Exchange":
    st.header("📤 Data Exchange & Backup")
    
    # --- Tab 1: Export ---
    st.subheader("1. Download & Backup")
    col_ex1, col_ex2 = st.columns(2)
    
    # 生成空白範本
    template_cols = ["client_group", "name_en", "name_ch", "incorp_date", "incorp_place", "incorp_place_others", "ci_no", "br_no", "co_type", "reg_addr", "corres_addr", "round_loc", "sign_loc", "seal_loc", "nd2a_eff_date", "nd2a_file_date", "nd2a_download", "nd4_eff_date", "nd4_file_date", "nd4_download", "dissolution_date"]
    tmp_df = pd.DataFrame(columns=template_cols)
    
    buffer_tmp = io.BytesIO()
    with pd.ExcelWriter(buffer_tmp, engine='xlsxwriter') as writer:
        tmp_df.to_excel(writer, index=False, sheet_name='Sheet1')
    
    col_ex1.download_button(
        label="📥 Download Blank Template",
        data=buffer_tmp.getvalue(),
        file_name="Company_Import_Template.xlsx",
        mime="application/vnd.ms-excel"
    )

    # 匯出所有現有資料
    df_all = pd.read_sql("SELECT * FROM companies", engine)
    buffer_all = io.BytesIO()
    with pd.ExcelWriter(buffer_all, engine='xlsxwriter') as writer:
        df_all.to_excel(writer, index=False, sheet_name='All_Companies')
    
    col_ex2.download_button(
        label="📦 Export All Data (Backup)",
        data=buffer_all.getvalue(),
        file_name=f"Company_Full_Backup_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.ms-excel",
        help="下載目前資料庫所有資料，可用作備份或批量修改後重新上傳"
    )

    st.write("---")
    
    # --- Tab 2: Import ---
    st.subheader("2. Upload & Import Data")
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
    
    if uploaded_file:
        try:
            up_df = pd.read_excel(uploaded_file)
            st.write("Preview (First 5 rows):")
            st.dataframe(up_df.head())
            
            if st.button("🚀 Confirm & Upload to Cloud"):
                # 檢查欄位是否齊全
                missing_headers = [c for c in template_cols if c not in up_df.columns]
                if missing_headers:
                    st.error(f"❌ 檔案格式錯誤，缺漏欄位：{', '.join(missing_headers)}")
                else:
                    # 逐行檢查必填項目
                    error_logs = []
                    for index, row in up_df.iterrows():
                        missing_data = [c for c in REQUIRED_COLS if pd.isna(row[c]) or str(row[c]).strip() == ""]
                        if missing_data:
                            error_logs.append(f"Row {index+2}: 缺少 {', '.join(missing_data)}")
                    
                    if error_logs:
                        st.error("❌ 上傳失敗！請修正以下錯誤後再試：")
                        for log in error_logs[:10]: # 只顯示前10條
                            st.write(log)
                    else:
                        # 成功通過檢查，上傳
                        # 注意：這裡使用 append。如果 user 是想「成個 list upload 返入去」當備份還原，
                        # 建議先清空再上傳，或者 user 手動 delete 所有野再 upload。
                        with st.spinner("Uploading..."):
                            up_df.to_sql('companies', engine, if_exists='append', index=False)
                            st.success(f"✅ 成功匯入 {len(up_df)} 條紀錄！")
                            st.balloons()
        except Exception as e:
            st.error(f"Error reading file: {e}")

# --- 4. Company Register (維持第23版邏輯) ---
elif choice == "🏢 Company Register":
    # [這裡保留你第 23 版的所有代碼，包含紅框提醒、預載邏輯等]
    st.info("此處代碼完全鎖定為第 23 版邏輯。")
    # (為了節省篇幅，此處省略重複的 Register 代碼，實際部署時請將第 23 版代碼放回這裡)

# --- 5. Dashboard & Group Mgmt ---
# [其餘部分保持不變]
