# YGO TYPE — 遊戲王卡圖自動拼接器

這個工具根據使用者輸入的中文文字，透過 [百鴿（YGOCDB）API](https://ygocdb.com/api) 搜尋**卡名含有指定字元**的卡片，從每張卡片的卡名位置裁出一條圖片，按字序自動拼在一起。

## 如何啟動

**推薦方式（搜尋與圖片匯出較可靠）**：安裝 Python 3 後，Windows 雙擊 `start_windows.bat`；macOS / Linux 執行 `bash start_mac_linux.sh`。工具會開啟 `http://127.0.0.1:8765`，不需安裝額外的 Python 套件。需要網路連線下載百鴿卡片資料與圖片；下載內容會快取於 `.cache`。

**免安裝嘗試**：直接開啟 `index.html`。此模式直接連百鴿 API 與圖片 CDN；可能因瀏覽器跨網域限制無法匯出，遇到此問題請改用上述啟動器。

## 功能

- 輸入最多 24 個字元，逐字自動找卡；會盡量避開重複卡片。
- 繁體字優先轉為簡體搜尋，圖中實際出現的字仍受卡圖語言限制。
- 可依序換卡、按「更多」擴大候選搜尋、左右微調裁切、上傳自己的圖作為該字的來源。
- 使用本機伺服器時，「更多」功能還能從百鴿提供的整包公開資料建立本機索引，增加冷門字的覆蓋率（第一次需要下載資料包）。
- 等寬 / 首尾加寬，切片寬度、匯出解析度、接縫顯示。
- 匯出 PNG；無匹配字會標示為缺失，而不會偽裝成已找到。

## 限制

1. 卡名位置是以統一版型**估算**，長卡名、特殊字型、異圖版本可能會偏移；可逐字調整。
2. 資料來源提供的卡圖多為**簡體中文**，因此繁體字可能以對應簡體字呈現，不保證每個字都能找到。
3. 搜尋依賴第三方 API 與卡圖 CDN，服務無法連線、變更 API 或某卡無圖時會無法自動完成。
4. 非官方粉絲工具；卡圖及卡片名稱相關權利歸其原權利人，僅建議私人、非商業使用。
5. Python 服務只監聽本機 `127.0.0.1`，並限制代理路徑與卡片 ID；不需要 API 金鑰。

## 技術

純 HTML/CSS/JavaScript Canvas，輔以可選 Python 標準函式庫本機 HTTP 代理。中文字形繁簡轉換採用 [opencc-js](https://github.com/nk2028/opencc-js) 公開 CDN，CDN 無法連線時採簡易替代表。卡名資料來自百鴿公開 API；卡圖來自百鴿指定的圖片 CDN。

## GitHub Pages 網頁版部署

預計網址：**https://gs040664.github.io/ygo-type-auto-stitch/**

已加入 `.github/workflows/deploy-pages.yml`，以 GitHub Actions 自動部署 `index.html` 靜態網頁。
只會將 `index.html` 發布，不會公開 `server.py`、本機快取或其餘專案檔案。

> **需先由儲存庫管理員啟用 Pages**：
>
> 1. 開啟 [GitHub Pages 設定](https://github.com/gs040664/ygo-type-auto-stitch/settings/pages)。
> 2. 在 **Build and deployment → Source** 選 **GitHub Actions**。
> 3. 如帳號為 GitHub Free，儲存庫必須先在 **Settings → General → Danger Zone → Change repository visibility** 切換為 Public；GitHub Pro 等付費方案可用 Private 儲存庫部署 Pages，但網站本身通常仍會公開。
> 4. 前往 **Actions → Deploy YGO TYPE to GitHub Pages → Run workflow**（如果先前 workflow 因未啟用 Pages 而失敗），確認成功後再瀏覽網站。

GitHub Pages 是純靜態環境，**不會執行本機的 `server.py`**。瀏覽器直接連百鴿 API 與卡圖 CDN；第三方 API 或圖片跨網域（CORS）設定可能造成卡片讀取或 PNG 匯出失敗。需要較完整資料搜尋與圖片代理時，使用前述本機 Python 版。

## 著作權及資料來源

這是非官方粉絲創作工具，與 KONAMI 無關；卡圖著作權歸原權利人。請遵守百鴿 API 及圖片 CDN 的使用規範，避免批量抓取。
