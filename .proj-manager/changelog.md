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

*後續變更將自動記錄於此*
