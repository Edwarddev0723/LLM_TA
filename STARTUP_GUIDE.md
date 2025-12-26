# 🚀 AI Math Tutor - 啟動指南

本指南說明如何在 Monorepo 架構下啟動 AI 數學語音助教系統的各個服務。

## 📋 前置檢查

在啟動服務前，請確認已完成以下步驟：

### 1. 安裝依賴

```bash
# Backend 依賴
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Student Frontend 依賴
cd frontend
npm install
cd ..

# Teacher/Parent Portal 依賴
cd apps/teacher-web
npm install
cd ../..
```

### 2. 初始化資料庫

```bash
cd backend
source venv/bin/activate
PYTHONPATH=.. python scripts/init_db.py
cd ..
```

### 3. 安裝 Ollama (可選，用於 LLM 功能)

```bash
# macOS
brew install ollama

# 啟動 Ollama 服務
ollama serve

# 下載模型
ollama pull llama3.2
```

## 🎯 啟動方式

### 方式一：使用啟動腳本 (推薦)

我們提供了三個啟動腳本，讓您輕鬆啟動各個服務：

#### 1. 啟動後端

```bash
./start-backend.sh
```

後端將運行在 `http://localhost:8000`

#### 2. 啟動學生前端

```bash
./start-frontend.sh
```

學生前端將運行在 `http://localhost:5173`

#### 3. 啟動教師/家長入口

```bash
./start-teacher-web.sh
```

教師入口將運行在 `http://localhost:3000`

### 方式二：手動啟動

#### 啟動後端

```bash
cd backend
source venv/bin/activate
PYTHONPATH=.. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 啟動學生前端

```bash
cd frontend
npm run dev
```

#### 啟動教師/家長入口

```bash
cd apps/teacher-web
npm run dev -- --port 3000
```

## 🔍 驗證服務

### 1. 後端健康檢查

```bash
curl http://localhost:8000/api/health
```

預期輸出：
```json
{"status":"healthy"}
```

### 2. 前端連接測試

1. 打開瀏覽器訪問 http://localhost:5173 (學生前端)
2. 打開開發者工具 (F12)
3. 檢查 Console 是否有錯誤
4. 檢查 Network 標籤，確認 API 請求正常

### 3. 教師入口測試

1. 打開瀏覽器訪問 http://localhost:3000 (教師入口)
2. 打開開發者工具 (F12)
3. 檢查 Console 是否有錯誤
4. 檢查 Network 標籤，確認 API 請求正常

## 📊 服務端口總覽

| 服務 | 端口 | URL | 說明 |
|------|------|-----|------|
| Backend API | 8000 | http://localhost:8000 | FastAPI 後端服務 |
| API 文件 | 8000 | http://localhost:8000/docs | Swagger UI |
| 健康檢查 | 8000 | http://localhost:8000/api/health | 後端狀態 |
| 學生前端 | 5173 | http://localhost:5173 | React 學習介面 |
| 教師入口 | 3000 | http://localhost:3000 | Vue 管理介面 |

## 🔧 API 代理配置

兩個前端應用都配置了 Vite 開發代理，自動將 `/api` 請求轉發到後端：

```
前端請求: /api/health
    ↓
Vite Proxy
    ↓
後端: http://localhost:8000/api/health
```

這樣做的好處：
- ✅ 無需配置 CORS
- ✅ 避免跨域問題
- ✅ 開發體驗更流暢
- ✅ 生產環境可通過環境變數配置

## 🐛 常見問題

### 問題 1: 後端啟動失敗

**錯誤**: `ModuleNotFoundError: No module named 'fastapi'`

**解決方案**:
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### 問題 2: 前端無法連接後端

**錯誤**: Console 顯示 `Failed to fetch` 或 `Network Error`

**解決方案**:
1. 確認後端已啟動: `curl http://localhost:8000/api/health`
2. 檢查 Vite proxy 配置 (應該已配置好)
3. 清除瀏覽器緩存並重新載入

### 問題 3: 端口被占用

**錯誤**: `Address already in use`

**解決方案**:
```bash
# 查找占用端口的進程
lsof -i :8000  # 後端
lsof -i :5173  # 學生前端
lsof -i :3000  # 教師入口

# 終止進程
kill -9 <PID>
```

### 問題 4: 資料庫未初始化

**錯誤**: API 返回資料庫錯誤

**解決方案**:
```bash
cd backend
source venv/bin/activate
PYTHONPATH=.. python scripts/init_db.py
```

## 📝 開發建議

### 推薦的啟動順序

1. **先啟動後端** - 確保 API 服務可用
2. **驗證後端** - 使用 curl 測試健康檢查
3. **啟動前端** - 根據需要啟動學生端或教師端
4. **測試連接** - 在瀏覽器中驗證 API 連接

### 多終端機工作流

建議使用 3 個終端機視窗：

```
終端機 1: Backend
終端機 2: Student Frontend
終端機 3: Teacher Portal
```

### 使用 tmux 或 screen

如果您熟悉 tmux 或 screen，可以在單一終端機中管理多個服務：

```bash
# 使用 tmux
tmux new-session -s ai-tutor
# Ctrl+B, C 創建新窗口
# Ctrl+B, N 切換窗口
```

## 🎓 下一步

服務啟動後，您可以：

1. 📖 閱讀 [API 文件](http://localhost:8000/docs)
2. 🧪 執行測試套件 (參見 README.md)
3. 💻 開始開發新功能
4. 📊 查看學習儀表板

## 🆘 需要幫助？

如果遇到問題：

1. 檢查本指南的「常見問題」章節
2. 查看 README.md 的完整文件
3. 檢查 .kiro/specs/ai-math-tutor/ 的規格文件
4. 提交 Issue 到專案 GitHub

---

祝您開發順利！🚀
