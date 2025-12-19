# Requirements Document

## Introduction

本系統為「國中數學 AI 語音助教」，採用費曼學習法核心精神，結合本地端 LLM (Ollama)、RAG、ASR (Whisper) 及有限狀態機 (FSM) 技術，提供即時語音互動式數學學習體驗。系統部署於 Apple MacBook 本地端，確保學生隱私與低延遲。

## Glossary

- **AI_Tutor**: 本系統的核心對話引擎，負責管理學習流程與生成引導回饋
- **ASR_Module**: 語音辨識模組，使用 Whisper 將學生語音轉換為文字
- **FSM_Controller**: 有限狀態機控制器，管理對話階段轉移 (IDLE, LISTENING, ANALYZING, PROBING, HINTING, REPAIR, CONSOLIDATING)
- **RAG_Module**: 檢索增強生成模組，從知識圖譜與題庫中檢索相關內容
- **Knowledge_Graph**: 知識圖譜，儲存數學概念節點與關聯
- **Question_Bank**: 題庫，儲存題目、標準解法與常見迷思概念
- **Learning_Metrics**: 學習指標，包含 WPM、停頓率、提示依賴度等
- **Dashboard**: 教師/家長儀表板，顯示學習數據與弱點分析
- **Error_Book**: 錯題本，自動歸檔學生錯題並標籤化
- **Hint_Level**: 提示層級 (Level 1-3)，由最小提示逐步增加資訊量

## Requirements

### Requirement 1: 題目篩選與練習

**User Story:** As a 學生, I want to 依科目、單元、難度篩選題目, so that 我可以針對性地練習特定範圍。

#### Acceptance Criteria

1. WHEN 學生進入練習模組 THEN THE AI_Tutor SHALL 顯示科目、單元、難度的篩選介面
2. WHEN 學生選擇篩選條件並確認 THEN THE Question_Bank SHALL 返回符合條件的題目列表
3. WHEN 題目列表為空 THEN THE AI_Tutor SHALL 顯示「無符合條件的題目」提示並建議調整篩選條件

### Requirement 2: 數位草稿與 OCR 辨識

**User Story:** As a 學生, I want to 在數位白板上書寫計算過程並讓系統辨識, so that 系統能理解我的解題步驟。

#### Acceptance Criteria

1. THE AI_Tutor SHALL 提供數位白板功能供學生書寫
2. WHEN 學生上傳手寫草稿圖片 THEN THE AI_Tutor SHALL 透過 OCR 辨識計算過程並轉換為結構化文字
3. IF OCR 辨識信心度低於閾值 THEN THE AI_Tutor SHALL 標示不確定區域並請學生確認或重寫

### Requirement 3: 即時答題回饋

**User Story:** As a 學生, I want to 答題後立即知道對錯並獲得延伸練習, so that 我可以即時修正錯誤觀念。

#### Acceptance Criteria

1. WHEN 學生提交答案 THEN THE AI_Tutor SHALL 於 2 秒內判定正誤並顯示結果
2. WHEN 答案錯誤 THEN THE RAG_Module SHALL 檢索 1-2 題同觀念延伸題並推播給學生
3. WHEN 答案正確 THEN THE AI_Tutor SHALL 顯示鼓勵訊息並提供進階題目選項

### Requirement 4: 錯題自動歸檔

**User Story:** As a 學生, I want to 錯題自動被歸檔並標籤化, so that 我可以日後複習弱點。

#### Acceptance Criteria

1. WHEN 學生答錯題目 THEN THE Error_Book SHALL 自動儲存該題目與學生的錯誤答案
2. WHEN 錯題被歸檔 THEN THE AI_Tutor SHALL 依據錯誤類型自動標籤化 (計算錯誤、觀念錯誤、粗心等)
3. THE Error_Book SHALL 支援依標籤、日期、單元篩選錯題

### Requirement 5: 語音輸入與即時轉錄

**User Story:** As a 學生, I want to 用語音講解解題思路並看到即時字幕, so that 我可以專注於口語表達而非打字。

#### Acceptance Criteria

1. WHEN 學生開始語音輸入 THEN THE ASR_Module SHALL 於 1 秒內開始串流轉錄並顯示流式字幕
2. WHEN 學生說「重說一次」 THEN THE ASR_Module SHALL 清除最近一段轉錄並重新開始聆聽
3. IF ASR 辨識結果包含數學符號 THEN THE ASR_Module SHALL 將口語描述轉換為標準數學符號 (如「X 平方」→「x²」)

### Requirement 6: 五階段引導循環 (FSM 核心)

**User Story:** As a 學生, I want to 在口語講題時獲得系統的階段性引導, so that 我可以完整且深入地理解解題邏輯。

#### Acceptance Criteria

1. WHEN 學生開始口語講題 THEN THE FSM_Controller SHALL 初始化為 LISTENING 狀態並開始記錄
2. WHILE FSM 處於 LISTENING 狀態 WHEN 學生完成一段陳述 THEN THE AI_Tutor SHALL 分析邏輯完整性
3. WHEN 偵測到邏輯缺漏 THEN THE FSM_Controller SHALL 轉移至 PROBING 狀態並生成蘇格拉底式追問
4. WHEN 靜默時間超過設定閾值 THEN THE FSM_Controller SHALL 轉移至 HINTING 狀態
5. WHEN 學生主動說「給我提示」 THEN THE FSM_Controller SHALL 轉移至 HINTING 狀態
6. WHILE FSM 處於 HINTING 狀態 THEN THE AI_Tutor SHALL 提供最小充分提示 (Minimum Sufficient Hint)
7. WHEN 偵測到邏輯謬誤 THEN THE FSM_Controller SHALL 轉移至 REPAIR 狀態並提供修正建議
8. WHEN 概念覆蓋率達到 90% 以上 THEN THE FSM_Controller SHALL 轉移至 CONSOLIDATING 狀態
9. WHILE FSM 處於 CONSOLIDATING 狀態 THEN THE AI_Tutor SHALL 生成觀念總結與遷移練習建議

### Requirement 7: 提示層級控制

**User Story:** As a 學生, I want to 獲得漸進式提示而非直接答案, so that 我可以在最少幫助下自行突破。

#### Acceptance Criteria

1. WHEN 首次進入 HINTING 狀態 THEN THE AI_Tutor SHALL 提供 Level 1 提示 (方向性暗示)
2. WHEN 學生仍無法突破且再次請求提示 THEN THE AI_Tutor SHALL 提供 Level 2 提示 (關鍵步驟提示)
3. WHEN 學生第三次請求提示 THEN THE AI_Tutor SHALL 提供 Level 3 提示 (具體解法框架)
4. THE AI_Tutor SHALL 記錄每次提示的層級以計算提示依賴度

### Requirement 8: 錯題重述與變題測試

**User Story:** As a 學生, I want to 針對歷史錯題重新口語講解並接受變題測試, so that 我可以確認已真正理解該觀念。

#### Acceptance Criteria

1. WHEN 學生選擇錯題重述 THEN THE AI_Tutor SHALL 顯示歷史講題紀錄與當時的卡頓點
2. WHEN 學生完成錯題重述且通過評估 THEN THE RAG_Module SHALL 生成同概念易混淆變題
3. WHEN 學生通過變題測試 THEN THE Error_Book SHALL 將該錯題標記為「已修復」

### Requirement 9: 學習指標計算與儲存

**User Story:** As a 教師/家長, I want to 查看學生的量化學習指標, so that 我可以精確定位學習斷點。

#### Acceptance Criteria

1. WHILE 學生進行口語講題 THEN THE Learning_Metrics SHALL 即時計算 WPM (總字數 / 發話時間分鐘)
2. WHILE 學生進行口語講題 THEN THE Learning_Metrics SHALL 記錄停頓時間點與停頓時長
3. WHEN 口語講題結束 THEN THE Learning_Metrics SHALL 計算停頓比例 (停頓總時長 / 總時長)
4. WHEN 口語講題結束 THEN THE Learning_Metrics SHALL 計算提示依賴度 (1 - Σ(提示次數 × 權重) / 總互動輪數)
5. THE Learning_Metrics SHALL 將所有指標儲存至學習歷程資料庫

### Requirement 10: 教師/家長儀表板

**User Story:** As a 教師/家長, I want to 透過儀表板查看學生學習狀態, so that 我可以適時介入輔導。

#### Acceptance Criteria

1. WHEN 教師/家長登入儀表板 THEN THE Dashboard SHALL 顯示 WPM 趨勢圖、停頓比例分佈、提示依賴度統計
2. THE Dashboard SHALL 依據知識圖譜節點顯示弱點熱力圖 (紅黃綠燈)
3. THE Dashboard SHALL 顯示學生專注時長、分心時段及疲勞週期分析
4. WHEN 點擊特定知識點 THEN THE Dashboard SHALL 展開該知識點的詳細學習歷程

### Requirement 11: LLM 回應生成

**User Story:** As a 系統, I want to 透過本地 LLM 生成教學引導回應, so that 學生可以獲得即時且隱私安全的 AI 輔導。

#### Acceptance Criteria

1. WHEN 需要生成回應 THEN THE RAG_Module SHALL 先檢索相關題目解法與常見迷思概念
2. WHEN RAG 檢索完成 THEN THE AI_Tutor SHALL 將檢索結果注入 Prompt 並呼叫本地 LLM
3. THE AI_Tutor SHALL 使用蘇格拉底式提問風格，不直接給出答案
4. IF LLM 無法確定答案 THEN THE AI_Tutor SHALL 回應「無法判斷」而非生成可能錯誤的內容
5. THE AI_Tutor SHALL 確保 LLM 首字生成時間 (TTFT) 於 5 秒內

### Requirement 12: 系統效能與資源管理

**User Story:** As a 系統管理者, I want to 系統在 MacBook 上流暢運行, so that 學生不會因延遲而中斷學習。

#### Acceptance Criteria

1. THE ASR_Module SHALL 確保轉錄延遲低於 1 秒
2. THE AI_Tutor SHALL 確保 LLM 顯存佔用控制在統一記憶體的 70% 以內
3. IF 系統記憶體不足 THEN THE AI_Tutor SHALL 顯示警告並建議關閉其他應用程式
4. THE AI_Tutor SHALL 支援 4-bit 量化模型以降低資源需求

### Requirement 13: 知識圖譜與題庫管理

**User Story:** As a 系統管理者, I want to 模組化管理知識圖譜與題庫, so that 未來可擴充至其他科目。

#### Acceptance Criteria

1. THE Knowledge_Graph SHALL 採用模組化結構，支援新增科目與單元節點
2. THE Question_Bank SHALL 支援批次匯入題目 (JSON/CSV 格式)
3. WHEN 新增題目 THEN THE Question_Bank SHALL 自動關聯至對應的知識圖譜節點
4. THE Knowledge_Graph SHALL 支援匯出與備份功能
