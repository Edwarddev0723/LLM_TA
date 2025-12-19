# Implementation Plan: AI 數學語音助教系統

## Overview

本實作計畫採用 Python (FastAPI) 作為 Backend，TypeScript (React) 作為 Frontend。實作順序為：核心資料模型 → FSM 狀態機 → RAG 模組 → ASR 整合 → 對話引擎 → 學習指標 → 前端介面 → 儀表板。

## Tasks

- [x] 1. 專案初始化與基礎架構
  - [x] 1.1 建立 Backend 專案結構 (FastAPI)
    - 建立 `backend/` 目錄結構：`app/`, `tests/`, `models/`, `services/`, `routers/`
    - 設定 `pyproject.toml` 或 `requirements.txt`
    - 設定 pytest 與 Hypothesis 測試框架
    - _Requirements: 12.1, 12.2_
  - [x] 1.2 建立 Frontend 專案結構 (React + TypeScript)
    - 使用 Vite 建立 React + TypeScript 專案
    - 設定 ESLint, Prettier, Jest
    - _Requirements: 5.1_
  - [x] 1.3 設定資料庫 Schema (SQLite)
    - 建立所有資料表 (students, questions, knowledge_nodes, sessions, etc.)
    - 設定 SQLAlchemy ORM models
    - _Requirements: 9.5, 13.1_

- [x] 2. 知識圖譜與題庫模組
  - [x] 2.1 實作 Knowledge Graph Manager
    - 實作 `KnowledgeNode` 與 `KnowledgeRelation` models
    - 實作 `get_node()`, `get_related_nodes()`, `add_node()`, `add_relation()` 方法
    - _Requirements: 13.1, 13.3_
  - [x] 2.2 撰寫 Property Test: 知識圖譜模組化擴充
    - **Property 14: 知識圖譜模組化擴充**
    - **Validates: Requirements 13.1**
  - [x] 2.3 實作 Question Bank Manager
    - 實作 `Question`, `Misconception`, `HintContent` models
    - 實作 `filter_questions()`, `get_question()`, `get_similar_questions()` 方法
    - 實作 `import_questions()`, `export_questions()` (JSON/CSV)
    - _Requirements: 1.2, 13.2_
  - [x] 2.4 撰寫 Property Test: 題目篩選結果正確性
    - **Property 1: 題目篩選結果正確性**
    - **Validates: Requirements 1.2**
  - [x] 2.5 撰寫 Property Test: 題庫匯入匯出 Round-Trip
    - **Property 15: 題庫匯入匯出 Round-Trip**
    - **Validates: Requirements 13.2**
  - [x] 2.6 撰寫 Property Test: 題目知識點自動關聯
    - **Property 16: 題目知識點自動關聯**
    - **Validates: Requirements 13.3**

- [x] 3. Checkpoint - 確保所有測試通過
  - 執行 `pytest tests/` 確認所有測試通過
  - 如有問題請詢問使用者

- [x] 4. 錯題本模組
  - [x] 4.1 實作 Error Book Manager
    - 實作 `ErrorRecord` model
    - 實作 `add_error()`, `get_errors()`, `mark_as_repaired()` 方法
    - 實作錯誤類型自動標籤化邏輯
    - _Requirements: 4.1, 4.2, 4.3_
  - [x] 4.2 撰寫 Property Test: 錯題歸檔完整性
    - **Property 4: 錯題歸檔完整性**
    - **Validates: Requirements 4.1, 4.2**
  - [x] 4.3 撰寫 Property Test: 錯題篩選正確性
    - **Property 5: 錯題篩選正確性**
    - **Validates: Requirements 4.3**

- [x] 5. FSM 狀態機模組
  - [x] 5.1 實作 FSM Controller
    - 定義 `FSMState` enum (IDLE, LISTENING, ANALYZING, PROBING, HINTING, REPAIR, CONSOLIDATING)
    - 實作 `FSMTransition` 與狀態轉移邏輯
    - 實作 `process_event()`, `get_current_state()`, `reset()` 方法
    - _Requirements: 6.1, 6.3, 6.4, 6.7, 6.8_
  - [x] 5.2 撰寫 Property Test: FSM 狀態轉移正確性
    - **Property 7: FSM 狀態轉移正確性**
    - **Validates: Requirements 6.3, 6.4, 6.7, 6.8**
  - [x] 5.3 實作提示層級控制邏輯
    - 實作 `HintLevel` enum 與層級遞增邏輯
    - 實作提示使用記錄功能
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  - [x] 5.4 撰寫 Property Test: 提示層級遞增正確性
    - **Property 8: 提示層級遞增正確性**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4**

- [x] 6. Checkpoint - 確保所有測試通過
  - 執行 `pytest tests/` 確認所有測試通過
  - 如有問題請詢問使用者

- [x] 7. RAG 檢索模組
  - [x] 7.1 設定向量資料庫 (ChromaDB 或 FAISS)
    - 安裝並設定向量資料庫
    - 設定 Embedding 模型 (sentence-transformers)
    - _Requirements: 11.1_
  - [x] 7.2 實作 RAG Module
    - 實作 `retrieve()` 方法：檢索相關題目解法與迷思概念
    - 實作 `index()` 方法：索引新內容
    - 實作相似度閾值與結果數量控制
    - _Requirements: 11.1, 11.2, 3.2_
  - [x] 7.3 撰寫 Property Test: RAG 檢索先於 LLM 生成
    - **Property 13: RAG 檢索先於 LLM 生成**
    - **Validates: Requirements 11.1, 11.2**
  - [x] 7.4 撰寫 Property Test: 錯誤答案觸發延伸題檢索
    - **Property 3: 錯誤答案觸發延伸題檢索**
    - **Validates: Requirements 3.2**

- [x] 8. LLM 整合模組
  - [x] 8.1 實作 Ollama 客戶端
    - 建立與 Ollama API 的連線
    - 實作 `generate()` 方法
    - 實作超時處理與錯誤回退
    - _Requirements: 11.4, 11.5_
  - [x] 8.2 實作 Prompt Builder
    - 建立蘇格拉底式提問 System Prompt 模板
    - 實作 RAG Context 注入邏輯
    - 實作不同 FSM 狀態的 Prompt 變體
    - _Requirements: 11.2, 11.3_

- [x] 9. Checkpoint - 確保所有測試通過
  - 執行 `pytest tests/` 確認所有測試通過
  - 如有問題請詢問使用者

- [x] 10. ASR 語音辨識模組
  - [x] 10.1 實作 Whisper ASR 整合
    - 安裝 OpenAI Whisper 或 faster-whisper
    - 實作 `transcribe()` 方法
    - 實作串流轉錄支援
    - _Requirements: 5.1_
  - [x] 10.2 實作數學符號後處理
    - 建立口語描述到數學符號的對照表
    - 實作 `post_process_math_symbols()` 方法
    - _Requirements: 5.3_
  - [x] 10.3 撰寫 Property Test: 數學符號轉換正確性
    - **Property 6: 數學符號轉換正確性**
    - **Validates: Requirements 5.3**

- [x] 11. 對話引擎模組
  - [x] 11.1 實作 Dialog Engine
    - 整合 FSM Controller, RAG Module, LLM Client
    - 實作 `process_student_input()` 方法
    - 實作 `start_session()`, `end_session()` 方法
    - _Requirements: 6.2, 6.6, 6.9_
  - [x] 11.2 實作會話管理
    - 實作 `Session` model 與對話歷史記錄
    - 實作概念覆蓋率計算
    - _Requirements: 6.8_

- [x] 12. 學習指標計算模組
  - [x] 12.1 實作 Metrics Calculator
    - 實作 `calculate_wpm()` 方法
    - 實作 `calculate_pause_rate()` 方法
    - 實作 `calculate_hint_dependency()` 方法
    - 實作 `calculate_concept_coverage()` 方法
    - _Requirements: 9.1, 9.3, 9.4_
  - [x] 12.2 撰寫 Property Test: 學習指標計算正確性
    - **Property 10: 學習指標計算正確性**
    - **Validates: Requirements 9.1, 9.3, 9.4**
  - [x] 12.3 實作指標持久化
    - 實作 `save_metrics()` 方法
    - 實作 `get_metrics()` 方法
    - _Requirements: 9.5_
  - [x] 12.4 撰寫 Property Test: 學習指標持久化完整性
    - **Property 11: 學習指標持久化完整性**
    - **Validates: Requirements 9.5**

- [x] 13. Checkpoint - 確保所有測試通過
  - 執行 `pytest tests/` 確認所有測試通過
  - 如有問題請詢問使用者

- [x] 14. Backend API 路由
  - [x] 14.1 實作題目相關 API
    - `GET /api/questions` - 篩選題目
    - `GET /api/questions/{id}` - 取得題目詳情
    - `POST /api/questions/validate` - 驗證答案
    - _Requirements: 1.1, 1.2, 3.1_
  - [x] 14.2 實作會話相關 API
    - `POST /api/sessions` - 開始新會話
    - `POST /api/sessions/{id}/input` - 處理學生輸入
    - `POST /api/sessions/{id}/end` - 結束會話
    - _Requirements: 6.1_
  - [x] 14.3 實作錯題本 API
    - `GET /api/errors` - 取得錯題列表
    - `POST /api/errors/{id}/repair` - 標記已修復
    - _Requirements: 4.3, 8.3_
  - [ ]* 14.4 撰寫 Property Test: 錯題修復流程正確性
    - **Property 9: 錯題修復流程正確性**
    - **Validates: Requirements 8.3**
  - [x] 14.5 實作儀表板 API
    - `GET /api/dashboard/metrics` - 取得學習指標
    - `GET /api/dashboard/heatmap` - 取得弱點熱力圖
    - _Requirements: 10.1, 10.2_
  - [ ]* 14.6 撰寫 Property Test: 弱點熱力圖資料正確性
    - **Property 12: 弱點熱力圖資料正確性**
    - **Validates: Requirements 10.2**

- [x] 15. Checkpoint - 確保所有測試通過
  - 執行 `pytest tests/` 確認所有測試通過
  - 如有問題請詢問使用者

- [x] 16. Frontend 學生介面
  - [x] 16.1 實作題目篩選與練習頁面
    - 建立篩選介面 (科目、單元、難度)
    - 建立題目列表與詳情顯示
    - _Requirements: 1.1, 1.2_
  - [x] 16.2 實作語音輸入元件
    - 整合 Web Audio API 進行音訊擷取
    - 實作即時字幕顯示
    - 實作「重說一次」功能
    - _Requirements: 5.1, 5.2_
  - [x] 16.3 實作口語講題介面
    - 建立對話框顯示區域
    - 顯示 FSM 狀態指示
    - 顯示提示層級與概念覆蓋率
    - _Requirements: 6.1, 6.6, 7.1_
  - [x] 16.4 實作錯題本頁面
    - 建立錯題列表與篩選功能
    - 建立錯題重述流程
    - _Requirements: 4.3, 8.1_

- [x] 17. Frontend 儀表板介面
  - [x] 17.1 實作學習指標視覺化
    - 建立 WPM 趨勢圖 (使用 Chart.js 或 Recharts)
    - 建立停頓比例分佈圖
    - 建立提示依賴度統計
    - _Requirements: 10.1_
  - [x] 17.2 實作弱點熱力圖
    - 建立知識圖譜視覺化
    - 實作紅黃綠燈掌握度顯示
    - _Requirements: 10.2_
  - [x] 17.3 實作學習歷程詳情
    - 建立知識點詳情展開功能
    - 顯示專注時長與分心時段
    - _Requirements: 10.3, 10.4_

- [ ] 18. OCR 整合 (選用)
  - [ ]* 18.1 實作數位白板元件
    - 建立 Canvas 繪圖功能
    - 實作筆跡儲存與清除
    - _Requirements: 2.1_
  - [ ]* 18.2 整合 OCR 服務
    - 整合 Tesseract 或 Vision API
    - 實作 `recognize_handwriting()` 方法
    - _Requirements: 2.2_
  - [ ]* 18.3 撰寫 Property Test: OCR 低信心度處理
    - **Property 2: OCR 低信心度處理**
    - **Validates: Requirements 2.3**

- [x] 19. 知識圖譜匯出備份
  - [x] 19.1 實作知識圖譜匯出功能
    - 實作 `export_knowledge_graph()` 方法
    - 支援 JSON 格式匯出
    - _Requirements: 13.4_
  - [ ]* 19.2 撰寫 Property Test: 知識圖譜匯出備份 Round-Trip
    - **Property 17: 知識圖譜匯出備份 Round-Trip**
    - **Validates: Requirements 13.4**

- [x] 20. Final Checkpoint - 完整測試
  - 執行所有 Property Tests 確認通過
  - 執行整合測試
  - 如有問題請詢問使用者

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- 每個 Property Test 對應設計文件中的一個正確性屬性
- Checkpoints 確保增量驗證，避免累積錯誤
- OCR 整合 (Task 18) 為選用功能，可在 MVP 後實作
- 建議先完成 Backend 核心模組，再進行 Frontend 開發
