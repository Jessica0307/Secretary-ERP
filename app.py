# --- 4. Company Register (維持 V32/38 鎖定邏輯) ---
elif choice == "🏢 Company Register":
    st.header("🏢 Company Records Management")
    mode = st.radio("Mode", ["🆕 Add New", "✏️ Edit Existing", "📋 Copy Existing"], horizontal=True)
    df_all = pd.read_sql("SELECT * FROM companies", engine)
    groups = pd.read_sql("SELECT group_name FROM client_groups", engine)['group_name'].tolist()
    d = {'cg': "", 'en': "", 'ch': "", 'idate': None, 'place': "", 'p_oth': "", 'ci': "", 'br': "", 'type': "", 'ra': "", 'ca': "", 'rl': "", 'sl': "", 'cl': "", 'n2e': None, 'n2f': None, 'n2d': False, 'n4e': None, 'n4f': None, 'n4d': False, 'dis': None}
    target_name = None

    if mode in ["✏️ Edit Existing", "📋 Copy Existing"] and not df_all.empty:
        comp_list = [""] + df_all['name_en'].tolist()
        target_name = st.selectbox("Select Company", comp_list)
        if target_name != "":
            row = df_all[df_all['name_en'] == target_name].iloc[0]
            d = {'cg': row.get('client_group', ""), 'en': row.get('name_en', ""), 'ch': row.get('name_ch', ""), 'idate': row.get('incorp_date'), 'place': row.get('incorp_place', ""), 'p_oth': row.get('incorp_place_others', ""), 'ci': row.get('ci_no', ""), 'br': row.get('br_no', ""), 'type': row.get('co_type', ""), 'ra': row.get('reg_addr', ""), 'ca': row.get('corres_addr', ""), 'rl': row.get('round_loc', ""), 'sl': row.get('sign_loc', ""), 'cl': row.get('seal_loc', ""), 'n2e': row.get('nd2a_eff_date'), 'n2f': row.get('nd2a_file_date'), 'n2d': str(row.get('nd2a_download', "")) == 'True', 'n4e': row.get('nd4_eff_date'), 'n4f': row.get('nd4_file_date'), 'n4d': str(row.get('nd4_download', "")) == 'True', 'dis': row.get('dissolution_date')}
            if mode == "📋 Copy Existing": d['en'], d['ch'] = "", ""

    def red_label(text, value):
        return f":red[⚠️ {text} (Required!)]" if not value or str(value).strip() == "" or value is None else text

    # 表單介面
    client_group = st.selectbox(red_label("Select Client Group", d['cg']), [""] + groups, index=(groups.index(d['cg'])+1 if d['cg'] in groups else 0))
    c1, c2 = st.columns(2); name_en = c1.text_input(red_label("English Name", d['en']), value=d['en']); name_ch = c2.text_input(red_label("Chinese Name", d['ch']), value=d['ch'])
    c3, c4 = st.columns(2); inc_date = c3.date_input(red_label("Incorp Date", d['idate']), value=d['idate'])
    # ... (此處繼續 V32 完整表單代碼)

# --- 6. Group Management & Data Exchange ---
# ... (此處繼續 V32/35 的 Group 刪除驗證與 Excel 上傳邏輯)
