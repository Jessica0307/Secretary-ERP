# --- PDF 生成函式 (【V131】：還原 V128 結構，日期顯示嚴格執行 YYYY/MM/DD) ---
def generate_custom_pdf(selected_df):
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    
    # 嚴格執行 YYYY/MM/DD 格式
    def fmt_date(val):
        d = to_date(val)
        return d.strftime('%Y/%m/%d') if d else "N/A"
    
    html_header = """... (HTML/CSS 與 V128 完全一致) ..."""
    html_header = html_header.replace("__NOW__", now)

    # 【PDF 卡片範本】：嚴格跟足你要求，日期後加 (YYYY/MM/DD)
    card_template = """
    <div class="company-container">
        <table class="main-table">
            <thead><tr><td><div class="header-content"><div class="name-en">__NAME_EN__</div><div class="name-ch">__NAME_CH__</div></div></td></tr></thead>
            <tbody><tr><td><div class="company-card">
                <div class="section-group"><div class="section-bar">Registration Details / 註冊詳情</div><table class="info-table">
                    <tr><th>Client Group / 客戶組別</th><td>__CLIENT_GROUP__</td></tr>
                    <tr><th>Incorp. Date / 成立日期 (YYYY/MM/DD)</th><td>__INCORP_DATE__</td></tr>
                    <tr><th>Incorp. Place / 成立地點</th><td>__INCORP_PLACE__</td></tr>
                    <tr><th>CI No. / 公司註冊編號</th><td>__CI_NO__</td></tr>
                    <tr><th>BR No. / 商業登記編號</th><td>__BR_NO__</td></tr>
                    <tr><th>Company Type / 公司類別</th><td>__CO_TYPE__</td></tr>
                </table></div>
                <div class="section-group"><div class="section-bar">Addresses / 地址</div><table class="info-table">
                    <tr><th>Registered Address / 註冊地址</th><td>__REG_ADDR__</td></tr>
                    <tr><th>Correspondence Address / 通訊地址</th><td>__CORRES_ADDR__</td></tr>
                </table></div>
                <div class="section-group"><div class="section-bar">Items Storage / 物品存放位置</div><table class="info-table">
                    <tr><th>Round Stamp / 小圓章</th><td>__ROUND_LOC__</td></tr>
                    <tr><th>Signature Chop / 簽名章</th><td>__SIGN_LOC__</td></tr>
                    <tr><th>Common Seal / 鋼印</th><td>__SEAL_LOC__</td></tr>
                </table></div>
                <div class="section-group"><div class="section-bar">Compliance Filings / 法定申報</div><table class="info-table">
                    <tr><th>ND2A Effective Date (YYYY/MM/DD)</th><td>__ND2A_EFF__</td></tr>
                    <tr><th>ND4 Effective Date (YYYY/MM/DD)</th><td>__ND4_EFF__</td></tr>
                </table></div>
            </div></td></tr></tbody>
        </table>
    </div>
    """

    final_html = html_header
    for _, row in selected_df.iterrows():
        card = card_template
        # ... (其餘 replace 保持 V128 一致)
        card = card.replace("__INCORP_DATE__", fmt_date(row.get('incorp_date')))
        card = card.replace("__ND2A_EFF__", fmt_date(row.get('nd2a_eff_date')))
        card = card.replace("__ND4_EFF__", fmt_date(row.get('nd4_eff_date')))
        # ... (其餘 replace)
        final_html += card
    return HTML(string=final_html).write_pdf()
