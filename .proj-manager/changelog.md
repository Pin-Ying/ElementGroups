# 專案變更日誌

本檔案記錄所有由 project-manager skill 協助進行的專案修改。

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
