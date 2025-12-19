"""
Unit tests for the Prompt Builder module.
"""
import pytest
from backend.services.prompt_builder import (
    PromptBuilder,
    PromptContext,
    PromptStyle,
    SYSTEM_PROMPTS,
    HINT_LEVEL_INSTRUCTIONS,
)
from backend.services.fsm_controller import FSMState
from backend.services.hint_controller import HintLevel
from backend.services.rag_module import RetrievedDocument, ContentType


class TestPromptContext:
    """Tests for PromptContext dataclass."""
    
    def test_default_context(self):
        """Test default context values."""
        context = PromptContext()
        
        assert context.question_content == ""
        assert context.student_input == ""
        assert context.conversation_history == []
        assert context.rag_documents == []
        assert context.current_concept is None
        assert context.hint_level is None
        assert context.concept_coverage == 0.0
    
    def test_custom_context(self):
        """Test custom context values."""
        context = PromptContext(
            question_content="What is 2+2?",
            student_input="I think it's 4",
            current_concept="addition",
            hint_level=HintLevel.LEVEL_1,
            concept_coverage=0.75
        )
        
        assert context.question_content == "What is 2+2?"
        assert context.student_input == "I think it's 4"
        assert context.current_concept == "addition"
        assert context.hint_level == HintLevel.LEVEL_1
        assert context.concept_coverage == 0.75


class TestPromptBuilder:
    """Tests for PromptBuilder class."""
    
    def test_init_default(self):
        """Test initialization with defaults."""
        builder = PromptBuilder()
        
        assert builder.style == PromptStyle.SOCRATIC
    
    def test_init_custom_style(self):
        """Test initialization with custom style."""
        builder = PromptBuilder(style=PromptStyle.DIRECT)
        
        assert builder.style == PromptStyle.DIRECT
    
    def test_init_custom_system_prompts(self):
        """Test initialization with custom system prompts."""
        custom_prompts = {
            FSMState.LISTENING: "Custom listening prompt"
        }
        builder = PromptBuilder(custom_system_prompts=custom_prompts)
        
        assert builder._system_prompts[FSMState.LISTENING] == "Custom listening prompt"
        # Other prompts should remain default
        assert builder._system_prompts[FSMState.PROBING] == SYSTEM_PROMPTS[FSMState.PROBING]


class TestBuildSystemPrompt:
    """Tests for build_system_prompt method."""
    
    def test_listening_state(self):
        """Test system prompt for LISTENING state."""
        builder = PromptBuilder()
        
        prompt = builder.build_system_prompt(FSMState.LISTENING)
        
        assert "蘇格拉底" in prompt
        assert "聆聽" in prompt
    
    def test_probing_state(self):
        """Test system prompt for PROBING state."""
        builder = PromptBuilder()
        
        prompt = builder.build_system_prompt(FSMState.PROBING)
        
        assert "引導" in prompt
        assert "問題" in prompt
    
    def test_hinting_state_with_level(self):
        """Test system prompt for HINTING state with hint level."""
        builder = PromptBuilder()
        context = PromptContext(hint_level=HintLevel.LEVEL_2)
        
        prompt = builder.build_system_prompt(FSMState.HINTING, context)
        
        assert "Level 2" in prompt
        assert "關鍵步驟" in prompt
    
    def test_hinting_state_all_levels(self):
        """Test system prompt includes correct hint level instructions."""
        builder = PromptBuilder()
        
        for level in HintLevel:
            context = PromptContext(hint_level=level)
            prompt = builder.build_system_prompt(FSMState.HINTING, context)
            
            assert f"Level {level.value}" in prompt
    
    def test_with_rag_context(self):
        """Test system prompt with RAG documents."""
        builder = PromptBuilder()
        
        rag_docs = [
            RetrievedDocument(
                id="doc1",
                content="This is a solution",
                content_type=ContentType.SOLUTION,
                similarity=0.9
            )
        ]
        context = PromptContext(rag_documents=rag_docs)
        
        prompt = builder.build_system_prompt(FSMState.LISTENING, context)
        
        assert "參考資料" in prompt
        assert "解法" in prompt
        assert "This is a solution" in prompt


class TestBuildUserPrompt:
    """Tests for build_user_prompt method."""
    
    def test_with_question_content(self):
        """Test user prompt includes question content."""
        builder = PromptBuilder()
        context = PromptContext(question_content="Solve x + 5 = 10")
        
        prompt = builder.build_user_prompt(FSMState.LISTENING, context)
        
        assert "題目" in prompt
        assert "Solve x + 5 = 10" in prompt
    
    def test_with_student_input(self):
        """Test user prompt includes student input."""
        builder = PromptBuilder()
        context = PromptContext(student_input="x equals 5")
        
        prompt = builder.build_user_prompt(FSMState.LISTENING, context)
        
        assert "學生回答" in prompt
        assert "x equals 5" in prompt
    
    def test_with_current_concept(self):
        """Test user prompt includes current concept."""
        builder = PromptBuilder()
        context = PromptContext(current_concept="一元一次方程式")
        
        prompt = builder.build_user_prompt(FSMState.LISTENING, context)
        
        assert "目前概念" in prompt
        assert "一元一次方程式" in prompt
    
    def test_with_conversation_history(self):
        """Test user prompt includes conversation history."""
        builder = PromptBuilder()
        context = PromptContext(
            conversation_history=[
                {"speaker": "STUDENT", "content": "我不太懂"},
                {"speaker": "TUTOR", "content": "讓我解釋一下"}
            ]
        )
        
        prompt = builder.build_user_prompt(FSMState.LISTENING, context)
        
        assert "對話紀錄" in prompt
        assert "學生：我不太懂" in prompt
        assert "助教：讓我解釋一下" in prompt
    
    def test_consolidating_state_shows_coverage(self):
        """Test CONSOLIDATING state shows concept coverage."""
        builder = PromptBuilder()
        context = PromptContext(concept_coverage=0.95)
        
        prompt = builder.build_user_prompt(FSMState.CONSOLIDATING, context)
        
        assert "95%" in prompt


class TestBuildFullPrompt:
    """Tests for build_full_prompt method."""
    
    def test_returns_tuple(self):
        """Test that build_full_prompt returns a tuple."""
        builder = PromptBuilder()
        context = PromptContext(student_input="test")
        
        result = builder.build_full_prompt(FSMState.LISTENING, context)
        
        assert isinstance(result, tuple)
        assert len(result) == 2
    
    def test_system_and_user_prompts(self):
        """Test that both prompts are properly built."""
        builder = PromptBuilder()
        context = PromptContext(
            question_content="What is 2+2?",
            student_input="4"
        )
        
        system_prompt, user_prompt = builder.build_full_prompt(
            FSMState.LISTENING,
            context
        )
        
        assert "蘇格拉底" in system_prompt
        assert "What is 2+2?" in user_prompt
        assert "4" in user_prompt


class TestFormatRAGContext:
    """Tests for _format_rag_context method."""
    
    def test_empty_documents(self):
        """Test formatting with no documents."""
        builder = PromptBuilder()
        
        result = builder._format_rag_context([])
        
        assert result == ""
    
    def test_single_document(self):
        """Test formatting with single document."""
        builder = PromptBuilder()
        docs = [
            RetrievedDocument(
                id="1",
                content="Solution content",
                content_type=ContentType.SOLUTION,
                similarity=0.9
            )
        ]
        
        result = builder._format_rag_context(docs)
        
        assert "參考資料" in result
        assert "解法" in result
        assert "Solution content" in result
    
    def test_multiple_document_types(self):
        """Test formatting with different document types."""
        builder = PromptBuilder()
        docs = [
            RetrievedDocument(
                id="1",
                content="Solution",
                content_type=ContentType.SOLUTION,
                similarity=0.9
            ),
            RetrievedDocument(
                id="2",
                content="Misconception",
                content_type=ContentType.MISCONCEPTION,
                similarity=0.8
            ),
            RetrievedDocument(
                id="3",
                content="Concept",
                content_type=ContentType.CONCEPT,
                similarity=0.7
            )
        ]
        
        result = builder._format_rag_context(docs)
        
        assert "解法" in result
        assert "常見迷思" in result
        assert "概念說明" in result
    
    def test_max_docs_limit(self):
        """Test that max_docs limit is respected."""
        builder = PromptBuilder()
        docs = [
            RetrievedDocument(
                id=str(i),
                content=f"Content {i}",
                content_type=ContentType.CONCEPT,
                similarity=0.9
            )
            for i in range(10)
        ]
        
        result = builder._format_rag_context(docs, max_docs=3)
        
        assert "Content 0" in result
        assert "Content 1" in result
        assert "Content 2" in result
        assert "Content 3" not in result


class TestInjectRAGContext:
    """Tests for inject_rag_context method."""
    
    def test_inject_into_prompt(self):
        """Test injecting RAG context into existing prompt."""
        builder = PromptBuilder()
        base_prompt = "This is the base prompt."
        docs = [
            RetrievedDocument(
                id="1",
                content="RAG content",
                content_type=ContentType.SOLUTION,
                similarity=0.9
            )
        ]
        
        result = builder.inject_rag_context(base_prompt, docs)
        
        assert "This is the base prompt." in result
        assert "RAG content" in result
    
    def test_inject_empty_documents(self):
        """Test injecting with no documents returns original."""
        builder = PromptBuilder()
        base_prompt = "Original prompt"
        
        result = builder.inject_rag_context(base_prompt, [])
        
        assert result == "Original prompt"


class TestAnalysisPrompt:
    """Tests for get_analysis_prompt method."""
    
    def test_basic_analysis_prompt(self):
        """Test basic analysis prompt generation."""
        builder = PromptBuilder()
        
        system, user = builder.get_analysis_prompt(
            student_input="x = 5",
            question_content="Solve x + 5 = 10"
        )
        
        assert "JSON" in system
        assert "logic_complete" in system
        assert "x = 5" in user
        assert "Solve x + 5 = 10" in user
    
    def test_analysis_prompt_with_solution(self):
        """Test analysis prompt with standard solution."""
        builder = PromptBuilder()
        
        system, user = builder.get_analysis_prompt(
            student_input="x = 5",
            question_content="Solve x + 5 = 10",
            standard_solution="x = 10 - 5 = 5"
        )
        
        assert "標準解法" in user
        assert "x = 10 - 5 = 5" in user


class TestMisconceptionCheckPrompt:
    """Tests for get_misconception_check_prompt method."""
    
    def test_basic_misconception_prompt(self):
        """Test basic misconception check prompt."""
        builder = PromptBuilder()
        
        system, user = builder.get_misconception_check_prompt(
            student_input="2 + 3 = 6",
            misconceptions=[]
        )
        
        assert "迷思概念" in system
        assert "has_misconception" in system
        assert "2 + 3 = 6" in user
    
    def test_misconception_prompt_with_docs(self):
        """Test misconception prompt with known misconceptions."""
        builder = PromptBuilder()
        misconceptions = [
            RetrievedDocument(
                id="1",
                content="學生常誤以為乘法優先於括號",
                content_type=ContentType.MISCONCEPTION,
                similarity=0.9
            )
        ]
        
        system, user = builder.get_misconception_check_prompt(
            student_input="test",
            misconceptions=misconceptions
        )
        
        assert "已知迷思概念" in user
        assert "乘法優先於括號" in user
