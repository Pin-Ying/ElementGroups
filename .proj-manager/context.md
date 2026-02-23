# 專案開發上下文

## 專案概述

**專案名稱:** ElementGroups
**建立追蹤時間:** 2026-02-23
**專案類型:** Fullstack Web Application
**主要技術:** Python Flask (後端) + Vue 3 + Vite (前端)

## 專案描述

元素週期表分組應用，提供元素資訊查詢、分組管理與視覺化功能。

- 後端：Flask REST API，SQLite 資料庫，Firebase Authentication
- 前端：Vue 3 SPA，ECharts 視覺化，Vue Router 路由

## 服務架構

```
[Browser]
    |
    v
[Frontend Container: Nginx:80]
    |-- 靜態資源 (Vue build)
    |-- /api/* --> 反向代理
    |
    v
[Backend Container: Gunicorn:8000]
    |
    |-- SQLite DB (volume 掛載)
    |-- Firebase Admin SDK
    |-- Pyrebase4 (Firebase Client)
```

## 部署方式

**目前:** Docker Compose
**之前:** Render.com (Procfile: `web: python run.py`)

啟動指令:
```bash
# 複製環境變數
cp backend/.env.example backend/.env
# 填入實際的 Firebase 金鑰後執行:
docker-compose up --build
```

## 路由說明

### 後端路由
- `backend/app/routes/public.py` - 公開 API (不需登入)
- `backend/app/routes/admin.py` - 管理員 API (需登入)

### 前端頁面
- `HomeView.vue` - 主頁面 (元素週期表)
- `StoryView.vue` - 故事頁面
- `AdminView.vue` - 管理員頁面

## 環境變數

所有環境變數定義於 `backend/.env.example`，使用 `pydantic-settings` 管理。

必填項目：
- `SECRET_KEY` - Flask Session 密鑰
- Firebase Admin SDK 相關金鑰 (FIREBASE_*)
- Firebase Client 相關設定

## 開發注意事項

- SQLite DB 路徑: `backend/elementGroups.db`，Docker 中透過 volume 掛載持久化
- CORS 已啟用 (`supports_credentials=True`)
- Session 有效期 5 分鐘 (可在 `backend/app/__init__.py` 調整)
- 前端 `/api` 路徑在開發時代理到 `localhost:8000`，生產時由 Nginx 代理到 backend container

## 待辦事項

- [ ] 補充 API 文檔
- [ ] 完善測試覆蓋率

---

*此文檔由 project-manager skill 自動生成，可手動編輯以補充資訊*
