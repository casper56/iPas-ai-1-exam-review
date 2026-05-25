# AI 人工智慧應用與程式開發歷屆甄試複習系統 — 軟體規格說明書 (Software Specifications)

本規格說明書旨在詳細記錄 **「AI 人工智慧應用與程式開發歷屆甄試複習系統」** 的軟體架構、UI/UX 佈局設計、交互功能邏輯、資料持久化以及 CI/CD 自動化部署規範，作為本專案後續維護與協作的最高技術指導準則。

---

## 🛠️ 專案基本架構 (Core Architecture)
- **架構模式**：單一檔案自包含 (Self-contained Single-file HTML)。
- **技術棧**：原生 HTML5 + 原生 CSS3 (CSS Variables, Grid, Flexbox) + 原生 JavaScript (ES6+)。
- **外部依賴**：**無 (Zero Dependencies)**。禁止引入 TailwindCSS (除非使用者特別指定並確認版本) 或任何前端 JS 框架，以保障極速離線運作能力。

---

## 📂 檔案目錄結構與資料庫規範 (File Directory & Database)

### 1. 目錄結構
```text
AI_TEST/
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions 靜態網頁自動部署工作流
├── backups/                    # 原始程式碼與規格文件之備份目錄 (.bak)
│   ├── index.html.bak
│   └── Soft_spec.md.bak
├── scratch/                    # 開發輔助與分析之 temporary 腳本目錄
│   ├── inspect_questions.js
│   └── analyze_similarity.js
├── index.html                  # 系統核心網頁主程式（單一自包含 HTML 檔案）
├── README.md                   # 專案技術開發與協作規範說明
├── Soft_spec.md                # 軟體規格說明書（本檔案）
├── analysis_results.md         # 歷屆考題相似度深度分析報告
└── *.pdf                       # 原始 113、114、115 年度甄試考古題 PDF 檔案
```

### 2. 題目資料庫規範
- 系統完整收錄 **113 年、114 年、115 年** 共三個年度的考題。
- 每個年度精準劃分為：
  - **「智力測驗 (第 1 - 25 題)」**
  - **「專業試題 (第 26 - 50 題)」**
- **題目總數**：150 題。在任何修改中，必須維護題目完整度，嚴禁產生重複題目或 ID 遺漏。

---

## 📐 UI/UX 佈局與排版規範 (Layout & Styling)

### 1. 核心容器尺寸公式 (V3.4 佈局標準)
為了確保網頁在各種解析度下（包括縮放與大螢幕）均能保持完美的左右留白與對齊，**題目主要容器必須嚴格採用以下樣式，嚴禁修改**：
```css
#main-container {
    width: calc(100% - 60px);
    margin: 20px auto;
    max-width: none;
}
```
* **設計意圖**：移除傳統的 `1200px` 最大寬度限制，以實現全屏外擴。確保左右精確留白各 `30px`，使導覽拉把、按鈕與題目卡在縮放時保持 `5px` 固定間隙並同步位移。

### 2. 題卡設計
- 題卡元件包含：易錯標記鈕（星形/旗標）、題號標籤、年份標籤、分類標籤、題目文字、程式碼區塊（如有）、選項網格、重新作答鈕、正確答案條以及詳細解析欄。
- **選項排版**：題目下方的單選/多選選項，必須採用 **「兩欄式格線 (2-column grid layout)」** 呈現，以確保視覺整齊美觀。

### 3. 「去粉紅」程式碼樣式規範 (Anti-Pink Syntax Styling - V3.1 標準)
為了保障專業工程審美，系統內所有程式碼區塊（如 C++、C# 等程式碼範例）必須嚴格執行「去粉紅」規則：
- **禁止**使用粉紅色、亮紅色作為程式碼字體色或背景底色。
- **統一採用深炭色設計**：
  ```css
  pre, code {
      background-color: #1e293b !important; /* 深灰色背景 */
      color: #e2e8f0 !important;            /* 亮灰色文字 */
  }
  ```

---

## 🔒 答案隱藏與互動機制 (Answer Masking & Interaction)

### 1. 正確答案條規範 (V3.1 標準)
為復刻 PDF 1:1 專業學術感並防止使用者在練習時被答案劇透，答案條必須遵循：
- **樣式要求**：**「純白背景、綠色文字 (#198754)、左側 5px 綠實線」**。
  ```css
  .answer-bar {
      background-color: #ffffff !important;
      color: #198754 !important;
      border-left: 5px solid #198754 !important;
      user-select: none;
  }
  ```
- **視覺隱藏邏輯**：預設情況下，正確答案文字字體顏色與背景同色（視覺隱藏）。
- **顯現機制**：
  - 當滑鼠指針移入該題目區塊時（Hover）。
  - 當使用者選取該段文字（Selection）。
  - **嚴禁**私自為答案條加入彩色底色或將白色背景替換，必須維持專業純白背景。

---

## 🔄 答題狀態與重新作答機制 (Answer Selection & Reset - V3.5 標準)

### 1. 選項點擊事件與 ID 衝突修復
由於「平常練習區」、「年度模擬考區」與「總模擬考區」會同時存在於同一個 DOM 樹中，相同的題目 ID 會重複出現在不同的 DOM 區塊中。
- **禁止**使用 `document.getElementById` 進行選項的點擊高亮或狀態處理（這會導致 ID 衝突，使模擬考區的選項無法被點選）。
- **必須採用相對 DOM 樹尋找**：透過點擊事件中的 `this` 元素，向上尋找最近的題卡容器（如 `.closest('.options-grid')`），再進行同題卡內選項的高亮與互斥設定。

### 2. 重新作答機制
- 練習模式中，每個題卡下方均設有 **「🔄 重新作答」** 按鈕。
- 點擊後，必須：
  1. 清除該題的所有已選高亮樣式（移除選項上的 `selected` 等 class）。
  2. 隱藏正確答案條與詳細步驟解析。
  3. 解除題卡的作答鎖定狀態，允許使用者重新點選。

---

## 📊 左側懸浮學習進度導覽側欄 (Collapsible Side Drawer - V3.6 標準)

### 1. 毛玻璃懸浮面板 (Glassmorphic Drawer)
- 採用 `fixed` 定位固定於螢幕左側。
- 預設收合於左側邊緣，點擊「📊」圖示的滑動拉把，可平滑滑出面板。
- 面板需支援亮色、深色與護眼（Sepia Cream）三種主題的無縫色彩適應。
- **限制**：側欄滑出時，必須為懸浮覆蓋層（Overlay），**絕對不能**推擠或破壞主內容區的 `width: calc(100% - 60px)` 核心佈局。

### 2. 四色進度追蹤網格 (4-Color Status Matrix)
側邊欄將根據目前選取的年份與分類，動態渲染對應題數（25 或 50 顆）的圓形/方形題號狀態按鈕。狀態顏色定義如下：
1. **🟩 淺綠色 (Correct)**：初次作答即答對。
2. **🟥 紅色 (Wrong)**：初次作答錯誤。
3. **🟧 亮橘色 (Corrected)**：*核心特色*！先前曾答錯過（已存入錯題紀錄），但經過「重新作答」重試後成功答對。此狀態可提醒使用者該題為「曾錯但已改正」的易錯題，考前需特別注意。
4. **⚪ 灰色 (Unanswered)**：尚未進行作答。

### 3. 進度儀表板 (Progress Stats Dashboard)
側欄頂端需實時更新答題數據，包含：
- 作答完成度（%）
- 答對題數（淺綠 + 亮橘）
- 曾錯/已改正題數
- 目前已答題數

### 4. 平滑跳轉與焦點引導 (Smooth Scroll & Flash Focus)
- 點選側邊欄中任何題號圓點，頁面需以平滑動畫（`scrollIntoView({ behavior: 'smooth' })`）捲動至目標題卡。
- 目標題卡在捲動完成後，其外框需觸發一個**短暫的藍色外框閃爍動畫**（持續 1~1.5 秒），用以瞬間吸引使用者視線定位。

---

## 💾 資料持久化規範 (State Persistence)
所有狀態必須完整儲存在瀏覽器的 `localStorage` 中，確保離線與重整網頁不遺失數據：
1. `flagged_questions`：儲存已標記為易錯題的題目 ID 陣列。
2. `practice_history`：儲存所有題目作答歷程的物件（包含每題的初次作答狀態、是否曾答錯、最終答對狀態等，以支援四色進度顯示）。
3. `review_system_theme`：儲存使用者的主題設定（Light / Dark / Sepia）。

---

## 🚀 CI/CD 自動部署規範 (GitHub Actions - V3.7 標準)

本專案採用 GitHub Actions 進行 GitHub Pages 靜態網站自動化部署。
- **工作流路徑**：`.github/workflows/deploy.yml`
- **觸發時機**：當有變更 `push` 推送到 `main` 或 `master` 分支時自動執行。
- **部署模式**：採用靜態資產上傳（Deploy static assets），使用 `actions/upload-pages-artifact@v3` 與 `actions/deploy-pages@v4`。
- **GitHub 專案設定要求**：倉庫的 `Settings -> Pages -> Build and deployment -> Source` 必須設定為 **`GitHub Actions`**。