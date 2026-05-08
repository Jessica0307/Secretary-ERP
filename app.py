# --- 3. Data Exchange (修正日期格式報錯版) ---
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
            
            if st.button("🚀 Confirm Upload to Cloud"):
                # --- [新增：日期欄位深度清洗邏輯] ---
                # 定義所有屬於「日期」嘅欄位
                date_cols = ["incorp_date", "nd2a_eff_date", "nd2a_file_date", "nd4_eff_date", "nd4_file_date", "dissolution_date"]
                
                # 確保這些日期欄位中，任何「空白字串」或「n/a」都被轉為真正的 None (NULL)
                for col in date_cols:
                    if col in up_df.columns:
                        up_df[col] = up_df[col].apply(lambda x: None if str(x).strip().lower() in ["", "nan", "n/a", "none", "nil"] else x)
                        # 嘗試轉為 pd.to_datetime，不成功的轉為 NaT (等同於 None)
                        up_df[col] = pd.to_datetime(up_df[col], errors='coerce')

                # --- [原本的必填檢查邏輯] ---
                error_logs = []
                for i, row in up_df.iterrows():
                    missing = []
                    for c in REQUIRED_COLS:
                        # 檢查必填項，注意日期現在可能是 NaT
                        val = row[c]
                        if pd.isna(val) or str(val).strip() == "":
                            missing.append(c)
                    if missing:
                        error_logs.append(f"Row {i+2}: 缺少 {', '.join(missing)}")
                
                if error_logs:
                    st.error("❌ 上傳攔截：有必填格仔未填")
                    for log in error_logs[:10]: st.write(log)
                else:
                    with st.spinner("Saving to database..."):
                        # 最終檢查：有些欄位如果資料庫沒有（例如你 Error 報出的 status），要處理掉
                        # 或者確保 DataFrame 的欄位跟資料庫 100% 對應
                        up_df.to_sql('companies', engine, if_exists='append', index=False)
                        st.success("✅ 匯入成功！")
                        st.rerun()
        except Exception as e:
            st.error(f"Upload Error: {e}")
