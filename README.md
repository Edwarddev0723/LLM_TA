# 🎓 AI 數學語音助教系統

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/TypeScript-5.9+-blue.svg" alt="TypeScript">
  <img src="https://img.shields.io/badge/FastAPI-0.104+-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-19.2+-61DAFB.svg" alt="React">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

一個基於費曼學習法的國中數學 AI 語音助教系統，結合本地端 LLM (Ollama)、RAG、ASR (Whisper) 及有限狀態機 (FSM) 技術，提供即時語音互動式數學學習體驗。

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
│                        Frontend (React)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │ 練習頁面 │  │ 講題介面 │  │ 錯題本   │  │ 教師/家長儀表板 │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │ REST API
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

## 📁 專案結構

```
ai-math-tutor/
├── backend/                    # Python FastAPI 後端
│   ├── app/
│   │   └── main.py            # FastAPI 應用程式入口
│   ├── models/                 # 資料模型
│   │   ├── database.py        # SQLAlchemy 資料庫設定
│   │   ├── knowledge.py       # 知識圖譜模型
│   │   ├── question.py        # 題目模型
│   │   ├── session.py         # 會話模型
│   │   ├── metrics.py         # 學習指標模型
│   │   ├── error_book.py      # 錯題本模型
│   │   └── embedding.py       # 向量嵌入模型
│   ├── services/              # 業務邏輯服務
│   │   ├── asr_module.py      # 語音辨識模組
│   │   ├── fsm_controller.py  # 有限狀態機控制器
│   │   ├── hint_controller.py # 提示層級控制器
│   │   ├── dialog_engine.py   # 對話引擎
│   │   ├── rag_module.py      # RAG 檢索模組
│   │   ├── llm_client.py      # LLM 客戶端 (Ollama)
│   │   ├── prompt_builder.py  # Prompt 建構器
│   │   ├── knowledge_graph.py # 知識圖譜管理器
│   │   ├── question_bank.py   # 題庫管理器
│   │   ├── error_book.py      # 錯題本管理器
│   │   ├── metrics_calculator.py # 指標計算器
│   │   └── session_manager.py # 會話管理器
│   ├── routers/               # API 路由
│   │   ├── questions.py       # 題目相關 API
│   │   ├── sessions.py        # 會話相關 API
│   │   ├── errors.py          # 錯題本 API
│   │   └── dashboard.py       # 儀表板 API
│   ├── tests/                 # 測試檔案
│   │   ├── test_*_properties.py  # Property-Based Tests
│   │   └── test_*.py          # 單元測試
│   ├── pyproject.toml         # Python 專案設定
│   └── requirements.txt       # Python 依賴
│
├── frontend/                   # React TypeScript 前端
│   ├── src/
│   │   ├── api/               # API 客戶端
│   │   ├── components/        # React 元件
│   │   │   ├── QuestionFilter.tsx    # 題目篩選器
│   │   │   ├── QuestionList.tsx      # 題目列表
│   │   │   ├── QuestionDetail.tsx    # 題目詳情
│   │   │   ├── VoiceInput.tsx        # 語音輸入元件
│   │   │   ├── ConversationPanel.tsx # 對話面板
│   │   │   ├── FSMStateIndicator.tsx # FSM 狀態指示器
│   │   │   ├── ErrorFilter.tsx       # 錯題篩選器
│   │   │   ├── ErrorList.tsx         # 錯題列表
│   │   │   └── ErrorDetail.tsx       # 錯題詳情
│   │   ├── pages/             # 頁面元件
│   │   │   ├── PracticePage.tsx      # 練習頁面
│   │   │   ├── SessionPage.tsx       # 講題會話頁面
│   │   │   ├── ErrorBookPage.tsx     # 錯題本頁面
│   │   │   └── DashboardPage.tsx     # 儀表板頁面
│   │   ├── hooks/             # 自訂 Hooks
│   │   │   └── useAudioRecorder.ts   # 音訊錄製 Hook
│   │   ├── types/             # TypeScript 型別定義
│   │   ├── App.tsx            # 主應用程式
│   │   └── main.tsx           # 入口點
│   ├── package.json           # Node.js 依賴
│   └── vite.config.ts         # Vite 設定
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
cd frontend
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

### 啟動服務

#### 啟動 Backend

```bash
cd backend
PYTHONPATH=.. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 啟動 Frontend

```bash
cd frontend
npm run dev
```

#### 存取應用程式

- **Frontend**：http://localhost:5173
- **Backend API**：http://localhost:8000
- **API 文件**：http://localhost:8000/docs

## 🧪 測試

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

### Frontend
- **框架**：React 19 + TypeScript
- **建置工具**：Vite
- **圖表**：Recharts
- **測試**：Vitest + Testing Library
- **程式碼風格**：ESLint + Prettier

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

---

<p align="center">
  Made with ❤️ for better math education
</p>
