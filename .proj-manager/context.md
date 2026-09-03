# 專案開發上下文

## 專案概述

**專案名稱:** ElementGroups
**建立追蹤時間:** 2026-02-23
**最後更新:** 2026-08-10
**專案類型:** Fullstack Web Application
**主要技術:** Python Flask (後端) + Vue 3 + Vite (前端)

## 專案描述

元素週期表分組應用，提供元素資訊查詢、分組管理與視覺化功能。

- 後端：Flask REST API，Firebase Realtime Database（週期表 + 故事資料），Firebase Auth
- 前端：Vue 3 SPA，ECharts 視覺化，Vue Router 路由

## 服務架構

```
[Browser]
    |
    v
[Frontend Container: Nginx:8080]
    |-- 靜態資源 (Vue build)
    |-- /api/* --> 反向代理
    |
    v
[Backend Container: Gunicorn:8000 (1 worker)]
    |
    |-- Firebase Realtime DB (periodic_table/, 故事資料)
    |-- Firebase Storage (元素圖片)
    |-- Firebase Admin SDK
    |-- Pyrebase4 (Firebase Client 認證)
```

## 資料儲存

| 資料 | 儲存位置 | 說明 |
|------|---------|------|
| 週期表 118 筆 | Realtime DB `periodic_table/{Symbol}` | 由 `POST /api/admin/update-db` 從 PubChem 爬取 |
| 故事 / 圖片 URL | Realtime DB `{Symbol}/img, description` | 管理員上傳 |
| 圖片 base64 備援 | Realtime DB `{Symbol}/img_data` | Storage 不可用時的 fallback |
| 元素圖片檔案 | Firebase Storage `static/img/{Symbol}.JPG` | |
| 完成度摘要 | Realtime DB `_completion/{Symbol}` | `{story, image, updated_at}`，避免首頁掃全庫 |
| 點閱統計 | Realtime DB `_stats/{Symbol}/views` | 熱門元素排序用 |
| 其他樣貌圖庫 | Realtime DB `_gallery/{Symbol}[]` | `{img_data, caption}`，上限 6 張 |
| 網站設定 | Realtime DB `_site_settings` | 文案、背景圖、圖鑑外框 |
| 社群連結 | Realtime DB `_creator_links` | 描述、頭像形狀、連結清單 |
| AI 用量 | Realtime DB `_ai_usage/{YYYY-MM-DD}` | 每日呼叫次數 |
| 基本粒子形象 | Realtime DB `_particles/{slug}` | 電子、質子、中子⋯可自由新增；同時是繞行粒子的來源 |
| 元素分層素材 | Realtime DB `_layers/{Symbol}` | `{nucleus, name_img}` base64；繞行粒子不存這裡 |
| 全站繞行粒子 | Realtime DB `_orbit_particle` | 指向 `_particles/{slug}` |
| 全站運動方式 | Realtime DB `_motion` | `orbit` / `free` / `static` |
| 內建頁面文案 | Realtime DB `_page_meta/{key}` | 只存被改過的欄位，讀不到退回程式內建預設 |

## 部署方式

**目前:** Render.com — 前端 static site（elementgroups-frontend）+ 後端 web service（elementtable），
同一個 repo，push 後兩者皆自動重新部署。
**本地開發:** Docker Compose（前端 8080，後端 8000），需 `backend/.env` 的 Firebase 憑證。
對外 port 可用專案根目錄的 `.env` 覆寫（`FRONTEND_PORT` / `BACKEND_PORT`），
本機已有服務佔用時不必改 `docker-compose.yml`。

> `backend/.env.example` 的 Firebase 私鑰是佔位字串，直接複製會讓憑證初始化失敗
> （`MalformedFraming`）、worker 開不起來。要跑真後端必須填入真實的 service account。

> 注意：production 的 `VITE_API_URL` 由 Render 環境變數注入為後端絕對網址，
> 會覆蓋 repo 內 `frontend/.env.production` 的 `/api`。

啟動指令:
```bash
cp backend/.env.example backend/.env   # 填入 Firebase 金鑰
docker-compose up --build --quiet-pull  # build 時加 --quiet
```

初始化週期表資料（首次啟動後執行）:
```
POST /api/auth/login       # 管理員登入
POST /api/admin/update-db  # 爬取並寫入 118 筆元素
```

## 路由說明

### 後端路由
| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/elements` | 取得所有元素 |
| POST | `/api/groups` | 分組資料（cp / vs）|
| GET | `/api/elements/:symbol` | 元素詳細資料（含 img_data fallback）|
| GET | `/api/elements/:symbol/img` | 圖片 proxy（從 Storage 下載，fallback Electron.JPG，Cache-Control 1 day）|
| GET | `/api/elements/:symbol/ability` | 能力數值 + abMax |
| POST | `/api/auth/login` | 登入 |
| POST | `/api/auth/logout` | 登出 |
| GET | `/api/auth/status` | 查詢目前登入狀態（`{"loggedIn": bool}`）|
| POST | `/api/admin/update-db` | 初始化/更新週期表（已有資料則略過）|
| GET/POST | `/api/admin/story` | 故事與圖片管理 |
| POST | `/api/admin/backfill-img-data` | 補齊舊圖片的 base64 img_data（有 img 無 img_data 者）|
| GET | `/api/elements/completion` | 各元素的故事/圖片完成狀態（讀 `_completion` 摘要）|
| GET | `/api/elements/recent` | 最近更新的元素（依 `updated_at`）|
| GET | `/api/elements/popular` | 熱門元素（依 `_stats` 點閱數）|
| POST | `/api/elements/:symbol/view` | 累加元素頁點閱 |
| GET | `/api/elements/:symbol/gallery` | 元素的「其他樣貌」圖庫 |
| GET | `/api/site-settings` | 網站文案、背景圖、圖鑑外框設定 |
| GET | `/api/creator-links` | 社群連結（含描述、頭像形狀）|
| GET | `/api/ai/status` | AI 協助是否啟用（公開，便於部署後確認環境變數）|
| POST | `/api/admin/rebuild-completion` | 重建完成度摘要 |
| GET/POST | `/api/admin/site-settings` | 網站設定（POST 為 multipart，含背景圖與外框圖）|
| GET/POST | `/api/admin/elements/:symbol/gallery` | 其他樣貌圖庫（上限 6 張）|
| POST | `/api/admin/story-suggest` | AI 產生故事建議 |

### 前端頁面
- `HomeView.vue` - 主頁面（分組下拉 + 檢視樣式 + 完成度 + 最近更新／熱門）
- `StoryView.vue` - 元素詳細頁（圖鑑外框、數值條、基本資料、其他樣貌、元素滾輪）
- `AdminView.vue` - 管理員頁面（側邊選單五個區塊）
- `LinksView.vue` - 社群連結頁 `/links`
- `GuideView.vue` - 元素說明書 `/guide`

### 前端元件
- `PeriodicTableGrid.vue` - 標準週期表格排版（18 欄）
- `ElementIconGrid.vue` - 大／小圖示檢視（取代已移除的 PeriodicTable.vue）
- `ElementListView.vue` - 詳細清單檢視
- `GroupBox.vue` - 分組容器，依 viewStyle 渲染對應樣式
- `ElementHighlights.vue` - 最近更新／熱門元素卡片列
- `CompletionDots.vue` - 完成度圓點
- `AbilityBars.vue` - CPK 色數值條（Stats 預設視圖）
- `AbilityChart.vue` - ECharts 雷達圖（第二視圖）
- `ElementProfile.vue` - 基本資料區
- `PokedexFrame.vue` - 圖鑑外框（四款內建 + 自訂 PNG）
- `ElementGallery.vue` - 其他樣貌圖庫與放大檢視
- `ImageCropper.vue` - 圖片裁切
- `SocialLink.vue` - 社群連結膠囊（頁尾與 /links 共用）
- `SiteFooter.vue` - 全站頁尾
- `LoadingSpinner.vue` - 全域 loading overlay

## 環境變數

所有環境變數定義於 `backend/.env.example`，使用 `pydantic-settings` 管理。

必填項目：
- `SECRET_KEY` - Flask Session 密鑰
- `FIREBASE_*` - Firebase Admin SDK 與 Client 金鑰

選填項目：
- `FIREBASE_STORAGE_ENABLED` - 預設 false，只用 Realtime DB base64
- `AI_PROVIDER` / `AI_API_KEY` / `AI_MODEL` / `AI_DAILY_LIMIT` / `AI_MAX_OUTPUT_TOKENS` - AI 故事協助，未設 key 則整個功能不啟用
- `VITE_SITE_URL`（前端）- SEO 的 `og:url` 用，未設定會省略該標籤

**已移除:** `DATABASE_URI`（SQLite 已廢棄）

## 開發注意事項

- **Gunicorn workers = 1**：Flask-Login 使用 in-memory `users` dict，多 worker 會導致 session 跨 process 失效（401 問題）
- CORS 已啟用（`supports_credentials=True`）
- Session 有效期 10 分鐘 sliding（`backend/app/__init__.py`），每次 request 自動延長
- 前端 `VITE_API_URL=/api`（`frontend/.env.production`），nginx 代理 `/api` 到後端
- 開發模式：Vite proxy `/api` 到 `localhost:8000`
- Firebase Realtime DB 使用 Spark 免費方案（週期表 + 圖片 base64 約 50 MB，遠低於 1 GB 上限）

## 待辦事項

- [x] 完成前端 table 版面設計（PeriodicTableGrid.vue，CSS Grid 18×10）
- [x] 隱藏 Firebase Storage 圖片 URL，改由後端提供圖片 proxy API（`/api/elements/:symbol/img`），避免直接暴露 Storage URL
- [x] 優化整體前端介面（宇宙主題 UI 全面實作）
- [ ] Flask-Login session 改用 Redis 或 server-side store（支援多 worker）
- [x] StoryView 前端串接 img_data fallback 已實作；舊圖片可透過 Admin「Backfill img_data」一鍵補齊
- [x] 元素完成度標示（Admin 下拉 + 首頁週期表圓點）
- [x] 圖片上傳壓縮與裁切
- [x] 網站設定與 SEO 標籤 build 時注入
- [x] AI 故事協助（Gemini）
- [x] 首頁分組下拉與三種檢視樣式
- [x] 元素頁圖鑑化（數值條、基本資料、外框、其他樣貌、元素滾輪）
- [x] 元素說明書頁 `/guide`
- [ ] 頁面管理 CMS（issue #10：Markdown 編輯器、前台左側導覽欄、草稿狀態、元素故事草稿）
- [ ] 分子區塊（issue #11：PubChem 化合物 API 已驗證可用，等需求確認）
- [ ] AI 故事生成的截斷修正尚未實測（模型為 gemini-3.5-flash，屬思考型模型）
- [ ] 若圖片量成長，評估啟用 Firebase Storage（需 Blaze 方案，程式碼已支援切換）

## Auth 相關注意事項

- `logout()` 不加 `@login_required`，避免 session 過期時無法登出（返回 401）
- Realtime DB 根節點同時有故事資料（`{Symbol}/img,description`）和 `periodic_table/` 子樹，迭代時需過濾 `periodic_table` 鍵
- `App.vue` Admin 登入區塊在標題下方（column layout），避免橫排破版
- **Gunicorn timeout**：backfill-img-data 使用 `ThreadPoolExecutor(max_workers=10)` 並行下載，避免 N 次串行請求超過 30s worker timeout
- **元素 API**：`/api/elements` 與 `/api/groups` 回傳包含 `Name` 欄位（前端顯示元素全名用）
- **PeriodicTableGrid 斷點**：動態計算格子寬（`(viewport - 17×3) / 18 < 70px`）決定切換分組備援，不使用固定像素
- **Auth 狀態唯一來源**：`store/auth.js` 的 `authState`。所有元件（App、AdminView、StoryView）都使用同一個 reactive 物件，嚴禁在元件內建立本地 `loggedIn` 狀態
- `initAuth()`：App 掛載時呼叫，透過 `GET /api/auth/status` 恢復頁面重整後的登入狀態；只允許設為 true，不覆蓋已登入狀態（防 race condition）
- `AdminView` 在 `mounted()` 若已登入會自動載入 story 資料
- **axios 401 interceptor**：在 `App.vue` created() 中設置，任何 401 response 自動同步 `authState.loggedIn = false`
- **`login_manager.session_protection = None`**：停用 Flask-Login IP/UA hash 識別符檢查，避免 Windows Docker 環境中 IPv4/IPv6 切換導致 session 失效

## 部署與環境的陷阱（實際踩過）

- **前端不可寫死相對 `/api`**：production 的前端是 Render static site，`/api/*` 會被
  SPA fallback（`/* → /index.html`）吞掉並回傳 index.html。非 axios 場合
  （`<img src>` 等）一律使用 `api/index.js` 匯出的 `apiBase`
- **`frontend/public/_redirects` 在 Render 上沒有作用**：那是 Netlify 的格式，Render
  不支援（官方只有 dashboard 與 `render.yaml` 的 `routes`，社群仍在提功能請求）。
  線上的 SPA fallback 來自 routes，不是這個檔案——先前的記錄歸因錯了。改路由規則
  時不要動它，動了也不會生效
- **必須有 `.dockerignore`**：沒有的話 `COPY . .` 會把本地 `node_modules` 複製進 image，
  覆蓋掉 `npm install` 裝好的依賴；若本地檔案缺少執行位元，build 會以 `Permission denied` 失敗
- **SEO 靠 build 時注入**：`index.html` 是 build-time 靜態檔，JS 設定的 meta tag 爬蟲讀不到
  （Facebook / LINE / Twitter 完全不執行 JS）。`frontend/vite-plugin-seo.js` 在打包階段向後端
  抓一次設定並注入 title/description/og/twitter。**後台改完文案需重新部署一次爬蟲才看得到**
- **build 時取不到後端資料一律不可靜默略過**（issue #45，代價是整站三個月沒被索引）：
  後端也在 Render 免費方案上、會休眠，build 撞上冷啟動時請求就逾時。三個 plugin 原本各自
  `catch { return null }`＋`console.warn`＋`return`，**exit code 仍是 0**，於是 118 個元素頁
  的預渲染整批被跳過而沒人知道。現在共用 `frontend/build-fetch.js`：重試 3 次、
  `buildCommand` 先 curl 預熱後端，且 Render 上帶 `PRERENDER_REQUIRED=1` 讓取不到資料時
  **部署直接失敗**。CI 刻意不設這個變數——它要走 fallback 路徑確認退路沒被改壞
- **Render 的 rewrite 不會蓋掉真實存在的檔案**：`/* → /index.html` 只在該路徑沒有資源時生效，
  且 `stroy/H/index.html` 同時對應 `/stroy/H` 與 `/stroy/H/`，所以預渲染出來的檔案送得出去。
  也因為兩種形式都通，canonical 一律寫不帶尾斜線的那個
- **本機無 Firebase 憑證時**：`app/firebase.py` 在 import 階段就初始化 SDK，後端起不來。
  只能驗證編譯（`py_compile` / `vite build`），完整驗證需靠部署或代理到 production 後端
- **working tree 行尾**：本地 checkout 為 CRLF、repo 內為 LF，且無 `.gitattributes`。
  commit 前需對改動檔案轉 LF，否則 diff 會夾帶整份檔案的行尾變更

## 資料安全注意事項

- **Firebase 讀寫不可吞例外**：`upload_fdb` / `show_fdb` 的錯誤一律往上拋。
  歷史上這兩個函式吞掉例外，導致寫入失敗仍回報成功、讀取失敗被當成「沒有資料」，
  進而在寫回時用空字串覆蓋既有圖片（見 mod-002）
- **部分更新用 `update`，不要用 `set`**：`upload_fdb` 是整筆覆寫。只改故事時應直接
  `fdb.child(symbol).update({...})`，不要為了保留舊圖而先讀回整個 DB 再覆寫
- **Realtime DB 的陣列**：有空洞時會回傳以索引為 key 的 dict，讀取端必須正規化
  （見 `app/gallery.py` 的 `normalize_gallery`）

## 前端版面注意事項

- **`overflow-x: auto` 會連帶裁切垂直方向**：依 CSS 規範，一軸非 `visible` 時另一軸的
  `visible` 會變成 `auto`。`.pt-wrapper` 因此切掉了 hover 放大（scale 1.18）溢出的部分，
  容器四周需預留空間
- **用 `offsetLeft` 計算捲動位置前，容器必須是定位祖先**：`.nav-wheel` 未設 `position`
  時 `offsetParent` 會是 `body`，取到的座標與 `scrollLeft` 基準不同（實測偏移 182px）
- **介面字型沒有 emoji 字符**：Space Grotesk 下 📷 ✨ 等會渲染成空白方框，一律改用
  幾何符號（✓ ▣ ⚙ ⚯ ⚒ ✧）或 CSS 繪製
- **圖片量與 Realtime DB**：base64 編碼膨脹約 33%，且讀取是整個節點一起拉。
  圖庫另存 `_gallery` 節點、完成度另存 `_completion` 摘要，都是為了不讓列表頁
  的查詢連帶拉下圖片

---

*此文檔由 project-manager skill 維護*

## 開發注意事項（2026-08-10 補充）

### 文案與內容的覆寫原則
- 附加頁面的標題與零碎文案一律走 `_page_meta` 覆寫層（`utils/pageMeta.js` 定義欄位與預設值），**不要寫死在元件裡**；新增附加頁面時後端 `META_KEYS` 補 key、前端補欄位定義即可
- 內建頁面（guide/links）的模板更新是 opt-in：使用者按「載入最新內建模板」才會換，部署不得覆蓋 DB 內容

### 表單與手機
- 全站表單元件在 ≤760px 一律 16px（iOS 聚焦縮放）；scoped class 選擇器會蓋過全域規則，新元件需自帶斷點

### 後台載入
- AdminView 資料載入走 `bootstrap()`（含 watch authState.loggedIn）；新增後台資料來源時把 loader 掛進 `loadAll()`，不要在 mounted 直接呼叫

### 批次修改程式碼的教訓
- 以字串替換批改檔案時，每一段替換都要 assert 命中次數，否則錨點沒對上會靜默 no-op（曾造成樣式全缺與 /particles 路由漏掛）
- 建置後用 bundle 字串掃描防呆：預期出現的關鍵字串 grep 一次

### 憑證
- 對話／部署流程中出現過 GitHub token 與 Gemini API key 明碼，開發告一段落時提醒使用者輪替

---

## 開發注意事項（2026-09-01 補充）

### 登入機制（feature-019、feature-020）

後台有兩條登入路徑，由兩個環境變數控制：

| `GOOGLE_LOGIN_ENABLED` | `PASSWORD_LOGIN_ENABLED` | 頁尾（訪客） | `/admin`（站長） |
|---|---|---|---|
| false | 留空 | 帳密表單 | 帳密表單 |
| **true** | **留空** | **只有 Google** | **只有 Google** |
| true | true | 只有 Google | Google ＋「使用其他方式登入」→ 帳密 |
| false | false | 沒有可用的登入方式 | 沒有可用的登入方式 |

- `PASSWORD_LOGIN_ENABLED` 留空＝與 Google 連動（開 Google 就關帳密）；**明確設 `true` 是逃生門**，Google 出狀況時不必改程式或重新部署
- **擋在後端 `auth.login()`，不是只藏前端表單**。`/api/auth/login` 是公開端點，繞過畫面直接打就行
- 頁尾與 `/admin` 分工不同：頁尾面向一般訪客保持單純，`/admin` 是站長自己的頁面、保留後路。改其中一處時記得另一處
- **`ADMIN_ACCOUNTS` 是唯一的授權關卡**。通過 Google 驗證不等於能進後台——Google 只證明 email 擁有權。沒設定的話，Google 登入比帳密登入更糟（連註冊那一步都省了）

### Firebase 的兩個坑（都實際踩過）

**1. Google 登入會移除同 email 底下「未驗證」的密碼憑證。**

Firebase 的防帳號劫持機制：聯合登入的 email 已驗證，而密碼是誰設的無從證明，所以連結帳號時會把密碼憑證拿掉。實際後果是**每次用 Google 登入都可能把帳密這條後路消滅掉**，而且沒有任何通知，等真的需要備援時才發現。

- 症狀：帳密登入回 401「Incorrect email or password」，但密碼並沒有記錯
- 診斷：後台維護工具 →「登入帳號」→ 看 `providers`。**沒有 `密碼` 就是被移除了**，這是唯一看得出來的地方
- 根治：把該帳號的 email 標記為已驗證（同一個工具就有按鈕）。已驗證的 email 不會再被移除
- 為什麼不用驗證信：企業信箱常整封擋掉，而 Firebase 主控台**沒有**「標記為已驗證」或「發送驗證信」的按鈕（只有重設密碼、停用、刪除）。所以改用 Admin SDK 直接設定

**2. 授權網域要填「前端」網域。**

Authentication → Settings → 授權網域要加的是 `elementgroups-frontend.onrender.com`，不是後端的 `elementtable.onrender.com`。Google 登入的彈出視窗由瀏覽器上的頁面發起，Firebase 檢查的是網址列的網域；後端只收前端拿到的 ID token，全程不經手。填錯會得到 `auth/unauthorized-domain`，前端已把它翻成看得懂的訊息。

> 順帶一提，自訂寄件網域（Templates 的 From）需要該網域的 DNS 權限，而 `onrender.com` 的 DNS 不在我們手上——與 mod-022 的 GSC 網域驗證是同一個障礙。寄件者名稱與回覆地址則可自由設定。

### 建置可重現性（feature-017）

- `backend/requirements.txt` **連間接依賴一起釘死**（67 筆）。更新方式寫在檔案開頭：用 `python:3.11-slim`（與 Dockerfile 同一個 base image）跑 `pip freeze`
- 前端一律 `npm ci`（Dockerfile 與 `render.yaml` 都是），不要改回 `npm install`——那會讓 `package-lock.json` 形同虛設
- CI 有兩個防退化檢查會擋：**requirements 出現沒有 `==` 的行**、**CRLF 進版控**
- 已驗證：Render 部署後的 CSS hash 與本機 `npm ci` 產物一致；pandas 2.x→3.0.5 後 `/api/groups` 與 `/api/elements/:symbol/ability` 的回應與升級前逐位元組相同

### 觸控裝置

- **iOS Safari 對非輸入元素的 `dblclick` 不可靠**，iPad 上實測完全不觸發。要「點兩下」就自己用 `click` 記時間戳比對（見 `AdminLogin.vue` 的 `handleTrigger`，450ms）
- `touch-action: manipulation` 仍要留，但它的作用是「停用雙擊縮放」與「去掉 iOS 約 300ms 的 click 延遲」——**不是**讓 `dblclick` 能運作。當初混為一談才寫出那個 bug
- 教訓：只在桌面驗證就送出的 UI 改動，觸控裝置要另外確認

### 分子分類（feature-018）

- 分類軸是**組成元素的金屬性**，不是有機／無機。後者的邊界是慣例問題（CO₂ 含碳卻歸無機、碳酸鹽也是），要人工維護例外表；金屬性查表就有答案
- 對照表在 `frontend/src/utils/moleculeCategory.js`，取自週期表 `GroupBlock`，照 `data/elementSymbols.js` 的做法寫成靜態表——**不要改成打 API**，前台分類是即時算的
- **後台手填的 `category` 永遠優先**，沒填才自動判斷。所以既有資料不必回填，規則改進會立刻全站生效
- 公開的 `/api/molecules` slim 投影必須帶 `category`，否則前台拿不到手動覆寫
