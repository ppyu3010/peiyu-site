# peiyu 個人網站 — 給下一個接手的 Claude 看

這是 peiyu（用戶，email: peggy.shuai@gmail.com，GitHub 帳號 **ppyu3010**）的個人網站專案。
**新對話開始時，先讀這份檔案，再讀 `assets/CHECKLIST.md`（素材規格與填寫方式），不用再重新問一次「這是什麼網站」。**

## 現況

- **正式網址**：https://ppyu3010.github.io/peiyu-site/ （GitHub Pages，repo 是 https://github.com/ppyu3010/peiyu-site ，`main` 分支根目錄）
- 純靜態網站：一個 `index.html`（所有 CSS/JS 都寫在裡面，沒有拆檔、沒有建置工具、沒有 npm）+ `assets/` 圖片素材 + `content/content.js`（由 Python 腳本掃描 `assets/` 自動產生，**不要手動改這個檔案**）。
- 本機開發：直接用 `python3 -m http.server 8768` 在專案根目錄起一個伺服器，瀏覽器開 `http://localhost:8768/index.html` 就能測試（相對路徑，不能直接用 `file://` 打開，會有 CORS 問題）。
- 每次改完 **一定要用瀏覽器工具實際點過一輪再回報完成**，尤其動畫/過場類的東西常常需要等待才能看到最終狀態（螢幕截圖如果剛好是淡入淡出中間會看起來像壞掉，多等 1-2 秒重新截圖再判斷）。

## 部署流程

```bash
cd ~/Desktop/peiyu-site
git add -A
git commit -m "說明這次改了什麼"
git push
```
推上去後，GitHub Pages 大約 1 分鐘內自動更新，不用其他設定。

**`gh` (GitHub CLI) 不是系統安裝的**，是我在某次對話裡直接下載到 scratchpad 暫存資料夾裡用的，那個資料夾每個對話 session 結束就會消失。如果下一個對話需要用到 `gh`（例如要用 API 做點什麼），检查 `which gh`；如果沒有，需要重新下載（官方 release，或請使用者自己 `brew install gh`）。**但一般的 `git push` 不需要 `gh`**——本機的 git 已經透過 `gh auth setup-git` 設定好認證了，用 `git push` 應該可以直接用，除非使用者的系統 keychain 憑證被清掉。如果 push 失敗顯示要帳密，才需要重新走一次 `gh auth login --web` 的裝置授權流程（帶使用者去瀏覽器輸入一次性代碼，不要自己代替使用者輸入帳號密碼）。

## 網站架構（index.html 內部）

這是一個「電梯／門禁卡」概念改版後的「牆面」個人網站，流程：**載入畫面（刷門禁卡動畫）→ 平面牆（四個手繪圖樣，點了展開）→ 各區域內容**。

### 響應式的核心機制：「u 單位」

`layoutStage()`（約在第 356 行）把整個構圖鎖定在一個固定比例的「舞台」（`REF = {w:1676, h:1054}`，早期依使用者的示意圖訂出來的比例），無論螢幕多寬，舞台永遠等比縮放置中。`--u` 這個 CSS 變數 = 舞台寬度的 1%，幾乎所有位置、大小都是 `calc(var(--u) * N)` 這樣寫，N 是從使用者的示意圖裡量出來的百分比數字（用截圖 + canvas 取樣像素算出來的，過程都在對話紀錄裡）。

**手機版**（`body.narrow`，寬度 < 560px 觸發）是完全不同的排版邏輯：首頁牆面變成直式、由上往下滑的一排圖樣（`display:flex; flex-direction:column`），展開頁的內容從「絕對定位」改成「一般文件流」由上往下排。手機版相關的 CSS 都用 `body.narrow ...` 前綴，JS 裡常有 `document.body.classList.contains("narrow")` 的判斷分岔。

**踩過的坑（別重蹈覆轍）**：
1. **CSS 優先權**：例如 `.motif img { display:block; }`（class+標籤）的優先權會贏過單獨的 `.m-title-img { display:none; }`（單一 class），造成「規則明明寫著隱藏、卻沒生效」。改 CSS 規則時想清楚特異度，不確定就加更具體的選擇器（如 `.motif .m-title-img`），不要輕易用 `!important` 蓋過去（能不用就不用，但對抗「行內 style 的 JS 設定」時 `!important` 是必要手段，這網站裡到處都是 `body.narrow .xxx { ... !important; }` 這種寫法，是故意的，因為同一個元素平常用 JS 設 inline style 定位）。
2. **CSS margin 塌陷（collapsing margin）**：一個 `position:relative` 但沒有 padding/border 的容器，裡面第一個「一般流」子元素的 `margin-top` 會直接變成外層容器整個往下位移，而不是在容器內部產生間距，導致絕對定位的標題和底下的內文疊在一起。手機版排版遇到「間距沒生效／東西疊在一起」，先懷疑這個，解法是改用容器的 `padding-top` 而不是子元素的 `margin-top`。
3. **`position:absolute` 在可捲動的手機頁面上會被捲走**：手機版首頁很長、要捲動，任何「應該固定顯示在畫面上」的裝飾（例如彈跳的草皮圓）在手機版要用 `position:fixed`，不能用 `position:absolute`（那個是跟著文件走，一捲動就跑出視窗外）。
4. **CSS 裡同一個選擇器的規則，宣告順序 (source order) 比 `@media` 條件更早/更晚會影響誰贏**：同特異度時，寫在檔案「後面」的規則會贏，跟有沒有 `@media` 包住無關。改響應式規則時，確定新規則寫在「會被覆蓋的舊規則」後面。
5. **每個作品卡片的說明文字寬度**：曾經想用 CSS `width:100%` 讓文字寬度跟著圖片走，但在「auto-size 的 flex/inline-block 容器」裡，子元素的百分比寬度會被當成 `auto`（CSS 規範如此），文字反而會撐開容器。現在的解法是 JS 量出圖片實際渲染寬度、用 inline style 把卡片寬度鎖死。

### 重要的程式碼位置（行號僅供參考，之後改了會偏移，用關鍵字搜尋比較準）

- `const AREAS = [...]`：四個牆面圖樣（about / writing / newsletter / design）的所有位置、大小、角度、對應素材路徑、螢光框顏色設定。
- `function layoutStage()`：響應式核心，設定 `--u`。
- `function shell(a, backFn, opts)`：展開頁共用的「大標題 + 返回鍵」外殼。
- `const RENDER = { about(){...}, writing(){...}, design(){...} }` + `RENDER.newsletter = function(){...}`：四個區域各自的內容渲染邏輯，讀 `SITE.xxx`（來自 `content/content.js`）。
- `designDetail(w)` / `writingDetail(w)` / `issueDetail(w)`：單一作品／文章／電子報期數的詳細頁。
- `function fadeSwap(fn)`：淡出→換內容→淡入的過場動畫，設計頁的切換都走這個。
- 訂閱彈窗：`openModal / closeModal`，送出時 POST 到 `newsletterForm`（讀自 `assets/06-newsletter/newsletter.md` 的 `form:` 欄位，目前接的是使用者的 Formspree：`https://formspree.io/f/xjykadnb`）。

## 內容怎麼填（給使用者編輯用，工具已經寫好）

- `assets/CHECKLIST.md`：**最重要的參考文件**，每個資料夾要放什麼檔案、檔名規則、`.md` 的欄位格式都寫在這裡。使用者改素材前應該先看這份，Claude 回答「怎麼加作品/文章」之類的問題也直接引用這份，不用重新發明規則。
- `tools/build-content.py`：掃描 `assets/03~06` 底下的資料夾和 `.md`，產生 `content/content.js`。改完素材或這支腳本後要重新跑：`python3 tools/build-content.py`（雙擊專案根目錄的「更新網站內容.command」效果一樣）。
- `tools/build_font_subset.py`：把使用者系統裡的「源流明體」（`~/Library/Fonts/GenRyuMin-EL.ttc` / `GenRyuMin-B.ttc`，注意**不是** Downloads 裡那份「注音版」`BpmfGenRyuMin`）瘦身成只含網站實際用到的字的 `.woff2`，跑法：`python3 tools/build_font_subset.py`。**如果新增了很多新文字（例如一大批新文章），沒跑這個的話新字會顯示成一般字型 fallback（不會壞，只是字體不一致）**，記得提醒使用者或主動重跑。
- **圖片大小紀律**：使用者常常直接丟手機拍照或掃描的原始檔，動輒 20-40MB。放新圖片進資產夾前，或發現有超大檔案時，用 `sips --resampleWidth <px> -s format jpeg -s formatOptions 82 file.jpg` 壓縮（macOS 內建工具，不用額外安裝）。**使用者的習慣是「原檔直接覆蓋刪除，不用另外備份」**，除非他另外說要保留。目前約定的建議尺寸都寫在 CHECKLIST.md 裡。

## 使用者的溝通習慣（重要，照著做不用重新摸索）

- 全程用**繁體中文**回覆。
- 使用者不太會寫程式，但很清楚自己要什麼效果，常常會**上傳截圖／手繪示意圖**來說明版面、位置、動畫。收到示意圖時：
  - 如果是要求「精確對齊」的東西（像素級的裝飾線、圖樣位置），**用程式讀圖片像素座標去量**，不要用肉眼目測，過去幾次目測都不夠準，使用者會抓出來。
  - 如果使用者說「不用鎖死、可以配合畫面」，就不用逐像素校準，抓合理的比例就好。
- 使用者對「不要用 AI 生成圖案，所有視覺素材都要她自己畫或拍」有堅持——**Claude 絕對不要自己生成或建議用 AI 生成圖片來填內容**，暫代圖案只能用簡單的色塊/形狀/文字佔位，等使用者提供真的素材再換上去。
- 每次改完，養成習慣：**先在瀏覽器裡實際操作測過（桌機＋手機兩種尺寸），再跟使用者回報**，不要只憑改程式碼的邏輯推斷「應該可以了」。過去好幾次改完看起來合理，實測才發現 CSS 優先權/塌陷之類的坑。
- 使用者會主動要求刪掉不需要的備份檔案（不喜歡佔空間），改動前不用刻意每次都留一份 `.backup` 檔，除非是大改動、值得留一手；但改完确定沒問題後，記得清掉暫時性的備份與測試檔案。

## 尚待處理 / 懸而未決的事

- 使用者上一輪訊息提過「(6)」但**內容是空的**（訊息被截斷），還沒補上是什麼需求，下次她提到時接續處理即可。
- Design 分類頁的行動裝置版面，目前沿用桌面版類似的邏輯（每年最多顯示 2 件、超過用「更多」），但**沒有拿到使用者手機版 design 詳細頁的示意圖**做逐項核對，如果她之後有意見要調整不意外。
- `assets/06-newsletter/` 底下有一個叫「孵化中...」的資料夾（使用者自己建的一篇電子報期數），命名和其他資料夾的英文慣例不一致，正常運作，不用主動去動它。
