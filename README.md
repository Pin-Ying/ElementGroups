# ElementGroups

元素週期表分組應用，支援依化學性質（Chemical Properties）與價電子層（Valence Shell）分組顯示，並提供各元素詳細資料與故事介紹。

## 技術架構

| 層級 | 技術 |
|------|------|
| 前端 | Vue 3 + Vite + ECharts + Vue Router |
| 後端 | Python Flask + Gunicorn |
| 資料庫 | Firebase Realtime Database（週期表資料 + 故事資料） |
| 認證 | Firebase Auth（Pyrebase） |
| 儲存 | Firebase Storage（元素圖片，含 Realtime DB base64 備援） |

## 快速啟動

### 環境需求

- Docker + Docker Compose

### 設定步驟

```bash
# 1. 複製環境變數範本
cp backend/.env.example backend/.env

# 2. 填入 Firebase 相關金鑰（見下方說明）
vim backend/.env

# 3. 啟動服務
docker-compose up --build
```

服務啟動後：
- 前端：http://localhost:8080
- 後端 API：http://localhost:8000

### 環境變數說明（`backend/.env`）

```env
# Flask
SECRET_KEY=          # 任意隨機字串

# Firebase Admin SDK（Service Account）
FIREBASE_PROJECT_ID=
FIREBASE_PRIVATE_KEY_ID=
FIREBASE_PRIVATE_KEY=
FIREBASE_CLIENT_EMAIL=
FIREBASE_CLIENT_ID=
FIREBASE_STORAGE_BUCKET=
FIREBASE_DATABASE_URL=

# Firebase Client（Pyrebase）
FIREBASE_API_KEY=
FIREBASE_AUTH_DOMAIN=
FIREBASE_MESSAGING_SENDER_ID=
FIREBASE_APP_ID=
FIREBASE_MEASUREMENT_ID=
```

## 初始化資料

服務啟動後，需登入 Admin 並初始化週期表資料：

```
POST /api/auth/login        # 登入
POST /api/admin/update-db   # 從 PubChem 爬取 118 筆元素資料寫入 Realtime DB
                            # 若資料已存在會自動略過
```

## API 端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/elements` | 取得所有元素（AtomicNumber / Symbol / CPKHexColor）|
| POST | `/api/groups` | 依分組類型回傳分組結果（`cp` / `vs`）|
| GET | `/api/elements/:symbol` | 取得元素詳細資料（含前後元素、故事、圖片）|
| GET | `/api/elements/:symbol/ability` | 取得元素能力數值（含全域最大值）|
| POST | `/api/auth/login` | 登入 |
| POST | `/api/auth/logout` | 登出 |
| POST | `/api/admin/update-db` | 初始化/更新週期表資料 |
| GET/POST | `/api/admin/story` | 取得/更新元素故事與圖片 |
