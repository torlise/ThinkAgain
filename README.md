# 逆思維 Think Again｜讀書會閱讀器

這個 repo 將《逆思維 Think Again》第 1～7 章重點整理轉成可用 GitHub Pages 閱讀的靜態網站。

預期網址：

https://torlsie.github.io/ThinkAgain/

## 檔案

- `index.html`：主要閱讀器
- `styles.css`：閱讀版型與響應式樣式
- `app.js`：閱讀進度、章節高亮、返回頁首
- `assets/`：從 Word 轉出的圖片資產與 manifest
- `tools/build_site.py`：從 Word 重新產生網站內容的轉換器
- `tools/validate_site.py`：檢查 HTML、圖片引用與基本結構

## 來源

來源文件：`逆思維_第1至7章重點整理_更豐富版.docx`

## 更新流程

1. 更新來源 Word 文件。
2. 執行 `python tools/build_site.py` 重新產生網站。
3. 執行 `python tools/validate_site.py` 檢查輸出。
4. 推送到 `main` 後，在 GitHub Pages 設定中選擇 `main` / root 發佈。
