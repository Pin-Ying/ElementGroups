# 專案開發上下文

## 專案概述

**專案名稱:** ElementGroups
**建立追蹤時間:** 2026-02-23
**最後更新:** 2026-02-23
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

## 部署方式

**目前:** Docker Compose（前端 8080，後端 8000）
**之前:** Render.com (Procfile)

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
| GET | `/api/elements/:symbol/ability` | 能力數值 + abMax |
| POST | `/api/auth/login` | 登入 |
| POST | `/api/auth/logout` | 登出 |
| POST | `/api/admin/update-db` | 初始化/更新週期表（已有資料則略過）|
| GET/POST | `/api/admin/story` | 故事與圖片管理 |

### 前端頁面
- `HomeView.vue` - 主頁面（週期表 + 分組切換）
- `StoryView.vue` - 元素詳細故事頁面（含登入後 inline 編輯 Modal）
- `AdminView.vue` - 管理員頁面

### 前端元件
- `PeriodicTable.vue` - 週期表格
- `GroupBox.vue` - 分組盒子
- `AbilityChart.vue` - ECharts 雷達圖
- `LoadingSpinner.vue` - 全域 loading overlay

## 環境變數

所有環境變數定義於 `backend/.env.example`，使用 `pydantic-settings` 管理。

必填項目：
- `SECRET_KEY` - Flask Session 密鑰
- `FIREBASE_*` - Firebase Admin SDK 與 Client 金鑰

**已移除:** `DATABASE_URI`（SQLite 已廢棄）

## 開發注意事項

- **Gunicorn workers = 1**：Flask-Login 使用 in-memory `users` dict，多 worker 會導致 session 跨 process 失效（401 問題）
- CORS 已啟用（`supports_credentials=True`）
- Session 有效期 10 分鐘 sliding（`backend/app/__init__.py`），每次 request 自動延長
- 前端 `VITE_API_URL=/api`（`frontend/.env.production`），nginx 代理 `/api` 到後端
- 開發模式：Vite proxy `/api` 到 `localhost:8000`
- Firebase Realtime DB 使用 Spark 免費方案（週期表 + 圖片 base64 約 50 MB，遠低於 1 GB 上限）

## 待辦事項

- [ ] Flask-Login session 改用 Redis 或 server-side store（支援多 worker）
- [ ] StoryView 前端串接 img_data fallback 已實作，如需讓舊圖片也有 base64，需重新上傳

## Auth 相關注意事項

- `logout()` 不加 `@login_required`，避免 session 過期時無法登出（返回 401）
- Realtime DB 根節點同時有故事資料（`{Symbol}/img,description`）和 `periodic_table/` 子樹，迭代時需過濾 `periodic_table` 鍵
- `App.vue` Admin 登入區塊在標題下方（column layout），避免橫排破版

---

*此文檔由 project-manager skill 維護*
