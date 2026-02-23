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

*後續變更將自動記錄於此*
