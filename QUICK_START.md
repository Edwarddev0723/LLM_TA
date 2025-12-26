# ⚡ Quick Start - AI Math Tutor Monorepo

## 🎯 目標

將 AI_TA 前端整合進 LLM_TA，形成統一的 Monorepo 架構，並確保前後端能夠正常通信。

## ✅ 已完成的整合工作

### 1. 專案結構
- ✅ `frontend/` - React 學生前端
- ✅ `apps/teacher-web/` - Vue 教師/家長入口
- ✅ `backend/` - FastAPI 後端 (統一 `/api` 前綴)

### 2. API 配置
- ✅ 所有 API 路由使用 `/api` 前綴
- ✅ 健康檢查端點: `GET /api/health`
- ✅ CORS 配置支援多個前端應用

### 3. 開發代理
- ✅ `frontend/vite.config.ts` - 配置 `/api` proxy
- ✅ `apps/teacher-web/vite.config.js` - 配置 `/api` proxy
- ✅ 無需手動處理 CORS

### 4. 啟動腳本
- ✅ `start-backend.sh` - 啟動後端
- ✅ `start-frontend.sh` - 啟動學生前端
- ✅ `start-teacher-web.sh` - 啟動教師入口

## 🚀 立即開始

### 第一次使用 (安裝依賴)

```bash
# 1. 安裝後端依賴
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# 2. 安裝學生前端依賴
cd frontend
npm install
cd ..

# 3. 安裝教師入口依賴
cd apps/teacher-web
npm install
cd ../..

# 4. 初始化資料庫
cd backend
source venv/bin/activate
PYTHONPATH=.. python scripts/init_db.py
cd ..
```

### 日常開發 (啟動服務)

**開啟 3 個終端機視窗：**

```bash
# 終端機 1: 啟動後端
./start-backend.sh

# 終端機 2: 啟動學生前端
./start-frontend.sh

# 終端機 3: 啟動教師入口
./start-teacher-web.sh
```

## 🧪 驗收測試

### 測試 1: 後端健康檢查

```bash
curl http://localhost:8000/api/health
```

**預期輸出:**
```json
{"status":"healthy"}
```

### 測試 2: 前端連接測試

1. 啟動後端和前端
2. 打開瀏覽器訪問:
   - 學生前端: http://localhost:5173
   - 教師入口: http://localhost:3000
3. 打開開發者工具 (F12)
4. 檢查 Console 無 API base URL 錯誤
5. 檢查 Network 標籤，確認 `/api/*` 請求返回 200

### 測試 3: 互動式測試頁面

```bash
# 1. 啟動後端
./start-backend.sh

# 2. 在瀏覽器打開
open test-api-connection.html
# 或直接拖曳到瀏覽器

# 3. 點擊測試按鈕，確認所有測試通過
```

## 📊 服務端口

| 服務 | 端口 | URL | 說明 |
|------|------|-----|------|
| 後端 API | 8000 | http://localhost:8000 | FastAPI |
| API 文件 | 8000 | http://localhost:8000/docs | Swagger UI |
| 健康檢查 | 8000 | http://localhost:8000/api/health | 狀態檢查 |
| 學生前端 | 5173 | http://localhost:5173 | React |
| 教師入口 | 3000 | http://localhost:3000 | Vue |

## 🔍 驗證清單

在提交代碼前，請確認：

- [ ] 後端可以正常啟動
- [ ] `curl http://localhost:8000/api/health` 返回 `{"status":"healthy"}`
- [ ] 學生前端可以訪問，Console 無錯誤
- [ ] 教師入口可以訪問，Console 無錯誤
- [ ] 前端可以成功調用後端 API
- [ ] 沒有 CORS 錯誤
- [ ] 沒有 API base URL 錯誤

## 📚 更多資訊

- **完整文檔**: [README.md](./README.md)
- **啟動指南**: [STARTUP_GUIDE.md](./STARTUP_GUIDE.md)
- **整合總結**: [INTEGRATION_SUMMARY.md](./INTEGRATION_SUMMARY.md)

## 🆘 遇到問題？

### 問題: 後端啟動失敗
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### 問題: 前端無法連接後端
1. 確認後端已啟動: `curl http://localhost:8000/api/health`
2. 檢查瀏覽器 Console 和 Network 標籤
3. 確認 Vite proxy 配置正確

### 問題: 端口被占用
```bash
# 查找占用端口的進程
lsof -i :8000  # 後端
lsof -i :5173  # 學生前端
lsof -i :3000  # 教師入口

# 終止進程
kill -9 <PID>
```

## 🎉 完成！

所有整合工作已完成，系統可以正常運行。開始開發吧！🚀
