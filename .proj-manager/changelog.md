# 專案變更日誌

本檔案記錄所有由 project-manager skill 協助進行的專案修改。

---

## [建置可重現性、分子分類、Google 登入] - 2026-09-01 | PR #33〜#39

### 變更類型

新增功能 ＋ 優化 ＋ 修復（feature-017〜020、mod-035〜038）

### 背景

這輪起於一次橫向比對：拿本專案跟同一台機器上的其他專案（km-util、heyids200、
TPEX、CSPTC、NCDR）對照工程配置，發現 ElementGroups 是**唯一**同時沒有測試、
沒有 CI、沒有 lint、依賴也完全沒釘版本的專案。對一個 push 就自動部署的站來說，
最後一項風險最大：同一份程式碼今天和下個月 build 出來是不同的東西，網站可能在
沒動程式的情況下壞掉，而且回不到昨天能跑的組合。

修完基礎建設後，接著做了分子分類與 issue #32 的 Google 登入，過程中連帶踩到
兩個 Firebase 的坑（見下方）。

### 做法

**建置可重現性與 CI（feature-017 / PR #33）**

- `requirements.txt` 從 13 個裸套件改為 67 筆全釘死（含間接依賴）。版本在
  `python:3.11-slim`（Dockerfile 同一個 base image）實際解出來，非估計
- 順手移除 `Flask-Cors`——CORS 是 `app/__init__.py` 手寫的，該套件從未被 import
- 前端 Dockerfile 與 `render.yaml` 改用 `npm ci`；原本有 `package-lock.json`
  卻用 `npm install`，等於 lock 檔形同虛設
- 新增 `.gitattributes`（`eol=lf`）。過去每次 commit 都要手動轉行尾，且已經有
  三個檔案帶著 CRLF 進了版控，一併正規化
- 新增 GitHub Actions build check：前端建置、後端檢查、防退化檢查（requirements
  必須全釘死、CRLF 不得進版控）

**分子依金屬性自動分類（feature-018 / PR #34）**

分子頁原本只有搜尋加一片平鋪卡片。查下去發現 `category` 欄位早就存在、後台也能
填，卡在三件事疊在一起：公開 API 的 slim 投影漏了這個欄位、PubChem 帶入資料時
不推斷分類（4 筆全空）、預設分類裡沒有「單質」而現有 3/4 正是單質。

分類軸選**組成元素的金屬性**而非有機／無機——後者邊界是慣例問題，要人工維護
例外表；金屬性查表就有答案。對照表取自週期表 `GroupBlock`，寫成靜態表，前台
即時算，不多打 API。後台手填的 `category` 永遠優先，既有資料不必回填。

**Google 帳號登入（feature-019 / PR #35、#36、#38）**

- 後端多一支端點收 ID token，驗完一樣走 `ADMIN_ACCOUNTS`，發相同的 session token
- Firebase SDK 用 `await import()` 動態載入：主 bundle 只增加 4.6 KB，firebase
  切成獨立 chunk 245 KB（gzip 51 KB），按下按鈕才下載
- 開啟 Google 後帳密登入預設連動關閉（擋在後端，不是只藏前端表單），
  `PASSWORD_LOGIN_ENABLED=true` 是逃生門
- 頁尾入口改為點兩下才展開；`/admin` 保留「使用其他方式登入」作為備援，且不再
  顯示頁尾

**後台登入帳號管理（feature-020 / PR #39）**

維護工具可列出所有 Firebase Auth 帳號（含 `providers` 與 email 驗證狀態），並用
Admin SDK 直接把白名單內帳號的 email 標記為已驗證。補上 issue #31 提過但未做的
項目——原本的 `scripts/list_auth_users.py` 需要 Firebase 憑證，而免費方案的
Render 沒有 Shell，那支腳本實際用不到。

### 踩到的坑

**Firebase 會移除同 email 底下「未驗證」的密碼憑證。** 用 Google 登入之後帳密就
再也進不去，而密碼並沒有記錯。這是防帳號劫持的既定行為，症狀是 401「Incorrect
email or password」，唯一看得出來的地方是 `providers` 少了 `密碼`。根治方式是把
email 標記為已驗證——但驗證信被企業信箱擋掉，且主控台沒有對應按鈕，所以才做了
feature-020。

**授權網域要填前端網域**（`elementgroups-frontend`），不是後端（`elementtable`）。
填錯會得到 `auth/unauthorized-domain`，而錯誤訊息不會說是這個原因。

**iOS Safari 的 `dblclick` 對非輸入元素不可靠**，iPad 實測完全打不開（mod-036）。
`touch-action: manipulation` 只能避免縮放手勢搶事件，不保證 Safari 會派發
`dblclick`——當初把這兩件事混為一談。改成自己用 `click` 記時間戳比對。

### 部署後驗證

- pandas 2.x→3.0.5：`/api/groups`（vs／cp）與 `/api/elements/:symbol/ability`
  的回應與升級前**逐位元組相同**
- 後端確實換版（`/api/molecules` 出現 `category`、`/api/auth/firebase-config`
  從 404 變 200），排除了「部署失敗、舊版還在跑」的可能
- Render 的 CSS hash 與本機 `npm ci` 產物一致，建置可重現性得到實證
- 繞過前端直接打 `/api/auth/login`，確認帳密登入是被後端擋下而非只有前端隱藏
- 新端點未登入回 401（非 404 也非 200），授權正確

### 影響評估

- 風險等級: Medium（依賴大版本升級 ＋ 登入方式變更，皆已部署驗證）
- 受影響功能: feature-016（浮水印頁文案）、feature-017〜020
- 破壞性變更: Yes — 開啟 `GOOGLE_LOGIN_ENABLED` 後帳密登入預設關閉，
  且 `POST /api/auth/login` 在該狀態下一律回 401

---

## [功能] - 2026-08-14 | feature/watermark

### 變更類型

隱形浮水印（issue #25，feature-016、mod-034）

### 背景

issue #25 原本列了三件事：右鍵下載阻擋、隱形浮水印、截圖時二次處理。第一、三件
不成立——圖片要顯示在螢幕上，位元組就已經在對方電腦裡；瀏覽器也偵測不到截圖。
目標改成「拿走也沒用，或拿走能被抓到」，只做浮水印。

### 做法

簽名藏進色度：直接在 RGB 上加一組固定位移（−1.402, +0.370, +1.772），那正好
等價於「Cb 加、Cr 減」而 ΔY = 0，所以亮度真的沒動。把色度差高通再放大，簽名就
浮出來。後台可開關、可選文字或自訂圖樣、可調強度，另附試套用與檢驗兩個工具。

### 實測（9 張圖，強度 3）

| 情境 | 分數（門檻 0.75） | 驗到 |
|---|---|---|
| 原圖 | 0.53〜1.56 | 9/9 |
| 乾淨的圖（不該驗到） | 0.04〜0.29 | 0/9 |
| 裁掉 30% | — | 4/7 |
| 縮一半 + 壓 quality 0.6 | — | 6/7 |

### 過程中修掉的三個假陽性來源

1. **高通用「縮小再放大」取低頻**，在平滑漸層上留下以取樣格為週期的漣漪，乾淨的圖
   假陽性 3.4（門檻 0.5）。改用移動平均這種位置無關的做法
2. **邊緣主導相關值**：輪廓與色塊交界的色度落差是浮水印的十幾倍。相關前先把殘差
   夾在中位數的三倍以內
3. **放大兩倍的圖樣只是幾團色塊**，很容易和畫面裡的色塊對上。一個尺度至少要能放進
   6 個圖樣單元才列入比對

### 沒做

動態圖的逐幀浮水印（前端上傳走 canvas，GIF 早就被壓成單張）。既有圖片不會自動補，
要跑 `scripts/backfill_watermark.py`。

---

## [Issue #20~#23 與後續維護] - 2026-08-11 | commit e68d29c..0c6fe80

### 變更類型

新增功能 + 功能修改 + 修復 + 優化

### 變更摘要

處理 GitHub issues #20~#23，共 13 個 commit，全數部署至 Render。
新增兩個功能模組（SEO 基礎建設、元素分層動畫與繞行粒子），重構後台頁面管理，
並修掉三個既有缺陷——其中兩個是用瀏覽器實際操作才發現的，不在原本的 issue 範圍。

### 改動

**新增功能**
- SEO 基礎建設（feature-013，issue #21）：build 時產生 sitemap.xml 與 robots.txt、
  每頁獨立的 title/description/canonical/og、元素頁 ChemicalSubstance 與分子頁
  MolecularEntity 的 JSON-LD、118 個元素頁的靜態預渲染；新增 /api/elements/seo
- 元素分層動畫與電子樣式庫（feature-012，issue #23）：三種運動模式真正區分——
  分層繞行含前後景深、Teleport 到 body 的全頁飄動、等角度靜止排開；
  運動方式改為全站統一設定

**功能修改**
- 後台頁面管理統整（mod-006，issue #20）：系統頁與自訂頁併成同一張表格，
  改為清單／編輯兩段式；頁面資料模型補上 subtitle 與 seo_description
- 預設文案改英文佔位、內建說明書清空（mod-009）

**修復**
- 故事頁編輯視窗在矮視窗下超出畫面；關閉鈕與 Bulma `.modal-close` 撞名疊在標題上（mod-007，issue #22）
- 後台文字對比只有 1.54，整個後台的標題與欄位名幾乎看不見（mod-008，**非 issue**）
- 導覽列的內建頁面標題與頁面本身不一致：BUILTIN_NAV 是第二個真相來源（mod-009，**非 issue**）
- 部分頁面無法自行決定導覽位置：內建 Markdown 頁的欄位被 mod-006 藏起來（重構退步），
  純文案頁（/molecules、/particles）則從來就沒有這個設定（mod-011，**非 issue**）
- 頁面清單的系統頁標題重複顯示路徑

**維護（非 issue）**
- docker compose 對外 port 可用 .env 覆寫，預設值不變（mod-010）
- gitignore 憑證類檔案（*token*.txt、*.pem、service-account*.json）
- docs/verification/ 新增 5 張驗收截圖

**移除**
- 後台「預設圖片」獨立區塊：併入「圖層素材」
- 每元素的 motion 欄位：改為全站設定

**過程中的錯誤與還原（mod-012）**
- 一度把 `_electron_styles` 整個換成從 `_particles` 挑一種粒子，超出站長要求的範圍。
  站長要的是「圖庫可以上傳多個樣貌」，原本的樣式庫就能滿足，只是名字叫「電子樣式」。
- 已完整還原：樣式庫、每元素的個別指定、「帶入預設電子圖」全部回來。
  Firebase 資料從未被刪除，還原程式後即恢復。

### 影響評估

- 風險等級: Medium
- 受影響功能: feature-003、feature-007、feature-010、feature-011、feature-012、feature-013
- 破壞性變更: No（舊的 `_electron_styles` 與每元素 motion 資料留著但不再讀取）

### 備註

- **若正式站的資料庫沒有存過 /guide 頁面，清空內建內容後該頁會是空白**，部署後需確認
- issue #23 的「靜止排開」語意仍待站長確認，已在 issue 留言提出
- issue #20 的區塊編輯器未納入，理由記錄於 mod-006 與 issue 留言
- Google Search Console 註冊需站長操作
- 本次驗證改用 docker compose；真後端需要 Firebase 私鑰，驗證時以 mock 後端替代
- 站長回饋後台可調整的項目仍偏少（相較 issue #20 附的參考專案），尚未收斂範圍
- **待辦**：站長希望圖庫不只限於電子——每個基本粒子都能有自己的多個樣式，
  圖庫如何組成由站長決定。尚未實作

---

## [Issue 批次處理：#2~#11] - 2026-08-09 | commit 6199f4c..f384b72

### 變更類型

新增功能 + 修復 + 優化

### 變更摘要

處理 GitHub issues #2~#11 的全部需求與後續回饋，共 19 個 commit，全數部署至 Render。
新增七個功能模組（完成度標示、社群連結、網站設定與 SEO、圖片處理、AI 故事協助、
首頁檢視方式、元素圖鑑呈現），並修掉四個既有缺陷。

### 改動

**新增功能**
- 元素完成度標示：Admin 下拉註記 + 首頁週期表圓點（feature-001，issue #5）
- 創作者社群連結：不限數量、可設頭像與自訂色、Connect 頁描述（feature-002，issue #6）
- 網站設定與 SEO：後台編輯文案與背景圖，build 時注入 og/twitter 標籤（feature-003，issue #3）
- 圖片壓縮與裁切：長邊 1200px、5MB 上限、1:1/4:3/3:4 裁切框（feature-004，issue #4）
- AI 故事協助：Gemini 串接、每日次數上限、草稿帶入（feature-005，issue #8）
- 首頁檢視方式：分組下拉 + 三種樣式、最近更新／熱門元素（feature-006，issue #7-1、#7-2）
- 元素圖鑑呈現：數值條、基本資料區、圖鑑外框、其他樣貌圖庫、說明書頁（feature-007，issue #7-3、#7-4、#9）

**後台介面**
- 功能區塊改為側邊選單，一次只顯示一項；同樣內容從捲動 5.2 屏降至 2.2 屏（issue #3 回饋）
- 「目前圖片」移至上傳欄位旁與新圖並排，可直接對照
- 移除所有輸入框的範例文字，改用欄位標題與 aria-label
- 切換編輯元素時清空 AI 的方向、參考資料與建議

**修復（皆為既有缺陷）**
- 元素頁圖片全數破圖：路徑寫死相對 /api，被 Render 的 SPA fallback 吞掉（mod-003）
- 儲存故事可能清空既有圖片：Firebase 讀寫錯誤被吞噬（mod-002）
- 週期表 hover 放大被容器裁切、滾輪置中偏移 182px（mod-003）
- 缺少 .dockerignore 導致 docker build 必定失敗（mod-003）
- 完成度標示原本會全部失效：後端只回 Storage URL，但專案預設走 base64
- 詳細清單的原子量與常溫狀態全為空：/api/elements 只回傳四個欄位
- emoji 在介面字型下渲染成方框，改用幾何符號

**移除**
- PeriodicTable.vue：職責已被 ElementIconGrid 完全涵蓋
- style.css 的 .elements-box / .elements：改用元件後的殘留死碼

### 影響評估

- 風險等級: Medium
- 受影響功能: feature-001 ~ feature-007
- 破壞性變更: No（`_creator_links` 格式擴充但向後相容三種歷史格式）

### 備註

- 待確認事項記錄於 issue #10（頁面管理 CMS）與 #11（分子區塊），均已提出設計方案等待回覆
- AI 故事生成的截斷修正已上線但尚未實測

---

## [初始化] - 2026-02-23T00:00:00Z

### 變更類型

專案啟動 + 部署方式修改

### 執行動作

- 建立 `.proj-manager/` 目錄結構
- 生成專案記憶檔案 (project.json, structure.json, dependencies.json, context.md)
- 建立 Docker 部署設定 (backend/Dockerfile, frontend/Dockerfile, frontend/nginx.conf, docker-compose.yml)

### Git 標籤

`proj-manager-skill-init`

### 備註

- 原部署方式為 Render.com，使用 `Procfile: web: python run.py`
- 改為 Docker Compose，支援本地或任意主機部署
- 前端使用 Nginx 提供靜態資源並反向代理 `/api` 到後端

---

## [重大重構] - 2026-02-23 | commit 4bd7b72

### 變更類型
移除 SQLite/SQLAlchemy，全面改用 Firebase Realtime Database

### 執行動作

**後端**
- `firebase.py`：新增 `periodic_table_ref`、`periodic_table_exists()`、`upload_periodic_table()`、`get_periodic_table()`、`get_element_by_symbol()`、`get_element_by_atomic_number()`
- `elements.py`：移除 sqlite3、`_get_db_path()`；改用 `_get_periodic_table_df()` 從 Realtime DB 取資料
- `routes/public.py`：移除 SQLAlchemy session，改用 Firebase 函式；`get_elements()` try/except 修正
- `routes/admin.py`：移除 ElementGroups、alchemy_db；`update_db()` 加「已有資料則略過」邏輯；`create_db()` 改回傳說明
- `app/__init__.py`：移除 SQLAlchemy 初始化
- `run.py`：移除 `alchemy_db.create_all()`
- `app/config.py`：移除 `DATABASE_URI`
- `.env.example`：移除 `DATABASE_URI`
- `requirements.txt`：移除 flask_sqlalchemy、SQLAlchemy
- `app/models.py`：清空
- `Dockerfile`：gunicorn workers 2 → 1（修正 session 跨 process 失效 401 問題）

**前端**
- `frontend/.env.production`：新增 `VITE_API_URL=/api`（修正 405 問題）

**Docker**
- `docker-compose.yml`：移除 SQLite volume；前端 port 80 → 8080（Windows 限制）

### 修正問題
- 405 Not Allowed：VITE_API_URL 未設，請求不帶 `/api` 前綴
- 401 Unauthorized：gunicorn 多 worker session 失效
- Firebase Index 錯誤：`get_element_by_atomic_number` 改為 Python 端 filter
- AtomicNumber 排序：`get_periodic_table()` 回傳前按 int(AtomicNumber) 排序

---

## [功能新增] - 2026-02-23 | commit 7a22b3f

### 變更類型
圖片 base64 備援儲存 + .gitignore 更新

### 執行動作
- `routes/admin.py`：上傳圖片時額外存 base64 至 Realtime DB `img_data` 欄位
- `routes/public.py`：`GET /api/elements/:symbol` 回傳新增 `img_data` 欄位
- `.gitignore`：新增 `.idea/`

---

## [維護] - 2026-02-23 | commit e341b13

### 變更類型
清理 SQLite 殘留檔案

### 執行動作
- 刪除 `backend/elementGroups.db`

---

## [文件] - 2026-02-23 | commit 26de99a

### 變更類型
README 更新

### 執行動作
- 重寫 README：技術架構、Docker 啟動步驟、環境變數說明、API 端點列表

---

## [前端優化] - 2026-02-23 | commit 463f36b

### 變更類型
前端 UI 優化

### 執行動作
- 新增 `LoadingSpinner.vue`：全域半透明 overlay 轉圈元件
- `HomeView.vue`：初始載入與切換分組顯示 spinner；active 按鈕 highlight；fade 過渡動畫
- `StoryView.vue`：loadData 期間顯示 spinner；img_src → img_data → altImage 三層 fallback；ability bar 寬度 transition
- `AdminView.vue`：所有非同步操作加 spinner；成功/失敗訊息顏色區分
- `style.css`：按鈕 hover/active 樣式；元素卡片 hover scale；header backdrop-blur

---

## [功能新增 + 修正] - 2026-02-23 | pending commit

### 變更類型
Admin 登入 UI 重排 + 元素頁面 inline 編輯 + Session / Auth 修正

### 執行動作

**後端**
- `app/__init__.py`：Session 改為 sliding 機制（靜置 10 分鐘過期），`PERMANENT_SESSION_LIFETIME=10min`、`SESSION_REFRESH_EACH_REQUEST=True`、`session.permanent=True`
- `app/auth.py`：`logout()` 移除 `@login_required`，避免 session 過期後無法登出
- `routes/admin.py`：`show_fdb()` 迭代時過濾 `periodic_table` 節點（避免與故事資料衝突的 KeyError）；`fbDatas[data]` 改用 `.get()` 存取 `img`/`description` 欄位

**前端**
- `App.vue`：Admin 登入區塊從標題旁移到標題下方（header-inner 改 column layout），避免破版
- `StoryView.vue`：
  - 在「Atomic NUMBER: XX」標題旁新增「Edit」按鈕（需登入才顯示）
  - 點擊後以 Modal overlay 顯示編輯表單（故事文字 + 圖片上傳）
  - 儲存成功後即時更新畫面；有圖片更換時重新載入資料
  - Modal 可點擊遮罩關閉

### 修正問題
- `POST /api/admin/story` 500 KeyError `'img'`：Realtime DB 根節點同時有故事資料和 `periodic_table` 子樹，後者沒有 `img` 欄位
- 401 on logout：`@login_required` 在 session 過期後阻擋登出請求
- Session 5 分鐘太短：改為 10 分鐘 sliding session，使用中不會斷線

---

## [修正] - 2026-02-23 | pending commit

### 變更類型
統一 Auth 狀態，修正切換頁面被登出問題

### 根本原因
`AdminView.vue` 擁有自己獨立的 `loggedIn: false` 本地狀態，與 `authState` store 完全分離：
- 從 Header 登入 → `authState.loggedIn = true`，但 AdminView 的 `this.loggedIn` 仍為 `false` → 進入 `/admin` 頁面顯示登入表單（外觀上像被登出）
- 從 AdminView 登入 → `this.loggedIn = true`，但 `authState.loggedIn` 仍為 `false` → StoryView 看不到 Edit 按鈕

### 執行動作

**後端**
- `routes/admin.py`：新增 `GET /api/auth/status` endpoint，回傳 `{"loggedIn": current_user.is_authenticated}`，供前端重整頁面後恢復登入狀態

**前端**
- `api/index.js`：新增 `getAuthStatus()` 函式
- `store/auth.js`：新增 `initAuth()`，呼叫 `/api/auth/status` 恢復登入狀態；改用 store 的 `login`/`logout` 給 AdminView 使用
- `App.vue`：新增 `created()` 呼叫 `initAuth()`，頁面載入（含重整）時自動恢復登入狀態
- `AdminView.vue`：
  - 移除本地 `loggedIn` 狀態
  - 改用 `authState` + store 的 `login`/`logout`（從 `'../store/auth'` 匯入）
  - 新增 `mounted()` 鉤子：若已登入則自動載入 story 資料

### 修正問題
- 切換到 `/admin` 頁面後顯示登入表單（狀態不同步）
- 從 AdminView 登入後 StoryView 不顯示 Edit 按鈕（狀態不同步）
- 頁面重整後登入狀態遺失（`initAuth()` 修正）

---

## [修正] - 2026-02-23 | pending commit

### 變更類型
修正切換頁面後端 session 失效（401 無權限）

### 根本原因
Flask-Login 預設的 session protection 機制：將 `hash(remote_addr + user_agent)` 存入 session 作為識別符。
在 Windows Docker 環境中，localhost 請求有時使用 IPv4 (`127.0.0.1`)，有時使用 IPv6 (`::1`)，
兩者 hash 不同 → Flask-Login 認為識別符被竄改 → 自動將 `_user_id` 從 session 移除 → 後續請求匿名 → 401。
前端 `authState.loggedIn` 仍為 true（因為沒有任何機制通知），故 Edit 按鈕持續顯示。

### 執行動作

**後端**
- `auth.py`：設定 `login_manager.session_protection = None`，停用 IP/UA 識別符檢查

**前端**
- `store/auth.js`：`initAuth()` 只允許設為 true，不設 false，
  避免 pending request 在用戶登入後才返回而覆蓋登入狀態（race condition 防護）
- `App.vue`：在 `created()` 加入 axios 401 interceptor，
  任何 401 response 自動將 `authState.loggedIn = false`，確保前後端狀態同步

### 修正問題
- 切換頁面後嘗試編輯顯示 401 無權限（IPv4/IPv6 切換導致 session 失效）
- `initAuth()` race condition：用戶登入後 stale request 返回 `{"loggedIn": false}` 覆蓋狀態
- 前端不知道後端 session 已失效（Edit 按鈕顯示但操作失敗）

---

## [功能新增] - 2026-02-23 | pending commit

### 變更類型
新增週期表（Periodic Table）排版模式，設為首頁預設

### 執行動作

**前端**
- `components/PeriodicTableGrid.vue`（新建）：
  - CSS Grid 18 欄 × 10 列，對應 IUPAC 標準週期表位置
  - row 1–7：主週期；row 8：10px 視覺間隔；row 9–10：鑭系 / 錒系
  - (6,3) / (7,3) 顯示佔位標示（57–71 / 89–103）
  - `aspect-ratio: 1/1`，`min-width: 620px` 加 `overflow-x: auto` 支援小螢幕水平捲動
  - `font-size: clamp(7px, 1vw, 13px)` 響應式字體
- `HomeView.vue`：
  - 新增 'table' 模式，設為預設（`showMode: 'table'`）
  - 加入第一個按鈕「Periodic Table」
  - 移除 `showNone()` method，改用 inline `@click`
- `style.css`：
  - `.group-type-button` 由 3 欄改為 4 欄
  - mobile 響應式由 1 欄改為 2 欄

---

## [修正 + 優化] - 2026-02-24 | pending commit

### 變更類型
PeriodicTableGrid 樣式對齊 + 響應式分組備援 + 分組資料快取

### 執行動作

**前端**
- `PeriodicTableGrid.vue`：
  - 根本修正：改用與 `PeriodicTable.vue`、`GroupBox.vue` 相同的 `div.element > router-link` 結構
  - scoped 樣式中 `.pt-grid .element` 僅覆寫 size（`width: 100%; aspect-ratio: 1/1`）和 font（`clamp`），
    其餘全域樣式（background、border、hover 等）完全繼承，確保外觀一致
  - 新增響應式邏輯：`window.innerWidth < 700px` 切換至分組備援模式，監聽 `resize` 事件
  - 分組備援：依週期表欄位產生 CAS 符號（1A/2A/3B.../1B/2B/3A.../8A），鑭系/錒系獨立群組
  - 備援直接使用全域 `.element`、`.elements-box`、`.group-box`、`#group` 樣式，外觀與其他分組模式一致
- `HomeView.vue`：
  - 新增 `groupsCache: {}` 儲存已載入的分組資料
  - `loadGroups(type)` 優先從 cache 取用，避免重複打 API

---

## [功能新增] - 2026-02-24 | commit 503cba0

### 變更類型
新增圖片 proxy API，隱藏 Firebase Storage URL

### 執行動作

**後端**
- `firebase.py`：新增 `get_image_bytes(symbol)`，從 Storage 下載圖片位元組（`static/img/{symbol}.JPG`），無圖片時 fallback 至 `static/img/Electron.JPG`；引入 `google.cloud.exceptions.NotFound`
- `routes/public.py`：新增 `GET /api/elements/<symbol>/img` proxy endpoint，回傳圖片 bytes，附加 `Cache-Control: public, max-age=86400`；`get_element_detail()` 移除 `img_src`（Storage 公開 URL）與 `alt_image`（硬編碼 Storage URL）欄位

**前端**
- `StoryView.vue`：`imgSrc` 改用 `/api/elements/:symbol/img`（不再從 API response 取 URL）；移除 `altImage` 狀態；`resolvedImg` 簡化為 proxy URL → base64 (`img_data`) 兩層 fallback

### 修正問題
- Firebase Storage 圖片 URL 不再暴露給前端瀏覽器
- `alt_image` 硬編碼 Storage URL 也一併移除

---

## [功能新增] - 2026-02-24 | commit d23c091

### 變更類型
新增 backfill-img-data endpoint，補齊舊圖片 base64

### 執行動作

**後端**
- `routes/admin.py`：新增 `POST /api/admin/backfill-img-data`（需登入），遍歷 Realtime DB 中有 `img` 但無 `img_data` 的元素，使用 `get_image_bytes()` 從 Storage 下載圖片並寫入 base64；已有 `img_data` 者略過，回傳 updated/skipped 計數

**前端**
- `api/index.js`：新增 `backfillImgData()`
- `AdminView.vue`：新增「Backfill img_data」按鈕，點擊後顯示成功/失敗訊息

---

## [UI 全面優化] - 2026-02-24 | 多個 commits

### 變更類型
宇宙主題 UI、StoryView 導覽重構、元素格子優化、響應式改善

### 執行動作

**後端**
- `routes/public.py`：`/api/elements` 與 `/api/groups` 回傳加入 `Name` 欄位
- `routes/admin.py`：backfill-img-data 改用 `ThreadPoolExecutor` 並行下載（N 次串行 → 並行，解決 Gunicorn timeout）
- `routes/admin.py`：移除 Log out 按鈕（已移至 header）

**前端 — 宇宙主題**
- `style.css`：body 改星雲漸層背景（紫/藍 radial-gradient）
- `style.css`：header 加星星（20 顆 radial-gradient）+ 銀河光暈，透明度 80%
- `style.css`：新增宇宙主題 scrollbar（6px，紫→青漸層）
- `style.css`：`.group-type-button` 改 flex 底線頁籤（active 有 glow 底線）
- `style.css`：元素格子背景改半透明玻璃效果，hover glow 加強（雙層 box-shadow）
- `style.css`：加入 `.el-num / .el-sym / .el-name` 三層文字樣式
- `StoryView.vue`：ability bar 改紫→青漸層；`#element-ability` 邊框改柔邊 + 光暈；`grid-auto-rows` 50px→36px
- `AbilityChart.vue`：chart 背景改深空黑、雷達線改宇宙藍 `#64b8e8`
- `LoadingSpinner.vue`：多色軌道邊框 + glow 效果
- `AdminView.vue`：表單 `.box` 加半透明深紫背景

**前端 — StoryView 導覽**
- 前後導覽改 `←` / `→` 箭頭（48px，窄螢幕 28px）
- 首/末元素時箭頭 dim（`nav-arrow--dim`）
- 新增 `touchstart/touchend` 手勢，滑動 >50px 切換元素
- 窄螢幕：標題佔滿第一行，箭頭排第二行（`flex-basis: 100%` + `order: -1`）

**前端 — StoryView 頁籤**
- 介紹→Story、雷達圖→Radar、能力圖→Ability
- 新增 fade transition

**前端 — 元素格子**
- 三個元件（PeriodicTable / GroupBox / PeriodicTableGrid）template 改用 `<span>` 結構顯示全名
- PeriodicTableGrid 格狀視圖隱藏 `.el-name`（格子太小）

**前端 — PeriodicTableGrid**
- 響應式斷點從固定 700px 改為動態計算：格子寬 < 70px 時切換分組備援

**前端 — App.vue / AdminView.vue**
- Header 登入後新增 Admin Page 連結（`/admin`）
- AdminView 移除 Back To Index 和 Log out 按鈕（已整合至 header）

---

## [功能新增 + 修正] - 2026-06-15 | commits 0f40015 57d18d7 b284b3d

### 變更類型
Toast 通知系統、元素滾輪導航、Session Cookie 跨域修正、週期表顯示修正、後端冷啟動提示

### 執行動作

**後端**
- `app/__init__.py`：新增 `SESSION_COOKIE_SAMESITE="None"` 與 `SESSION_COOKIE_SECURE=True`
  - 解決前後端不同 Render 子域（跨域）時 Session Cookie 無法傳遞導致登入後 401 的問題

**前端 — Toast 通知系統**
- `src/store/toast.js`（新建）：全域 reactive store，`showToast(message, type, duration)` / `removeToast(id)`
- `src/components/ToastContainer.vue`（新建）：
  - `<teleport to="body">` 渲染到 body 層級，不受父層 overflow 影響
  - `<transition-group name="toast">` 支援堆疊動畫（右側滑入）
  - 4 種類型：success（綠）/ error（紅）/ warning（黃）/ info（青）
  - 3500ms 自動消失，可點擊提前關閉
  - 手機版出現在底部
- `App.vue`：登入成功/失敗改用 `showToast()`，移除 `errMsg` 資料與 `<span class="err-msg">`
- `StoryView.vue`：儲存成功/失敗改用 `showToast()`，移除 `saveMsg` / `saveMsgType` 資料

**前端 — 元素滾輪導航（StoryView）**
- `src/store/elements.js`（新建）：共享 reactive store 快取全部 118 元素，`ensureElements()` lazy 載入
- `HomeView.vue`：載入元素後同步寫入 `elementsState`，StoryView 不需額外 API call
- `StoryView.vue`：
  - 移除舊版 ← → 箭頭 `element-btns` / `nav-arrow` 結構
  - 新增 `wheelElements` computed：以當前元素為中心取前後各 4 個（共最多 9 個）
  - 新增 `.nav-wheel-wrap` + `.nav-wheel` 橫向滾動條，顯示鄰近元素 chip（原子序 + 符號）
  - 當前元素 chip：`.wheel-chip--active`（較大、顏色使用元素本身 CPKHexColor）
  - `scrollWheelToActive()`：`$nextTick` 後自動將 active chip 捲至置中
  - `ensureElements()` 加入 `loadData()` 的 `Promise.all`

**前端 — 週期表格狀顯示修正**
- `PeriodicTableGrid.vue`：
  - 移除 `shouldGroupFallback()` 與整個分組備援模式（是造成在 1280px 螢幕顯示 1A/2A/3B 群組的根本原因）
  - 永遠顯示 CSS Grid 18 欄格狀週期表，手機透過 `overflow-x: auto` 橫向捲動
  - 補上 `:data-name` tooltip 與 `el-num` / `el-sym` span 一致性

**前端 — LoadingSpinner 冷啟動提示**
- `LoadingSpinner.vue`：
  - 掛載後啟動兩個 timer（`beforeUnmount` 時清除）
  - 10 秒後：顯示「Waking up the server…」提示卡（淡入 + 三點 pulse 動畫）
  - 22 秒後：升級為「Still waking up…」+ Render 免費方案休眠說明

### 修正問題
- 登入成功後 `GET /api/admin/story` 回 401：Flask `SameSite=Lax`（預設）阻擋跨域 Cookie 傳送
- Periodic Table 在 1280px 螢幕顯示群組而非格狀：fallback 閾值 70px 計算出格子 68px 而觸發
- StoryView 上下頁只有 ← → 箭頭：改為顯示多個鄰近元素的滾輪 UI

---

## [修正] - 2026-06-15 | 本次 commit

### 變更類型
元素滾輪導航修正 + 搜尋欄移出 Periodic Table 限制 + PeriodicTableGrid 分組備援根因說明

### 根本原因

**滾輪不顯示**：
`ensureElements()` 放在 `Promise.all` 裡 — 任何情況下失敗（網路、後端冷啟動）就會讓整個 `Promise.all` reject，catch block 觸發，`elInfo` 設不進去，整個 StoryView 空白。
`wheelElements` 因此從未渲染。
修正：`elements.js` 改為靜態預填 118 個元素（序號 + 符號），確保滾輪在 API 回應之前就有資料可用；`ensureElements()` 改為 fire-and-forget 呼叫（不放進 Promise.all），成功時 enrich 資料，失敗時保留靜態 fallback。

**PeriodicTableGrid 始終顯示 1A/2A/3B 分組備援**：
原因是 `shouldGroupFallback()` 動態計算閾值設為 70px（對應元素格寬度），但 1280px 螢幕計算出格寬 68.3px < 70px，因此永遠觸發備援。這是 2026-02-24 將固定 700px 斷點改為動態計算時引入的 bug。
修正：移除整個備援邏輯，永遠顯示 CSS Grid 格狀週期表，手機以 overflow-x: auto 橫向捲動。
（該分組備援顯示 CAS 欄位群組 1A/2A/3B，與 Chemical Properties / Valence Shell 的化學性質分組無關，屬 PeriodicTableGrid 內部的純展示備援，移除不影響其他模式）

**搜尋欄只在非 Periodic Table 模式顯示**：
HomeView 搜尋欄有 `v-if="showMode !== 'table'"` 條件，Periodic Table 模式下被隱藏。
修正：移除條件，所有模式均顯示搜尋欄；PeriodicTableGrid 改用 `filteredElements` prop。

### 執行動作

**`frontend/src/store/elements.js`**
- 靜態預填 118 個元素的序號 + 符號（公開靜態資料，永不變動）
- `ensureElements()` 成功時以 API 回應的完整資料（含 Name、CPKHexColor）覆蓋；失敗時靜默保留靜態 fallback

**`frontend/src/views/StoryView.vue`**
- `ensureElements()` 從 `Promise.all` 移出，改為獨立 fire-and-forget 呼叫
- 滾輪現在在頁面一開啟就有靜態資料可顯示，API 回應後自動 enrich

**`frontend/src/views/HomeView.vue`**
- 移除搜尋欄的 `v-if="showMode !== 'table'"` 條件
- Periodic Table 模式下 `PeriodicTableGrid` 接收 `filteredElements`（而非 `elements`）
- Periodic Table 模式下也加入 no-results 提示

---

## [Bug 修正] - 2026-06-15 | commit f8d9629

### 變更類型
SPA 頁面重新整理 404 修正

### 根本原因
`_redirects` 檔案（`/* /index.html 200`）已正確存在於 `frontend/public/` 且 Vite build 後確認出現於 `frontend/dist/_redirects`，編碼亦正確（LF，非 CRLF）。問題推測為 Render dashboard 上靜態站點「Publish directory」設定有誤（例如設為 `./` 或未對應到 `frontend/dist`），導致 Render CDN 找不到 `_redirects` 而直接回傳 404。

### 執行動作

**`render.yaml`（新增）**
- 新增於 repo 根目錄
- 明確宣告靜態站點建置指令與發佈路徑：
  - `buildCommand: npm --prefix frontend install && npm --prefix frontend run build`
  - `staticPublishPath: ./frontend/dist`
- 宣告路由重寫規則：`/* → /index.html`（Render IaC routes rewrite）
- 讓 Render 透過 Infrastructure as Code 讀取設定，取代依賴 dashboard 手動設定

### 待確認
Render 對現有服務的 `render.yaml` 支援方式：若服務尚未啟用 IaC，需在 dashboard → Settings 手動連結，或從 repo 建立新服務。

---

## [功能修改] - 2026-06-15 | commits 53c7176 → 4dec939 → 3ba52c9

### 變更類型
Admin 登入 401 修正（多次嘗試）

### 根本原因分析
1. **CORS origins 未明確指定**：`CORS(app, supports_credentials=True)` 無 origins 限制，flask-cors 在某些版本可能輸出 `Access-Control-Allow-Origin: *`，瀏覽器拒絕在萬用字元下儲存 session cookie
2. **`load_user` 依賴 in-memory dict**：Render free-tier 冷啟動後 `users = {}` 被清空，現有 session cookie 的 user_id 無法找到對應 User object → 401
3. **flask-cors 版本行為差異**：即使明確指定 `origins=[FRONTEND_URL]`，字串完全匹配失敗（如結尾 `/` 差異）時也不套用 CORS header

### 執行動作

**`backend/app/__init__.py`**
- 移除 flask-cors，改用手動 `@before_request`（處理 OPTIONS preflight）和 `@after_request`（加 CORS headers）
- 最終改為反射任何 `Origin`（`if origin:`），確保不因 FRONTEND_URL 字串不符而失效

**`backend/app/auth.py`**
- `load_user` 加入 Firebase fallback：找不到 user 時從 `auth.get_user(uid)` 重建，解決冷啟動後舊 cookie 失效問題

**`backend/app/config.py`**
- 新增 `FRONTEND_URL: str = "http://localhost:5173"`（正式環境由 Render env var 覆蓋）

---

## [功能新增] - 2026-06-15 | commit 2b32b62

### 變更類型
Token-based 身份驗證（取代跨域 session cookie）

### 動機
Session cookie 跨域方案（SameSite=None; Secure + CORS）持續 401，根本原因是瀏覽器對跨域 Set-Cookie 的限制難以完全繞過。改用 Authorization header token 完全規避 cookie 跨域問題。

### 執行動作

**`backend/app/auth.py`（重構）**
- 新增 `tokens = {}` dict（token → uid 對照）
- 新增 `@login_manager.request_loader`：從 `Authorization: Bearer <token>` 讀取 token，查找對應 user（in-memory 或 Firebase fallback）
- `login()` 改回傳 `(token, message)` tuple；成功時用 `secrets.token_urlsafe(32)` 產生隨機 token
- `logout()` 接受 token 並從 `tokens` dict 刪除

**`backend/app/routes/admin.py`**
- `/api/auth/login` POST：回傳 `{"result": "success", "token": "<token>"}`
- `/api/auth/logout` POST：從 Authorization header 取 token 並傳給 `auth_module.logout()`

**`frontend/src/api/index.js`**
- 移除 `withCredentials: true`
- 新增 axios request interceptor：從 `localStorage.getItem('auth_token')` 取 token，加入 `Authorization: Bearer <token>` header

**`frontend/src/store/auth.js`**
- `login()`：成功後將 token 存入 `localStorage('auth_token')`
- `logout()`：清除 `localStorage('auth_token')`
- `initAuth()`：只有當 localStorage 有 token 時才查 `/api/auth/status`；失敗時清除 token

---

## [功能修改] - 2026-06-15 | commit 8bcebe1

### 變更類型
StoryView Stats tab 整合

### 執行動作

**`frontend/src/views/StoryView.vue`**
- 移除 Radar 和 Ability 兩個獨立 tab
- 新增單一 **Stats** tab，內含 Radar / Bars 小切換按鈕（pill 樣式）
- 新增 `chartType: 'radar'` data 屬性
- 新增 `.chart-type-toggle` CSS

---

## [功能新增] - 2026-06-15 | commit 7635f56

### 變更類型
預設圖管理功能

### 執行動作

**`backend/app/routes/public.py`**
- 新增 `GET /api/elements/default-img`：從 Firebase Storage `_default.JPG` 回傳預設圖

**`backend/app/routes/admin.py`**
- 新增 `GET /api/admin/default-img`：回傳 `_default` 的 base64 img_data（admin 預覽用）
- 新增 `POST /api/admin/default-img`：上傳新預設圖到 Storage + Realtime DB `_default` key

**`frontend/src/api/index.js`**
- 新增 `getDefaultImgInfo()` 和 `updateDefaultImg()`

**`frontend/src/views/AdminView.vue`**
- 新增 "DEFAULT IMAGE" 管理區塊：預覽當前預設圖 + 上傳表單

**`frontend/src/views/StoryView.vue`**
- `resolvedImg` 改為四層 fallback：Storage URL → imgData base64 → `/api/elements/default-img` → 佔位符
- `onImgError` 上限從 2 改為 3
- 新增 `imgBroken` computed
- 新增 `.img-placeholder` 樣式：以元素顏色和符號呈現無圖狀態

---

## [Bug 修正] - 2026-06-15 | commits 76b0d15 → d17e915

### 變更類型
首頁冷啟動空白 + 空查詢誤顯 no-results

### 根本原因
1. `HomeView` 的 `elements` 初始值為 `[]`，後端未回應時週期表空白
2. no-results `v-if` 條件未排除 `query === ''` 的情況

### 執行動作

**`frontend/src/views/HomeView.vue`**
- `elements` 初始值改為 `elementsState.elements`（靜態 118 個元素），冷啟動期間立即顯示
- no-results 條件改為 `v-if="query && filteredElements.length === 0"`
- 新增 `v-if="!loading && elements.length === 0"` 錯誤提示區塊（真正為空時顯示「Unable to load elements. Please refresh the page.」）

---

*後續變更將自動記錄於此*

---

## [功能] - 2026-08-10 | commits baba74c → fbafc10

### 變更類型
分子圖鑑（#11）、主族形象（#16）、基本粒子（#17）、分子分類篩選（#18）、頁面 AI 協助（#19）、手機修正（#10/#15）、後台載入提示（#13）、隱藏軌道線（#14）

### 重點

**分子圖鑑 Molecule Groups（feature-008）**
- `_molecules` node、PubChem 查詢（name/fastformula）、視覺化分子式建構器
- 前台 /molecules、/molecule/:slug；元素頁相關分子（最近 5 個＋查看全部）
- 後台清單支援搜尋／分類／元素三種篩選（參考化學資料庫慣例）

**主族形象（feature-009）**
- `_element_groups` node，20 個族各自可設形象；元素頁顯示所屬族形象
- 故事 AI 勾選「帶入主族形象設定」，後端由原子序自動對照（15 案例驗證）

**基本粒子（feature-010）**
- `_particles` node、前台 /particles 圖鑑跨頁卡片、後台自由新增

**頁面 AI 協助（feature-005 擴充）**
- POST /api/admin/page-suggest：依主題產生 Markdown（含 :::cards/:::note 語法教學）
- 編輯內建頁提供「載入最新內建模板」，模板更新改為 opt-in

### 修正的 bug
1. **重整 /admin 後資料全空**：initAuth 非同步、mounted 跳過 loadAll——「編輯內容不見了」的元凶（誤點載入內建模板覆蓋）。補 authState.loggedIn watcher
2. iOS 聚焦縮放：≤760px 全站表單元件字級固定 16px（select 13.3px / textarea 14px 都會觸發 iPhone 自動放大）
3. CSS/路由插入錨點沒對上靜默失敗兩次（主族樣式、/particles 路由）——多段替換務必 assert，或改用 Edit 工具

### 憑證備忘
- 對話中出現過 GitHub token 與 Gemini key 明碼，收尾時要提醒輪替

---

## [功能] - 2026-08-10 | commits db11995 → 79a03dd

### 變更類型
全站附加頁面文案皆可後台編輯（issue #20，feature-011）

### 重點
- `_page_meta/{key}` 覆寫層：只存改過欄位、退回內建預設、部署不影響已編輯內容
- 涵蓋 molecules／molecule／particles／story 區塊標題／footer
- 後台「頁面管理 → 內建頁面文案」編輯器，placeholder 即預設值，清空＝還原

---

## [重構] - 2026-08-11 | feature/ai-assist

### 變更類型
AiField：把「帶 AI 的文字欄位」收成一個元件（issue #26，mod-027）

### 重點
- 新增 `components/AiField.vue`：標籤列＋輸入框＋AI 協助是一組，`v-model` 寫回，附加／覆蓋的合併邏輯收在元件裡（原本三處各一份）
- 新增 `store/ai.js`：啟用狀態與每日額度的單一來源。原本 AdminView 與 StoryEditor 各存一份、各打一次 `/ai/status`，在一邊用掉額度另一邊的數字不會動
- 新增 `assets/forms.css`：`.textarea` / `.label-row` / `.field-hint` / `.ai-toggle` 原本散在兩個元件、值還不一致，AiAssist 再加第三份

### 修正的 bug
1. **頁面內容的 AI 產生了但看不到**：建議寫進 `pageForm.content`，而區塊編輯器上線後那個欄位已經沒有畫在任何地方。改掛在區塊的 Markdown 欄位上
2. **「載入最新內建模板」按了沒反應卻顯示成功**：同一個原因，只換 `content` 沒換 `blocks`
3. **StoryEditor 的 `reset()` 後半段從未執行**：`text = ''` 的 `text` 在該範圍未宣告，ES module 嚴格模式下丟 ReferenceError，切換元素時檔案輸入沒被清空
4. 後台把 AI 面板的 `.ai-quota` 借去當通用小字用了四處，面板收成元件後失去樣式，正名為 `.hint-inline`

### 備註
- 新增一種 AI 用途仍要兩筆註冊（`utils/aiKinds.js` 定義輸入、後端 `SUGGEST_KINDS` 定義提示）。那是前後端本質的分工，不是可以消掉的重複

---

## [功能] - 2026-08-11 | feature/ai-assist

### 變更類型
AI 協助擴到主族形象與頁面 SEO 描述（issue #26，mod-028）

### 重點
- `group-archetype`（創作型）：產生同族共用的設計語彙，帶入族的 key、元素清單與已定的形象名稱
- `page-seo`（摘要型）：從頁面標題與區塊內容濃縮成一句描述，提示明講「不要自己補沒提到的事」
- 兩者都不需要面板上的額外輸入——要給 AI 的東西畫面上已經有了。新增一個 kind 的實際成本就是前後端各一筆
- `blockTypes.js` 新增 `blockToMarkdown`（原本在 PageBlocks 內）與 `blocksToText`

### 修正的 bug
1. **三個頁面的 SEO 描述都讀錯欄位**：PageView / GuideView / LinksView 的 fallback 取 `page.content`，但區塊編輯器上線後那個欄位已經不是真相——用區塊編輯過的頁面拿到搬遷前的舊文案，全新頁面直接空白
2. **`:::` 圍籬漏進 meta description**：`/links` 實際長成「追蹤創作者的社群帳號。 :::links :::」
3. **AiAssist 的 extra 用 deep watch 比對物件引用**：呼叫端多半傳行內字面值或 computed，每次重繪都是新物件，內容沒變也會把面板重設

---

## [功能] - 2026-08-11 | feature/ai-phase3

### 變更類型
AI 協助補齊基本粒子、分子、網站設定（issue #26 第三階段，mod-031）

### 重點
- 四個新用途：`particle-title`（25 字視覺描述）、`particle-intro`（200〜300 字段落）、`molecule`（扣著分子式與 IUPAC 名稱）、`site-description`（全站 SEO 文案）
- 粒子拆成兩個 kind 而非一個——輸出形狀不同就該是不同的提示；兩者互為對方的 context
- 分子的空欄位在後端濾掉，避免模型把空欄位當成未知數去猜
- 額度顯示改為剩餘次數，剩 5 次轉黃、用完轉紅並停用按鈕（issue 裡點名的問題）

### 實測發現
`particle-intro` 第一版寫成第一人稱（「大家好，我是光子！」），與元素故事的第三人稱不一致——提示裡「把粒子畫成有個性的角色」被讀成要角色自己說話。補上明確的第三人稱要求後修正，字數也從 350 收到 229。

### 至此 issue #26 的接點
元素故事、頁面內容、區塊 Markdown、主族形象、頁面 SEO、粒子形象稱呼、粒子介紹、分子介紹、網站描述。「內建頁面的零碎文案」照 issue 判斷不做；「圖片說明文字」需要 vision model，另案。

---

## [修正] - 2026-08-11 | fix/library-read-amplification

### 變更類型
前台 7 個端點不再整包讀 `_libraries`（issue #30 第一步，mod-032）

### 背景
`_libraries` 一個節點裝著所有圖庫的所有圖片 base64。7 個公開端點都是 `show_fdb(LIBRARIES_NODE)` 整包讀下來，只為了取出其中一張圖——與先前 `/elements/seo` 那次 30 秒 timeout 是同一個病。

### 做法
- `show_fdb_where()`：以子欄位過濾讀取。RTDB 的 orderBy 需要索引，沒有索引時接住例外退回整包讀，所以現在合併不會壞
- 查清單的端點用 `bind_type` 過濾；查單一對象的用 `bind_id`（精準得多）
- 頁面端點改成先掃出區塊參照到哪些圖庫再逐一讀；沒有圖片參照就完全不碰 `_libraries`

### 量測（8 個圖庫 / 4.58MB）
改動前 7 個端點都讀 100%；改動後單一對象降到 12.5%（正好一個圖庫），清單端點只讀該類型。

### 索引用腳本加，不必開主控台
```bash
python scripts/ensure_db_index.py            # 預覽
python scripts/ensure_db_index.py --apply    # 寫入
```
RTDB 有 `/.settings/rules.json` 端點，用既有的 service account 就能讀寫。那支端點是整份覆寫，所以腳本先備份、只補缺的 `.indexOn`、預設不寫入。沒加索引也能運作（會走 fallback），加了之後自動變快、不必改程式。

---

## [安全] - 2026-08-11 | fix/library-read-amplification

### 變更類型
後台登入加管理員白名單（mod-033）

### 發現
在回答「Firebase 規則怎麼設才不會被入侵」時查出來的。結論是**規則不是重點**——前端完全沒有 firebase 相依，後端一律走 Admin SDK 而 Admin SDK 不受規則約束，所以規則可以直接全關。真正的洞在登入：

`login()` 只驗證「這組帳密在這個 Firebase 專案裡有效」，沒有檢查「這個人是不是站長」。Firebase Auth 的註冊是打 Google 的公開端點，只需要依設計就不是機密的 `FIREBASE_API_KEY`。**任何人只要能在專案裡建一個帳號，就能進後台並取得完整寫入權限。**

### 做法
- 新增 `ADMIN_ACCOUNTS` 設定（逗號分隔，UID 或 email 皆可，不分大小寫）
- 拒絕時的訊息與密碼錯誤完全相同，不洩漏「帳號存在但權限不足」
- 留空＝放行但每次登入印警告，避免既有部署更新後登不進去
- `scripts/list_auth_users.py` 用來查自己的 UID，並檢查有無陌生帳號

### 建議的資料庫規則
```json
{
  "rules": {
    ".read": false,
    ".write": false,
    "_libraries": { ".indexOn": ["bind_type", "bind_id"] }
  }
}
```
Admin SDK 不受規則約束，所以全關不影響功能。`.indexOn` 是索引宣告不是權限，兩者可並存。
