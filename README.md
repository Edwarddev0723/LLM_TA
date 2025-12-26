# 🎓 AI 數學語音助教系統 (AI Math Tutor)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.104+-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/Vue-3.5+-4FC08D.svg" alt="Vue">
  <img src="https://img.shields.io/badge/React-19+-61DAFB.svg" alt="React">
  <img src="https://img.shields.io/badge/Ollama-Local_LLM-orange.svg" alt="Ollama">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

<p align="center">
  基於費曼學習法的國中數學 AI 語音助教系統<br>
  結合本地端 LLM、RAG、ASR 及 FSM 技術，提供即時語音互動式數學學習體驗
</p>

---

## 📖 目錄

- [功能特色](#-功能特色)
- [系統架構](#-系統架構)
- [專案結構](#-專案結構)
- [快速開始](#-快速開始)
- [功能模組詳解](#-功能模組詳解)
- [API 文件](#-api-文件)
- [FSM 狀態機](#-fsm-狀態機)
- [技術棧](#-技術棧)
- [測試](#-測試)
- [貢獻指南](#-貢獻指南)

---

## ✨ 功能特色

### 🎯 三大角色入口

| 角色 | 功能 | 入口 |
|------|------|------|
| **學生** | 學習儀表板、教學模式、做題模式、錯題診所 | `/student` |
| **教師** | 班級管理、學生分析、教學建議、題庫匯入 | `/teacher` |
| **家長** | 學習報告、進度追蹤、成績概覽 | `/parent` |

### 🧠 核心學習功能

#### 教學模式 (Teaching Mode)
- **語音互動學習**：透過 Whisper ASR 實現即時語音轉文字
- **蘇格拉底式引導**：五階段 FSM 引導循環，不直接給答案
- **智慧提示系統**：三層級漸進式提示 (方向暗示 → 關鍵步驟 → 解法框架)
- **即時白板**：Fabric.js 實作的互動式白板，支援繪圖、橡皮擦、存檔/載入

#### 做題模式 (Practice Mode)
- **題庫練習**：6 大範圍 (算術/代數/幾何/機率統計/函數/數列)
- **難度分級**：5 級難度選擇，支援題型比例調整
- **AI 評分**：解題邏輯評分 (0-100)，即時反饋
- **白板輔助**：每題配備互動白板，方便演算

#### 錯題診所 (Mistake Clinic)
- **自動歸檔**：錯題自動記錄並標籤化
- **錯題重述**：AI 引導重新理解錯誤概念
- **變題測試**：生成相似題目鞏固學習

### 📊 學習分析

- **即時指標**：WPM、停頓比例、提示依賴度、概念覆蓋率
- **弱點熱力圖**：基於知識圖譜的掌握度視覺化
- **學習歷程**：完整記錄對話歷史與進度
- **趨勢圖表**：正確率、學習時間、錯題分布

### 🔒 隱私與效能

- **本地端部署**：所有 AI 模型運行於本地，確保學生隱私
- **低延遲**：ASR 轉錄 < 1 秒，LLM 首字生成 < 5 秒

---

## 🏗️ 系統架構

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Frontend Applications                           │
│  ┌────────────────────────┐  ┌────────────────────────────────────┐ │
│  │   Student Frontend     │  │   Teacher/Parent Web Portal        │ │
│  │   (React + TypeScript) │  │   (Vue 3 + Composition API)        │ │
│  │   frontend/            │  │   apps/teacher-web/                │ │
│  │                        │  │                                    │ │
│  │   • Dashboard          │  │   • 學生端: 儀表板/教學/做題/錯題  │ │
│  │   • Session Page       │  │   • 教師端: 班級/學生/建議/題庫    │ │
│  │   • Error Book         │  │   • 家長端: 報告/進度/成績         │ │
│  │   • Practice Page      │  │   • 管理端: 系統管理               │ │
│  └────────────────────────┘  └────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                              │ REST API (/api)
┌─────────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI + Python)                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    API Routers (/api/*)                        │  │
│  │  auth | sessions | practice | questions | errors | dashboard  │  │
│  │  student | teacher | subjects | student_metrics | asr         │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    Core Services                               │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │  │
│  │  │ FSM 控制器  │ │ 對話引擎    │ │ 提示控制器  │              │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘              │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │  │
│  │  │ LLM Client  │ │ RAG Module  │ │ ASR Module  │              │  │
│  │  │ (Ollama)    │ │ (ChromaDB)  │ │ (Whisper)   │              │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘              │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │  │
│  │  │ 錯題本管理  │ │ 指標計算器  │ │ 會話管理器  │              │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘              │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────────┐
│                      Data Layer                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │ SQLite/MySQL │  │ ChromaDB     │  │ Ollama (Local LLM)       │   │
│  │ 主資料庫     │  │ 向量資料庫   │  │ gpt-oss:20b / llama3.2   │   │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📁 專案結構

```
ai-math-tutor/
├── backend/                          # Python FastAPI 後端
│   ├── app/
│   │   └── main.py                   # FastAPI 應用程式入口
│   ├── models/                       # 資料模型
│   │   ├── user.py                   # 使用者模型
│   │   ├── question.py               # 題目模型
│   │   ├── session.py                # 會話模型
│   │   ├── error_book.py             # 錯題本模型
│   │   └── ...
│   ├── services/                     # 業務邏輯服務
│   │   ├── llm_client.py             # Ollama LLM 客戶端
│   │   ├── fsm_controller.py         # FSM 狀態機控制器
│   │   ├── dialog_engine.py          # 對話引擎
│   │   ├── hint_controller.py        # 提示控制器
│   │   ├── rag_module.py             # RAG 檢索模組
│   │   ├── asr_module.py             # ASR 語音辨識
│   │   ├── error_book.py             # 錯題本管理
│   │   ├── metrics_calculator.py     # 學習指標計算
│   │   └── ...
│   ├── routers/                      # API 路由
│   │   ├── auth.py                   # 認證 API
│   │   ├── sessions.py               # 會話 API
│   │   ├── practice.py               # 做題模式 API
│   │   ├── questions.py              # 題目 API
│   │   ├── errors.py                 # 錯題 API
│   │   ├── dashboard.py              # 儀表板 API
│   │   ├── student_metrics.py        # 學生指標 API
│   │   ├── teacher.py                # 教師 API
│   │   └── ...
│   ├── tests/                        # 測試檔案
│   ├── scripts/                      # 工具腳本
│   │   └── init_db.py                # 資料庫初始化
│   ├── pyproject.toml
│   └── requirements.txt
│
├── frontend/                         # React TypeScript 學生前端
│   ├── src/
│   │   ├── api/                      # API 客戶端
│   │   ├── components/               # React 元件
│   │   ├── pages/                    # 頁面元件
│   │   ├── hooks/                    # 自訂 Hooks
│   │   └── types/                    # TypeScript 型別
│   ├── package.json
│   └── vite.config.ts                # Vite 設定 (含 /api proxy)
│
├── apps/
│   └── teacher-web/                  # Vue 3 多角色入口
│       ├── src/
│       │   ├── views/
│       │   │   ├── student/          # 學生視圖
│       │   │   │   ├── StudentDashboard.vue
│       │   │   │   ├── TeachingMode.vue
│       │   │   │   ├── PracticeMode.vue
│       │   │   │   └── MistakeClinic.vue
│       │   │   ├── teacher/          # 教師視圖
│       │   │   │   ├── TeacherOverview.vue
│       │   │   │   ├── TeacherClassManagement.vue
│       │   │   │   └── TeachingSuggestions.vue
│       │   │   └── parent/           # 家長視圖
│       │   │       ├── ParentOverview.vue
│       │   │       └── ParentStudentDetail.vue
│       │   ├── components/
│       │   │   └── teaching/
│       │   │       └── WhiteboardCanvas.vue  # Fabric.js 白板
│       │   ├── stores/               # Pinia 狀態管理
│       │   └── router/               # Vue Router
│       ├── package.json
│       └── vite.config.js
│
├── .kiro/specs/                      # 規格文件
│   └── ai-math-tutor/
│       ├── requirements.md
│       ├── design.md
│       └── tasks.md
│
├── start-backend.sh                  # 後端啟動腳本
├── start-frontend.sh                 # 學生前端啟動腳本
├── start-teacher-web.sh              # 教師入口啟動腳本
└── README.md
```

---

## 🚀 快速開始

### 系統需求

| 項目 | 最低需求 | 建議配置 |
|------|----------|----------|
| 作業系統 | macOS / Linux / Windows | macOS (Apple Silicon) |
| Python | 3.10+ | 3.11+ |
| Node.js | 18+ | 20+ |
| 記憶體 | 8GB | 16GB+ (運行本地 LLM) |
| 硬碟空間 | 10GB | 20GB+ (含模型) |

### 安裝步驟

#### 1. 克隆專案

```bash
git clone https://github.com/your-username/ai-math-tutor.git
cd ai-math-tutor
```

#### 2. 安裝 Backend

```bash
cd backend

# 建立虛擬環境
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 安裝依賴
pip install -r requirements.txt

cd ..
```

#### 3. 安裝 Frontend

```bash
# 學生前端 (React)
cd frontend
npm install
cd ..

# 教師/家長入口 (Vue)
cd apps/teacher-web
npm install
cd ../..
```

#### 4. 安裝 Ollama (本地 LLM)

```bash
# macOS
brew install ollama

# 啟動 Ollama 服務
ollama serve

# 下載模型 (另開終端機)
ollama pull llama3.2        # 通用模型
# 或
ollama pull gpt-oss:20b     # 專案預設模型
```

#### 5. 初始化資料庫

```bash
cd backend
source venv/bin/activate
PYTHONPATH=.. python scripts/init_db.py
cd ..
```

### 啟動服務

#### 方式一：使用啟動腳本 (推薦)

```bash
# 終端機 1: 啟動後端
./start-backend.sh

# 終端機 2: 啟動學生前端 (React)
./start-frontend.sh

# 終端機 3: 啟動教師入口 (Vue)
./start-teacher-web.sh
```

#### 方式二：手動啟動

```bash
# 後端
cd backend && source venv/bin/activate
PYTHONPATH=.. uvicorn app.main:app --reload --port 8000

# 學生前端
cd frontend && npm run dev

# 教師入口
cd apps/teacher-web && npm run dev -- --port 3000
```

### 存取應用程式

| 服務 | URL | 說明 |
|------|-----|------|
| Backend API | http://localhost:8000 | FastAPI 後端 |
| API 文件 | http://localhost:8000/docs | Swagger UI |
| 健康檢查 | http://localhost:8000/api/health | 狀態檢查 |
| 學生前端 | http://localhost:5173 | React 學習介面 |
| 教師入口 | http://localhost:3000 | Vue 管理介面 |

### 驗證安裝

```bash
# 測試後端
curl http://localhost:8000/api/health
# 預期: {"status":"healthy"}

# 測試 Ollama
curl http://localhost:11434/api/tags
# 預期: 顯示已安裝的模型列表
```

---

## 📱 功能模組詳解

### 學生端功能

#### 📊 學習儀表板 (StudentDashboard)
- KPI 卡片：總學習時間、完成題數、正確率、連續學習天數
- 學習趨勢圖：每日正確率、學習時間折線圖
- 錯題分析：按單元分類的錯題分布
- 弱點提示：需要加強的知識點

#### 🎓 教學模式 (TeachingMode)
- 雙欄佈局：左側題目+AI對話，右側白板
- FSM 狀態指示器：顯示當前引導階段
- 語音輸入：即時語音轉文字
- 串流回應：AI 回應即時顯示

#### ✍️ 做題模式 (PracticeMode)
- 設定畫面：
  - 年級選擇 (國小/國中/高中)
  - 範圍多選 (算術/代數/幾何/機率統計/函數/數列)
  - 難度滑桿 (1-5 級)
  - 題型比例調整
- 練習畫面：
  - 10 題選擇題
  - 每題配備白板
  - 解題邏輯輸入欄
  - 即時答案反饋
- 結果畫面：
  - 分數圓圈
  - 各範圍表現長條圖
  - AI 評語
  - 詳細解答與 AI 解題

#### 🏥 錯題診所 (MistakeClinic)
- 錯題列表：按時間/單元/難度篩選
- 錯題重述：AI 引導重新理解
- 變題練習：生成相似題目
- 修復標記：標記已掌握的錯題

### 教師端功能

#### 📈 班級總覽 (TeacherOverview)
- 班級學習統計
- 學生排名
- 整體進度追蹤

#### 👥 班級管理 (TeacherClassManagement)
- 學生名單管理
- 分組功能
- 批量操作

#### 💡 教學建議 (TeachingSuggestions)
- AI 生成的教學建議
- 班級弱點分析
- 個別學生建議

#### 📚 題庫匯入 (TeacherImportQuestions)
- Excel/CSV 匯入
- 題目預覽
- 批量編輯

### 家長端功能

#### 📊 學習報告 (ParentOverview)
- 孩子學習概況
- 週/月報告
- 進度對比

#### 📈 詳細分析 (ParentStudentDetail)
- 各科目表現
- 學習時間分析
- 錯題統計

---

## 📚 API 文件

### 認證 API (`/api/auth`)

| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/api/auth/login` | 使用者登入 |
| POST | `/api/auth/register` | 使用者註冊 |
| GET | `/api/auth/me` | 取得當前使用者資訊 |

### 會話 API (`/api/sessions`)

| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/api/sessions` | 開始新會話 |
| POST | `/api/sessions/{id}/input` | 處理學生輸入 |
| POST | `/api/sessions/{id}/end` | 結束會話 |
| GET | `/api/sessions/{id}` | 取得會話詳情 |

### 做題模式 API (`/api/practice`)

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/practice/topics` | 取得可用範圍列表 |
| POST | `/api/practice/start` | 開始練習會話 |
| POST | `/api/practice/check-answer` | 驗證單題答案 |
| POST | `/api/practice/submit` | 提交所有答案並取得結果 |

### 題目 API (`/api/questions`)

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/questions` | 篩選題目列表 |
| GET | `/api/questions/{id}` | 取得題目詳情 |
| POST | `/api/questions/validate` | 驗證答案 |

### 錯題本 API (`/api/errors`)

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/errors` | 取得錯題列表 |
| GET | `/api/errors/{id}` | 取得錯題詳情 |
| POST | `/api/errors/{id}/repair` | 標記已修復 |
| GET | `/api/errors/statistics` | 取得錯題統計 |

### 儀表板 API (`/api/dashboard`)

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/dashboard/metrics` | 取得學習指標 |
| GET | `/api/dashboard/heatmap` | 取得弱點熱力圖 |

### 學生指標 API (`/api/student-metrics`)

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/student-metrics/kpi` | 取得 KPI 數據 |
| GET | `/api/student-metrics/trends` | 取得學習趨勢 |
| GET | `/api/student-metrics/error-analysis` | 取得錯題分析 |

### 教師 API (`/api/teacher`)

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/teacher/classes` | 取得班級列表 |
| GET | `/api/teacher/students` | 取得學生列表 |
| GET | `/api/teacher/suggestions` | 取得教學建議 |

---

## 🔧 FSM 狀態機

系統採用有限狀態機 (FSM) 控制對話流程，實現蘇格拉底式引導教學：

```
                    ┌─────────────────────────────────────┐
                    │                                     │
                    ▼                                     │
              ┌──────────┐                                │
              │   IDLE   │ ←─────────────────────────┐    │
              └────┬─────┘                           │    │
                   │ 開始講題                         │    │
                   ▼                                 │    │
              ┌──────────┐                           │    │
         ┌───▶│ LISTENING│◀──────────────────┐      │    │
         │    └────┬─────┘                   │      │    │
         │         │                         │      │    │
         │    ┌────┴────┬────────────┐       │      │    │
         │    │         │            │       │      │    │
         │    ▼         ▼            ▼       │      │    │
         │ 邏輯缺漏  靜默超時     邏輯謬誤    │      │    │
         │    │         │            │       │      │    │
         │    ▼         ▼            ▼       │      │    │
         │ ┌──────┐ ┌──────┐    ┌──────┐    │      │    │
         │ │PROBING│ │HINTING│    │REPAIR│    │      │    │
         │ └──┬───┘ └──┬───┘    └──┬───┘    │      │    │
         │    │        │           │        │      │    │
         │    └────────┴───────────┴────────┘      │    │
         │                                         │    │
         │         覆蓋率 ≥ 90%                     │    │
         │              │                          │    │
         │              ▼                          │    │
         │    ┌─────────────────┐                  │    │
         │    │  CONSOLIDATING  │──────────────────┘    │
         │    └─────────────────┘                       │
         │              │                               │
         │              │ 完成總結                       │
         │              ▼                               │
         └──────────────┴───────────────────────────────┘
```

### 狀態說明

| 狀態 | 說明 | 觸發條件 |
|------|------|----------|
| `IDLE` | 閒置狀態 | 初始狀態 / 會話結束 |
| `LISTENING` | 聆聽學生陳述 | 開始講題 |
| `PROBING` | 蘇格拉底式追問 | 偵測到邏輯缺漏 |
| `HINTING` | 提供漸進式提示 | 靜默超時 (>10秒) |
| `REPAIR` | 修正邏輯謬誤 | 偵測到錯誤概念 |
| `CONSOLIDATING` | 觀念總結與遷移 | 概念覆蓋率 ≥ 90% |

### 提示層級

| 層級 | 類型 | 說明 | 權重 |
|------|------|------|------|
| Level 1 | 方向暗示 | 提示思考方向 | 0.1 |
| Level 2 | 關鍵步驟 | 提示關鍵步驟 | 0.2 |
| Level 3 | 解法框架 | 提供解法框架 | 0.3 |

---

## 📈 學習指標

### WPM (Words Per Minute)
```
WPM = 總字數 / 發話時間(分鐘)
```
衡量學生表達流暢度。

### 停頓比例
```
停頓比例 = 停頓總時長 / 總時長
```
反映學生思考時間分配。

### 提示依賴度
```
提示依賴度 = 1 - Σ(提示次數 × 權重) / 總互動輪數
```
衡量學生自主解題能力。

### 概念覆蓋率
```
概念覆蓋率 = 已覆蓋概念數 / 必要概念數
```
追蹤學習進度完整性。

---

## 🛠️ 技術棧

### Backend
| 技術 | 用途 |
|------|------|
| FastAPI | Web 框架 |
| SQLAlchemy | ORM |
| SQLite / MySQL | 資料庫 |
| ChromaDB | 向量資料庫 |
| sentence-transformers | Embedding |
| OpenAI Whisper | ASR 語音辨識 |
| Ollama | 本地 LLM |
| pytest + Hypothesis | 測試框架 |

### Frontend (學生端)
| 技術 | 用途 |
|------|------|
| React 19 | UI 框架 |
| TypeScript | 型別系統 |
| Vite | 建置工具 |
| Recharts | 圖表 |
| Vitest | 測試框架 |

### Frontend (教師/家長端)
| 技術 | 用途 |
|------|------|
| Vue 3 | UI 框架 |
| Composition API | 組合式 API |
| Pinia | 狀態管理 |
| Vue Router | 路由 |
| Fabric.js | 白板繪圖 |
| Chart.js | 圖表 |

---

## 🧪 測試

### 執行 Backend 測試

```bash
cd backend
source venv/bin/activate

# 執行所有測試
PYTHONPATH=.. pytest tests/ -v

# 執行 Property-Based Tests
PYTHONPATH=.. pytest tests/test_*_properties.py -v

# 測試覆蓋率
PYTHONPATH=.. pytest tests/ --cov=services --cov-report=html
```

### 執行 Frontend 測試

```bash
cd frontend

# 執行測試
npm test

# 監聽模式
npm run test:watch

# 覆蓋率
npm run test:coverage
```

### Property-Based Tests

本專案採用 Hypothesis 進行 Property-Based Testing：

| Property | 驗證內容 |
|----------|----------|
| Property 1 | 題目篩選結果正確性 |
| Property 3 | 錯誤答案觸發延伸題檢索 |
| Property 4 | 錯題歸檔完整性 |
| Property 6 | 數學符號轉換正確性 |
| Property 7 | FSM 狀態轉移正確性 |
| Property 8 | 提示層級遞增正確性 |
| Property 10 | 學習指標計算正確性 |
| Property 13 | RAG 檢索先於 LLM 生成 |
| Property 14 | 知識圖譜模組化擴充 |
| Property 15 | 題庫匯入匯出 Round-Trip |

---

## 🔧 環境變數

### Backend (.env)

```bash
# 資料庫
DATABASE_URL=sqlite:///./ai_math_tutor.db
# 或 MySQL
# DATABASE_URL=mysql+pymysql://user:pass@localhost/ai_math_tutor

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gpt-oss:20b

# ASR
WHISPER_MODEL=base

# 其他
DEBUG=true
LOG_LEVEL=INFO
```

### Frontend (.env)

```bash
# API URL (生產環境)
VITE_API_BASE_URL=https://api.example.com

# 開發環境使用 Vite proxy，無需設定
```

---

## 🤝 貢獻指南

### 開發流程

1. Fork 本專案
2. 建立功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交變更 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

### 開發規範

- Python: 遵循 PEP 8
- TypeScript/Vue: 遵循 ESLint 規則
- 所有新功能需撰寫對應測試
- Property-Based Tests 需至少執行 100 次迭代
- Commit message 使用繁體中文或英文

### 程式碼風格

```bash
# Python 格式化
cd backend
black .
isort .

# Frontend 格式化
cd frontend
npm run lint:fix

cd apps/teacher-web
npm run lint:fix
```

---

## 📋 常見問題

### Q: 後端啟動失敗？
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Q: 前端無法連接後端？
1. 確認後端已啟動: `curl http://localhost:8000/api/health`
2. 檢查 Vite proxy 配置
3. 清除瀏覽器緩存

### Q: Ollama 模型下載失敗？
```bash
# 檢查 Ollama 服務
ollama serve

# 重新下載模型
ollama pull llama3.2
```

### Q: 端口被占用？
```bash
# 查找占用進程
lsof -i :8000
lsof -i :5173
lsof -i :3000

# 終止進程
kill -9 <PID>
```

---

## 📄 授權

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案

---

## 🙏 致謝

- [FastAPI](https://fastapi.tiangolo.com/) - 高效能 Python Web 框架
- [Ollama](https://ollama.ai/) - 本地 LLM 運行平台
- [OpenAI Whisper](https://github.com/openai/whisper) - 語音辨識模型
- [ChromaDB](https://www.trychroma.com/) - 向量資料庫
- [Vue.js](https://vuejs.org/) - 漸進式 JavaScript 框架
- [Fabric.js](http://fabricjs.com/) - Canvas 繪圖庫
- [Hypothesis](https://hypothesis.readthedocs.io/) - Property-Based Testing

---

<p align="center">
  Made with ❤️ for better math education
</p>
