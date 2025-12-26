# 🎓 AI 數學語音助教系統

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/TypeScript-5.9+-blue.svg" alt="TypeScript">
  <img src="https://img.shields.io/badge/FastAPI-0.104+-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-19.2+-61DAFB.svg" alt="React">
  <img src="https://img.shields.io/badge/Vue-3.5+-4FC08D.svg" alt="Vue">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

一個基於費曼學習法的國中數學 AI 語音助教系統，結合本地端 LLM (Ollama)、RAG、ASR (Whisper) 及有限狀態機 (FSM) 技術，提供即時語音互動式數學學習體驗。本專案採用 Monorepo 架構，整合學生端 (React) 與教師/家長端 (Vue) 前端應用。

> 🚀 **快速開始**: 查看 [QUICK_START.md](./QUICK_START.md) 立即啟動系統！

## ✨ 功能特色

### 🎯 核心功能

- **語音互動學習**：透過 Whisper ASR 實現即時語音轉文字，支援數學符號口語轉換
- **蘇格拉底式引導**：採用五階段引導循環 (FSM)，不直接給答案，引導學生自主思考
- **智慧提示系統**：三層級漸進式提示 (方向暗示 → 關鍵步驟 → 解法框架)
- **RAG 知識檢索**：從知識圖譜與題庫中檢索相關內容，增強 LLM 回應品質
- **錯題自動歸檔**：自動記錄錯題並標籤化，支援錯題重述與變題測試

### 📊 學習分析

- **即時學習指標**：WPM (每分鐘字數)、停頓比例、提示依賴度、概念覆蓋率
- **弱點熱力圖**：基於知識圖譜的掌握度視覺化 (紅黃綠燈)
- **學習歷程追蹤**：完整記錄對話歷史與學習進度

### 🔒 隱私與效能

- **本地端部署**：所有 AI 模型運行於本地 MacBook，確保學生隱私
- **低延遲體驗**：ASR 轉錄延遲 < 1 秒，LLM 首字生成 < 5 秒

## 🏗️ 系統架構

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend Applications                         │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐ │
│  │  Student Frontend    │  │  Teacher/Parent Web Portal       │ │
│  │  (React + TypeScript)│  │  (Vue 3 + PrimeVue)              │ │
│  │  frontend/           │  │  apps/teacher-web/               │ │
│  └──────────────────────┘  └──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │ REST API (/api)
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                           │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    語音處理子系統                            ││
│  │  ┌──────────────┐  ┌────────────────────┐                   ││
│  │  │ ASR Module   │  │ 數學符號後處理器   │                   ││
│  │  │ (Whisper)    │  │                    │                   ││
│  │  └──────────────┘  └────────────────────┘                   ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    對話管控子系統                            ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       ││
│  │  │ FSM 控制器   │  │ 對話引擎     │  │ Prompt 建構器│       ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘       ││
│  │  ┌──────────────┐  ┌──────────────┐                         ││
│  │  │ 提示控制器   │  │ LLM Client   │                         ││
│  │  │              │  │ (Ollama)     │                         ││
│  │  └──────────────┘  └──────────────┘                         ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    知識檢索子系統                            ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       ││
│  │  │ RAG Module   │  │ 知識圖譜     │  │ 題庫管理器   │       ││
│  │  │ (ChromaDB)   │  │              │  │              │       ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘       ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    數據分析子系統                            ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       ││
│  │  │ 指標計算器   │  │ 錯題本管理器 │  │ 會話管理器   │       ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘       ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer (SQLite)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │ 知識圖譜 │  │ 題庫     │  │ 錯題本   │  │ 學習歷程        │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 專案結構 (Monorepo)

```
ai-math-tutor/
├── backend/                    # Python FastAPI 後端
│   ├── app/
│   │   └── main.py            # FastAPI 應用程式入口
│   ├── models/                 # 資料模型
│   ├── services/              # 業務邏輯服務
│   ├── routers/               # API 路由 (統一 /api 前綴)
│   ├── tests/                 # 測試檔案
│   ├── pyproject.toml         # Python 專案設定
│   └── requirements.txt       # Python 依賴
│
├── frontend/                   # React TypeScript 學生前端
│   ├── src/
│   │   ├── api/               # API 客戶端
│   │   ├── components/        # React 元件
│   │   ├── pages/             # 頁面元件
│   │   ├── hooks/             # 自訂 Hooks
│   │   └── types/             # TypeScript 型別定義
│   ├── package.json           # Node.js 依賴
│   └── vite.config.ts         # Vite 設定 (含 /api proxy)
│
├── apps/
│   └── teacher-web/           # Vue 3 教師/家長入口
│       ├── src/
│       │   ├── api/           # API 配置
│       │   ├── components/    # Vue 元件
│       │   ├── views/         # 頁面視圖
│       │   └── stores/        # Pinia 狀態管理
│       ├── package.json       # Node.js 依賴
│       └── vite.config.js     # Vite 設定 (含 /api proxy)
│
└── .kiro/specs/               # 規格文件
    └── ai-math-tutor/
        ├── requirements.md    # 需求文件
        ├── design.md          # 設計文件
        └── tasks.md           # 實作任務清單
```

## 🚀 快速開始

### 系統需求

- **作業系統**：macOS (Apple Silicon 建議)
- **Python**：3.10+
- **Node.js**：18+
- **記憶體**：16GB+ (建議 32GB 以運行本地 LLM)

### 安裝步驟

#### 1. 克隆專案

```bash
git clone https://github.com/your-username/ai-math-tutor.git
cd ai-math-tutor
```

#### 2. 安裝 Backend 依賴

```bash
cd backend

# 建立虛擬環境
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 安裝依賴
pip install -r requirements.txt

# 安裝開發依賴 (測試用)
pip install -e ".[dev]"
```

#### 3. 安裝 Frontend 依賴

```bash
# 學生前端 (React)
cd frontend
npm install

# 教師/家長入口 (Vue)
cd ../apps/teacher-web
npm install
```

#### 4. 安裝 Ollama (本地 LLM)

```bash
# macOS
brew install ollama

# 啟動 Ollama 服務
ollama serve

# 下載模型 (另開終端機)
ollama pull llama3.2  # 或其他支援的模型
```

#### 5. 初始化資料庫

```bash
cd backend
PYTHONPATH=.. python scripts/init_db.py
```

這會建立 SQLite 資料庫並插入範例資料。

## 🚀 啟動服務

> 💡 **提示**: 詳細的啟動指南請參閱 [STARTUP_GUIDE.md](./STARTUP_GUIDE.md)

### 快速啟動 (使用腳本)

```bash
# 1. 啟動後端
./start-backend.sh

# 2. 啟動學生前端 (新終端機)
./start-frontend.sh

# 3. 啟動教師入口 (新終端機，可選)
./start-teacher-web.sh
```

### 手動啟動

#### 啟動 Backend

```bash
cd backend
source venv/bin/activate  # 啟動虛擬環境
PYTHONPATH=.. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

後端將運行在 `http://localhost:8000`

#### 啟動學生前端 (React)

```bash
cd frontend
npm run dev
```

學生前端將運行在 `http://localhost:5173`

#### 啟動教師/家長入口 (Vue)

```bash
cd apps/teacher-web
npm run dev
```

教師入口將運行在 `http://localhost:5173` (如果 frontend 未運行)

**注意**：如果要同時運行兩個前端，需要修改其中一個的端口：

```bash
# 在 apps/teacher-web 目錄
npm run dev -- --port 3000
```

### 存取應用程式

| 服務 | URL | 說明 |
|------|-----|------|
| Backend API | http://localhost:8000 | FastAPI 後端服務 |
| API 文件 | http://localhost:8000/docs | Swagger UI 互動式 API 文件 |
| 健康檢查 | http://localhost:8000/api/health | 後端健康狀態檢查 |
| 學生前端 | http://localhost:5173 | React 學生學習介面 |
| 教師入口 | http://localhost:3000 | Vue 教師/家長管理介面 |

### API 前綴說明

所有 API 端點統一使用 `/api` 前綴：

- ✅ `GET /api/health` - 健康檢查
- ✅ `GET /api/questions` - 題目列表
- ✅ `POST /api/sessions` - 開始會話
- ✅ `GET /api/errors` - 錯題列表
- ✅ `GET /api/dashboard/metrics` - 學習指標

### 開發代理 (Dev Proxy)

前端應用在開發模式下使用 Vite proxy 自動轉發 `/api` 請求到後端：

- 前端請求 `/api/health` → Vite proxy → `http://localhost:8000/api/health`
- 無需配置 CORS，避免跨域問題
- 生產環境可通過環境變數 `VITE_API_BASE_URL` 配置完整 API URL

## 🧪 測試

### 健康檢查測試

#### 後端健康檢查

```bash
curl http://localhost:8000/api/health
# 預期輸出: {"status":"healthy"}
```

#### 前端 API 連接測試

1. 啟動後端和前端
2. 打開瀏覽器開發者工具 (F12)
3. 訪問 http://localhost:5173
4. 檢查 Console 是否有 API 錯誤
5. 檢查 Network 標籤，確認 `/api/health` 請求返回 200

### 執行 Backend 測試

```bash
cd backend

# 執行所有測試
PYTHONPATH=.. pytest tests/ -v

# 執行 Property-Based Tests
PYTHONPATH=.. pytest tests/test_*_properties.py -v

# 執行特定測試檔案
PYTHONPATH=.. pytest tests/test_fsm_controller.py -v

# 顯示測試覆蓋率
PYTHONPATH=.. pytest tests/ --cov=services --cov-report=html
```

### 執行 Frontend 測試

```bash
cd frontend

# 執行所有測試
npm test

# 監聽模式
npm run test:watch

# 測試覆蓋率
npm run test:coverage
```

## 📚 API 文件

### 題目相關 API

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/questions` | 篩選題目列表 |
| GET | `/api/questions/{id}` | 取得題目詳情 |
| POST | `/api/questions/validate` | 驗證答案 |

### 會話相關 API

| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/api/sessions` | 開始新會話 |
| POST | `/api/sessions/{id}/input` | 處理學生輸入 |
| POST | `/api/sessions/{id}/end` | 結束會話 |

### 錯題本 API

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/errors` | 取得錯題列表 |
| GET | `/api/errors/{id}` | 取得錯題詳情 |
| POST | `/api/errors/{id}/repair` | 標記已修復 |
| GET | `/api/errors/statistics` | 取得錯題統計 |

### 儀表板 API

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/dashboard/metrics` | 取得學習指標 |
| GET | `/api/dashboard/heatmap` | 取得弱點熱力圖 |

## 🔧 FSM 狀態機

系統採用有限狀態機 (FSM) 控制對話流程：

```
┌─────────┐
│  IDLE   │ ←────────────────────────────────┐
└────┬────┘                                  │
     │ 開始講題                               │
     ▼                                       │
┌─────────────┐                              │
│  LISTENING  │ ←──────────────────┐         │
└──────┬──────┘                    │         │
       │                           │         │
       ├── 邏輯缺漏 ──→ PROBING ───┘         │
       │                                     │
       ├── 靜默超時 ──→ HINTING ───┘         │
       │                                     │
       ├── 邏輯謬誤 ──→ REPAIR ────┘         │
       │                                     │
       └── 覆蓋率≥90% ──→ CONSOLIDATING ─────┘
```

### 狀態說明

| 狀態 | 說明 |
|------|------|
| IDLE | 閒置狀態，等待開始 |
| LISTENING | 聆聽學生陳述 |
| ANALYZING | 分析邏輯完整性 |
| PROBING | 蘇格拉底式追問 |
| HINTING | 提供漸進式提示 |
| REPAIR | 修正邏輯謬誤 |
| CONSOLIDATING | 觀念總結與遷移 |

## 📈 學習指標

### WPM (Words Per Minute)
```
WPM = 總字數 / 發話時間(分鐘)
```

### 停頓比例
```
停頓比例 = 停頓總時長 / 總時長
```

### 提示依賴度
```
提示依賴度 = 1 - Σ(提示次數 × 權重) / 總互動輪數
```
- Level 1 權重：0.1
- Level 2 權重：0.2
- Level 3 權重：0.3

### 概念覆蓋率
```
概念覆蓋率 = 已覆蓋概念數 / 必要概念數
```

## 🛠️ 技術棧

### Backend
- **框架**：FastAPI
- **資料庫**：SQLite + SQLAlchemy
- **向量資料庫**：ChromaDB
- **Embedding**：sentence-transformers
- **ASR**：OpenAI Whisper
- **LLM**：Ollama (本地部署)
- **測試**：pytest + Hypothesis (Property-Based Testing)

### Frontend (學生端)
- **框架**：React 19 + TypeScript
- **建置工具**：Vite
- **圖表**：Recharts
- **測試**：Vitest + Testing Library
- **程式碼風格**：ESLint + Prettier

### Frontend (教師/家長端)
- **框架**：Vue 3 + Composition API
- **UI 庫**：PrimeVue
- **狀態管理**：Pinia
- **建置工具**：Vite
- **路由**：Vue Router

## 📋 Property-Based Tests

本專案採用 Property-Based Testing 確保系統正確性：

| Property | 說明 | 驗證需求 |
|----------|------|----------|
| Property 1 | 題目篩選結果正確性 | 1.2 |
| Property 3 | 錯誤答案觸發延伸題檢索 | 3.2 |
| Property 4 | 錯題歸檔完整性 | 4.1, 4.2 |
| Property 5 | 錯題篩選正確性 | 4.3 |
| Property 6 | 數學符號轉換正確性 | 5.3 |
| Property 7 | FSM 狀態轉移正確性 | 6.3, 6.4, 6.7, 6.8 |
| Property 8 | 提示層級遞增正確性 | 7.1-7.4 |
| Property 10 | 學習指標計算正確性 | 9.1, 9.3, 9.4 |
| Property 11 | 學習指標持久化完整性 | 9.5 |
| Property 13 | RAG 檢索先於 LLM 生成 | 11.1, 11.2 |
| Property 14 | 知識圖譜模組化擴充 | 13.1 |
| Property 15 | 題庫匯入匯出 Round-Trip | 13.2 |
| Property 16 | 題目知識點自動關聯 | 13.3 |

## 🤝 貢獻指南

1. Fork 本專案
2. 建立功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交變更 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

### 開發規範

- 遵循 PEP 8 (Python) 與 ESLint 規則 (TypeScript)
- 所有新功能需撰寫對應測試
- Property-Based Tests 需至少執行 100 次迭代
- Commit message 使用繁體中文或英文

## 📄 授權

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案

## 🙏 致謝

- [FastAPI](https://fastapi.tiangolo.com/) - 高效能 Python Web 框架
- [Ollama](https://ollama.ai/) - 本地 LLM 運行平台
- [OpenAI Whisper](https://github.com/openai/whisper) - 語音辨識模型
- [ChromaDB](https://www.trychroma.com/) - 向量資料庫
- [Hypothesis](https://hypothesis.readthedocs.io/) - Property-Based Testing 框架
- [Vue.js](https://vuejs.org/) - 漸進式 JavaScript 框架
- [PrimeVue](https://primevue.org/) - Vue UI 元件庫

---

<p align="center">
  Made with ❤️ for better math education
</p>
