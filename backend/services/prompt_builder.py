"""
Prompt Builder for the AI Math Tutor system.
Builds prompts for different FSM states with RAG context injection.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

from backend.services.fsm_controller import FSMState
from backend.services.hint_controller import HintLevel
from backend.services.rag_module import RetrievedDocument


class PromptStyle(str, Enum):
    """Styles of prompts for different teaching approaches."""
    SOCRATIC = "socratic"  # 蘇格拉底式提問
    DIRECT = "direct"      # 直接回答
    ENCOURAGING = "encouraging"  # 鼓勵式


@dataclass
class PromptContext:
    """Context for building prompts."""
    question_content: str = ""
    student_input: str = ""
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    rag_documents: List[RetrievedDocument] = field(default_factory=list)
    current_concept: Optional[str] = None
    hint_level: Optional[HintLevel] = None
    concept_coverage: float = 0.0
    student_name: Optional[str] = None


# 核心禁止規則 - 所有狀態共用
CORE_PROHIBITION_RULES = """
【絕對禁止事項 - 最高優先級】
1. 在學生說出正確答案之前，絕對禁止透露：
   - 題目的最終答案（數值、結果）
   - 完整的解題步驟或流程
   - 關鍵的計算過程
2. 即使學生直接問「答案是什麼」，也必須拒絕並引導思考
3. 只有當學生自己說出正確答案後，才能確認答案正確

【允許的引導方式】
- 提出引導性問題
- 確認學生的思考方向是否正確
- 給予方向性的暗示（不含具體數值）
- 鼓勵學生繼續嘗試
"""

# System prompt templates for different FSM states
SYSTEM_PROMPTS = {
    FSMState.LISTENING: f"""你是一位耐心且富有智慧的數學家教，採用蘇格拉底式教學法。

{CORE_PROHIBITION_RULES}

你的角色：
- 仔細聆聽學生的解題思路
- 透過提問引導學生自己發現問題
- 保持鼓勵和支持的態度

當學生講解時：
- 確認你理解了他們的思路
- 注意邏輯是否完整
- 找出可能的概念缺漏
- 絕對不要說出答案或完整解法

回應風格：
- 使用繁體中文
- 語氣親切友善
- 簡潔明瞭""",

    FSMState.ANALYZING: f"""你是一位數學教學分析專家。

{CORE_PROHIBITION_RULES}

你的任務：
- 分析學生的解題思路
- 識別邏輯缺漏或錯誤
- 評估概念理解程度

分析重點：
- 解題步驟是否完整
- 數學概念是否正確應用
- 計算過程是否有誤

請以 JSON 格式回應分析結果。注意：分析結果中不要包含答案。""",

    FSMState.PROBING: f"""你是一位善於引導的數學家教，採用蘇格拉底式提問法。

{CORE_PROHIBITION_RULES}

你的任務：
- 針對學生思路中的缺漏提出引導性問題
- 不要直接指出錯誤，更不要說出正確答案
- 透過問題讓學生自己發現問題

提問原則：
- 問題要具體且有針對性
- 一次只問一個問題
- 問題要能引導學生思考
- 問題中不能包含答案的暗示

回應風格：
- 使用繁體中文
- 語氣溫和鼓勵
- 避免讓學生感到挫折""",

    FSMState.HINTING: f"""你是一位提供漸進式提示的數學家教。

{CORE_PROHIBITION_RULES}

你的任務：
- 根據提示層級提供適當的幫助
- Level 1: 只給方向性暗示，不透露任何具體步驟或數值
- Level 2: 提供關鍵步驟的提示，但不給出計算結果
- Level 3: 給出解法框架，但讓學生自己計算出答案

重要原則：
- 絕對不要直接給出最終答案
- 絕對不要給出完整的解題過程
- 讓學生保有自己解題的成就感
- 提示要循序漸進

回應風格：
- 使用繁體中文
- 語氣鼓勵支持
- 簡潔有力""",

    FSMState.REPAIR: f"""你是一位幫助學生修正錯誤的數學家教。

{CORE_PROHIBITION_RULES}

你的任務：
- 溫和地指出學生的錯誤方向（不是直接給正確答案）
- 解釋為什麼這個方向可能有問題
- 引導學生重新思考，而不是告訴他正確答案

修正原則：
- 不要讓學生感到羞愧
- 將錯誤視為學習機會
- 引導學生自己發現正確的方向
- 絕對不要在修正時說出正確答案

回應風格：
- 使用繁體中文
- 語氣溫和理解
- 提供方向性的引導""",

    FSMState.CONSOLIDATING: f"""你是一位幫助學生鞏固知識的數學家教。

注意：只有在學生已經自己說出正確答案後，才會進入此狀態。
此時可以確認答案正確，並進行總結。

你的任務：
- 確認學生的答案正確
- 總結本次學習的重點概念
- 強調學生做得好的地方
- 提供延伸學習的建議

總結原則：
- 肯定學生的努力和進步
- 清楚列出學到的概念
- 建議相關的練習題目

回應風格：
- 使用繁體中文
- 語氣正面鼓勵
- 結構清晰""",

    FSMState.IDLE: f"""你是一位友善的數學家教助手。

{CORE_PROHIBITION_RULES}

你的任務：
- 歡迎學生開始學習
- 了解學生想要練習的內容
- 引導學生選擇題目

回應風格：
- 使用繁體中文
- 語氣親切友善
- 簡潔明瞭"""
}


# Hint level specific instructions
HINT_LEVEL_INSTRUCTIONS = {
    HintLevel.LEVEL_1: """
【提示層級：Level 1 - 方向性暗示】
- 只提供思考的方向，絕對不透露任何數值或答案
- 不要透露具體的解題步驟
- 用問題引導學生思考
- 例如：「你有沒有想過從另一個角度來看這個問題？」
- 禁止：說出任何計算結果或中間數值""",

    HintLevel.LEVEL_2: """
【提示層級：Level 2 - 關鍵步驟提示】
- 可以提示關鍵的解題方向
- 但絕對不要給出任何數值答案
- 讓學生自己完成計算
- 例如：「這題的關鍵是要先找出兩個變數之間的關係」
- 禁止：說出具體數字、計算結果、或最終答案""",

    HintLevel.LEVEL_3: """
【提示層級：Level 3 - 解法框架提示】
- 可以提供解題的步驟框架
- 但每個步驟的計算結果必須由學生自己算出
- 確保學生理解每個步驟的原因
- 例如：「解這題的步驟是：1. 先移項... 2. 然後化簡... 3. 最後求解...」
- 禁止：在框架中包含任何具體數值或最終答案"""
}


class PromptBuilder:
    """
    Builder for constructing prompts for the AI Math Tutor.
    
    Supports:
    - Different FSM state-specific prompts
    - RAG context injection
    - Hint level customization
    - Conversation history integration
    """
    
    def __init__(
        self,
        style: PromptStyle = PromptStyle.SOCRATIC,
        custom_system_prompts: Optional[Dict[FSMState, str]] = None
    ):
        """
        Initialize the Prompt Builder.
        
        Args:
            style: The teaching style to use
            custom_system_prompts: Optional custom system prompts by state
        """
        self.style = style
        self._system_prompts = {**SYSTEM_PROMPTS}
        
        if custom_system_prompts:
            self._system_prompts.update(custom_system_prompts)
    
    def build_system_prompt(
        self,
        state: FSMState,
        context: Optional[PromptContext] = None
    ) -> str:
        """
        Build the system prompt for a given FSM state.
        
        Args:
            state: The current FSM state
            context: Optional context for customization
            
        Returns:
            The system prompt string
        """
        base_prompt = self._system_prompts.get(state, SYSTEM_PROMPTS[FSMState.LISTENING])
        
        # Add hint level instructions if in HINTING state
        if state == FSMState.HINTING and context and context.hint_level:
            hint_instruction = HINT_LEVEL_INSTRUCTIONS.get(context.hint_level, "")
            base_prompt = f"{base_prompt}\n{hint_instruction}"
        
        # Add RAG context if available
        if context and context.rag_documents:
            rag_context = self._format_rag_context(context.rag_documents)
            base_prompt = f"{base_prompt}\n\n{rag_context}"
        
        return base_prompt
    
    def build_user_prompt(
        self,
        state: FSMState,
        context: PromptContext
    ) -> str:
        """
        Build the user prompt for a given FSM state.
        
        Args:
            state: The current FSM state
            context: The prompt context
            
        Returns:
            The user prompt string
        """
        parts = []
        
        # Add question content if available
        if context.question_content:
            parts.append(f"【題目】\n{context.question_content}")
        
        # Add current concept if available
        if context.current_concept:
            parts.append(f"【目前概念】{context.current_concept}")
        
        # Add conversation history summary if available (includes student transcript)
        if context.conversation_history:
            history_summary = self._format_conversation_history(
                context.conversation_history,
                max_turns=5
            )
            parts.append(f"【對話紀錄（含學生逐字稿）】\n{history_summary}")
        
        # Add current student input (latest transcript)
        if context.student_input:
            parts.append(f"【學生最新回答（語音逐字稿）】\n{context.student_input}")
        
        # Add reminder about not revealing answer
        parts.append("【重要提醒】請記住：在學生自己說出正確答案之前，絕對不要透露答案或完整解法。")
        
        # Add state-specific instructions
        state_instruction = self._get_state_instruction(state, context)
        if state_instruction:
            parts.append(state_instruction)
        
        return "\n\n".join(parts)
    
    def build_full_prompt(
        self,
        state: FSMState,
        context: PromptContext
    ) -> tuple[str, str]:
        """
        Build both system and user prompts.
        
        Args:
            state: The current FSM state
            context: The prompt context
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = self.build_system_prompt(state, context)
        user_prompt = self.build_user_prompt(state, context)
        
        return system_prompt, user_prompt

    def _format_rag_context(
        self,
        documents: List[RetrievedDocument],
        max_docs: int = 5
    ) -> str:
        """
        Format RAG retrieved documents into context string.
        
        Args:
            documents: List of retrieved documents
            max_docs: Maximum number of documents to include
            
        Returns:
            Formatted context string
        """
        if not documents:
            return ""
        
        parts = ["【參考資料】"]
        
        for i, doc in enumerate(documents[:max_docs]):
            doc_type_labels = {
                "SOLUTION": "解法",
                "MISCONCEPTION": "常見迷思",
                "CONCEPT": "概念說明",
                "HINT": "提示",
                "QUESTION": "相關題目"
            }
            
            type_label = doc_type_labels.get(doc.content_type.value, "參考")
            parts.append(f"\n{i + 1}. 【{type_label}】\n{doc.content}")
        
        return "\n".join(parts)
    
    def _format_conversation_history(
        self,
        history: List[Dict[str, str]],
        max_turns: int = 5
    ) -> str:
        """
        Format conversation history into a summary string.
        
        Args:
            history: List of conversation turns
            max_turns: Maximum number of turns to include
            
        Returns:
            Formatted history string
        """
        if not history:
            return ""
        
        # Take the most recent turns
        recent_history = history[-max_turns:]
        
        parts = []
        for turn in recent_history:
            speaker = turn.get("speaker", "Unknown")
            content = turn.get("content", "")
            
            if speaker.upper() == "STUDENT":
                parts.append(f"學生：{content}")
            else:
                parts.append(f"助教：{content}")
        
        return "\n".join(parts)
    
    def _get_state_instruction(
        self,
        state: FSMState,
        context: PromptContext
    ) -> str:
        """
        Get state-specific instruction for the user prompt.
        
        Args:
            state: The current FSM state
            context: The prompt context
            
        Returns:
            State-specific instruction string
        """
        instructions = {
            FSMState.LISTENING: "請仔細聆聽學生的解題思路，並準備給予回饋。",
            
            FSMState.ANALYZING: "請分析學生的回答，識別任何邏輯缺漏或錯誤。",
            
            FSMState.PROBING: "請針對學生思路中的缺漏，提出一個引導性的問題。",
            
            FSMState.HINTING: self._get_hint_instruction(context),
            
            FSMState.REPAIR: "請溫和地指出學生的錯誤，並引導他們理解正確的概念。",
            
            FSMState.CONSOLIDATING: f"學生已完成本題的學習（概念覆蓋率：{context.concept_coverage:.0%}）。請總結學習重點並給予鼓勵。",
            
            FSMState.IDLE: "請歡迎學生並詢問他們想要練習什麼內容。"
        }
        
        return instructions.get(state, "")
    
    def _get_hint_instruction(self, context: PromptContext) -> str:
        """
        Get hint-specific instruction based on hint level.
        
        Args:
            context: The prompt context
            
        Returns:
            Hint instruction string
        """
        if not context.hint_level:
            return "請提供適當的提示幫助學生。"
        
        level_instructions = {
            HintLevel.LEVEL_1: "請提供 Level 1 提示：只給方向性暗示，不透露具體步驟。",
            HintLevel.LEVEL_2: "請提供 Level 2 提示：提示關鍵步驟，但不給完整解法。",
            HintLevel.LEVEL_3: "請提供 Level 3 提示：給出具體的解法框架，但讓學生自己計算。"
        }
        
        return level_instructions.get(context.hint_level, "請提供適當的提示幫助學生。")
    
    def inject_rag_context(
        self,
        base_prompt: str,
        documents: List[RetrievedDocument]
    ) -> str:
        """
        Inject RAG context into an existing prompt.
        
        Args:
            base_prompt: The base prompt to inject into
            documents: RAG retrieved documents
            
        Returns:
            Prompt with RAG context injected
        """
        if not documents:
            return base_prompt
        
        rag_context = self._format_rag_context(documents)
        return f"{base_prompt}\n\n{rag_context}"
    
    def get_analysis_prompt(
        self,
        student_input: str,
        question_content: str,
        standard_solution: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Build a prompt specifically for analyzing student responses.
        
        Args:
            student_input: The student's response
            question_content: The question being answered
            standard_solution: Optional standard solution for reference
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = """你是一位數學教學分析專家。請分析學生的解題思路並以 JSON 格式回應。

【重要】分析結果中絕對不要包含：
- 題目的正確答案
- 完整的解題步驟
- 任何可能讓學生直接得知答案的資訊

回應格式：
{
    "logic_complete": true/false,  // 邏輯是否完整
    "logic_gap": true/false,       // 是否有邏輯缺漏
    "logic_error": true/false,     // 是否有邏輯錯誤
    "error_type": "CALCULATION" | "CONCEPT" | "CARELESS" | null,  // 錯誤類型
    "missing_concepts": [],        // 缺漏的概念列表（不要包含答案）
    "covered_concepts": [],        // 已涵蓋的概念列表
    "feedback": ""                 // 簡短回饋（不要透露答案）
}"""
        
        user_parts = [
            f"【題目】\n{question_content}",
            f"【學生回答（語音逐字稿）】\n{student_input}"
        ]
        
        if standard_solution:
            user_parts.append(f"【標準解法（僅供內部分析參考，不要在回饋中透露）】\n{standard_solution}")
        
        user_parts.append("請分析學生的回答並以 JSON 格式回應。注意：feedback 欄位中絕對不要包含答案或完整解法。")
        
        user_prompt = "\n\n".join(user_parts)
        
        return system_prompt, user_prompt
    
    def get_misconception_check_prompt(
        self,
        student_input: str,
        misconceptions: List[RetrievedDocument]
    ) -> tuple[str, str]:
        """
        Build a prompt for checking if student exhibits known misconceptions.
        
        Args:
            student_input: The student's response
            misconceptions: Known misconceptions from RAG
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = """你是一位數學迷思概念分析專家。請檢查學生的回答是否展現了已知的迷思概念。

回應格式：
{
    "has_misconception": true/false,
    "matched_misconception": "迷思概念描述" | null,
    "confidence": 0.0-1.0,
    "correction_suggestion": "修正建議" | null
}"""
        
        user_parts = [f"【學生回答】\n{student_input}"]
        
        if misconceptions:
            misconception_list = "\n".join([
                f"- {doc.content}" for doc in misconceptions
            ])
            user_parts.append(f"【已知迷思概念】\n{misconception_list}")
        
        user_parts.append("請檢查學生是否展現了上述迷思概念。")
        
        user_prompt = "\n\n".join(user_parts)
        
        return system_prompt, user_prompt
