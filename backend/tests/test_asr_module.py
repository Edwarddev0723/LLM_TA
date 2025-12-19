"""
Unit tests for ASR Module.

Tests the Whisper ASR integration and math symbol post-processing.
Requirements: 5.1, 5.3
"""

import pytest
from backend.services.asr_module import (
    ASRModule,
    ASRConfig,
    ASRError,
    ASRConnectionError,
    ASRTranscriptionError,
    WhisperModelSize,
    TranscriptionResult,
    TranscriptionStream,
    WordTimestamp,
    MATH_SYMBOL_MAPPINGS,
    SYMBOL_TO_ORAL_MAPPINGS,
)


class TestASRConfig:
    """Tests for ASRConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = ASRConfig()
        assert config.model_size == WhisperModelSize.BASE
        assert config.language == "zh"
        assert config.task == "transcribe"
        assert config.fp16 is False
        assert config.device == "cpu"
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = ASRConfig(
            model_size=WhisperModelSize.SMALL,
            language="en",
            device="cuda"
        )
        assert config.model_size == WhisperModelSize.SMALL
        assert config.language == "en"
        assert config.device == "cuda"


class TestTranscriptionStream:
    """Tests for TranscriptionStream."""
    
    def test_stream_lifecycle(self):
        """Test stream start and stop."""
        stream = TranscriptionStream()
        assert not stream.is_active
        
        stream.start()
        assert stream.is_active
        
        stream.stop()
        assert not stream.is_active
    
    def test_partial_result_callback(self):
        """Test partial result callback registration and emission."""
        stream = TranscriptionStream()
        results = []
        
        stream.on_partial_result(lambda text: results.append(text))
        stream._emit_partial("test partial")
        
        assert len(results) == 1
        assert results[0] == "test partial"
    
    def test_final_result_callback(self):
        """Test final result callback registration and emission."""
        stream = TranscriptionStream()
        results = []
        
        stream.on_final_result(lambda result: results.append(result))
        
        test_result = TranscriptionResult(
            text="test final",
            confidence=0.95,
            timestamps=[],
            duration=1.5
        )
        stream._emit_final(test_result)
        
        assert len(results) == 1
        assert results[0].text == "test final"
        assert results[0].confidence == 0.95
    
    def test_error_callback(self):
        """Test error callback registration and emission."""
        stream = TranscriptionStream()
        errors = []
        
        stream.on_error(lambda e: errors.append(e))
        
        test_error = ASRTranscriptionError("test error")
        stream._emit_error(test_error)
        
        assert len(errors) == 1
        assert str(errors[0]) == "test error"
    
    def test_multiple_callbacks(self):
        """Test multiple callbacks for same event."""
        stream = TranscriptionStream()
        results1 = []
        results2 = []
        
        stream.on_partial_result(lambda text: results1.append(text))
        stream.on_partial_result(lambda text: results2.append(text))
        
        stream._emit_partial("test")
        
        assert len(results1) == 1
        assert len(results2) == 1
    
    def test_callback_error_isolation(self):
        """Test that callback errors don't break the stream."""
        stream = TranscriptionStream()
        results = []
        
        def failing_callback(text):
            raise ValueError("Callback error")
        
        stream.on_partial_result(failing_callback)
        stream.on_partial_result(lambda text: results.append(text))
        
        # Should not raise, and second callback should still work
        stream._emit_partial("test")
        assert len(results) == 1


class TestASRModule:
    """Tests for ASRModule."""
    
    def test_module_initialization(self):
        """Test module initialization with default config."""
        module = ASRModule()
        assert module.config.model_size == WhisperModelSize.BASE
        assert not module.is_loaded
    
    def test_module_initialization_custom_config(self):
        """Test module initialization with custom config."""
        config = ASRConfig(model_size=WhisperModelSize.TINY)
        module = ASRModule(config)
        assert module.config.model_size == WhisperModelSize.TINY
    
    def test_get_confidence_initial(self):
        """Test initial confidence value."""
        module = ASRModule()
        assert module.get_confidence() == 0.0
    
    def test_start_streaming(self):
        """Test starting a streaming session."""
        module = ASRModule()
        stream = module.start_streaming()
        
        assert stream is not None
        assert stream.is_active
        
        module.stop_streaming()
        assert not stream.is_active
    
    def test_stop_streaming_when_not_active(self):
        """Test stopping streaming when no stream is active."""
        module = ASRModule()
        # Should not raise
        module.stop_streaming()
    
    def test_start_streaming_replaces_existing(self):
        """Test that starting a new stream stops the existing one."""
        module = ASRModule()
        
        stream1 = module.start_streaming()
        assert stream1.is_active
        
        stream2 = module.start_streaming()
        assert not stream1.is_active
        assert stream2.is_active
        
        module.stop_streaming()


class TestMathSymbolPostProcessing:
    """Tests for math symbol post-processing."""
    
    def test_power_symbols(self):
        """Test power symbol conversions."""
        assert ASRModule.post_process_math_symbols("x平方") == "x²"
        assert ASRModule.post_process_math_symbols("X平方") == "x²"
        assert ASRModule.post_process_math_symbols("y平方") == "y²"
        assert ASRModule.post_process_math_symbols("x的平方") == "x²"
        assert ASRModule.post_process_math_symbols("x立方") == "x³"
    
    def test_root_symbols(self):
        """Test root symbol conversions."""
        assert ASRModule.post_process_math_symbols("根號") == "√"
        assert ASRModule.post_process_math_symbols("根号") == "√"
        assert ASRModule.post_process_math_symbols("根號2") == "√2"
        assert ASRModule.post_process_math_symbols("根號x") == "√x"
    
    def test_fraction_symbols(self):
        """Test fraction symbol conversions."""
        assert ASRModule.post_process_math_symbols("二分之一") == "½"
        assert ASRModule.post_process_math_symbols("三分之一") == "⅓"
        assert ASRModule.post_process_math_symbols("四分之一") == "¼"
    
    def test_greek_letters(self):
        """Test Greek letter conversions."""
        assert ASRModule.post_process_math_symbols("派") == "π"
        assert ASRModule.post_process_math_symbols("圓周率") == "π"
        assert ASRModule.post_process_math_symbols("阿爾法") == "α"
        assert ASRModule.post_process_math_symbols("西塔") == "θ"
    
    def test_comparison_operators(self):
        """Test comparison operator conversions."""
        assert ASRModule.post_process_math_symbols("大於") == ">"
        assert ASRModule.post_process_math_symbols("小於") == "<"
        assert ASRModule.post_process_math_symbols("大於等於") == "≥"
        assert ASRModule.post_process_math_symbols("小於等於") == "≤"
        assert ASRModule.post_process_math_symbols("不等於") == "≠"
        assert ASRModule.post_process_math_symbols("等於") == "="
    
    def test_arithmetic_operators(self):
        """Test arithmetic operator conversions."""
        assert ASRModule.post_process_math_symbols("加") == "+"
        assert ASRModule.post_process_math_symbols("減") == "-"
        assert ASRModule.post_process_math_symbols("乘") == "×"
        assert ASRModule.post_process_math_symbols("除") == "÷"
    
    def test_set_notation(self):
        """Test set notation conversions."""
        assert ASRModule.post_process_math_symbols("屬於") == "∈"
        assert ASRModule.post_process_math_symbols("子集") == "⊂"
        assert ASRModule.post_process_math_symbols("聯集") == "∪"
        assert ASRModule.post_process_math_symbols("交集") == "∩"
    
    def test_geometry_symbols(self):
        """Test geometry symbol conversions."""
        assert ASRModule.post_process_math_symbols("角") == "∠"
        assert ASRModule.post_process_math_symbols("度") == "°"
        assert ASRModule.post_process_math_symbols("垂直") == "⊥"
        assert ASRModule.post_process_math_symbols("平行") == "∥"
    
    def test_complex_expression(self):
        """Test conversion of complex expressions."""
        input_text = "x平方加y平方等於根號2"
        expected = "x²+y²=√2"
        assert ASRModule.post_process_math_symbols(input_text) == expected
    
    def test_mixed_text(self):
        """Test conversion with mixed text and math."""
        input_text = "如果x平方大於等於0，則x屬於實數"
        result = ASRModule.post_process_math_symbols(input_text)
        assert "x²" in result
        assert "≥" in result
        assert "∈" in result
    
    def test_no_conversion_needed(self):
        """Test text that doesn't need conversion."""
        input_text = "這是一段普通的文字"
        assert ASRModule.post_process_math_symbols(input_text) == input_text
    
    def test_empty_string(self):
        """Test empty string input."""
        assert ASRModule.post_process_math_symbols("") == ""


class TestSymbolToOralConversion:
    """Tests for converting symbols back to oral descriptions."""
    
    def test_power_symbols_reverse(self):
        """Test reverse conversion of power symbols."""
        assert ASRModule.convert_symbols_to_oral("x²") == "x平方"
        assert ASRModule.convert_symbols_to_oral("y²") == "y平方"
        assert ASRModule.convert_symbols_to_oral("x³") == "x立方"
    
    def test_root_symbols_reverse(self):
        """Test reverse conversion of root symbols."""
        assert ASRModule.convert_symbols_to_oral("√2") == "根號2"
        assert ASRModule.convert_symbols_to_oral("√x") == "根號x"
    
    def test_comparison_operators_reverse(self):
        """Test reverse conversion of comparison operators."""
        assert ASRModule.convert_symbols_to_oral(">") == "大於"
        assert ASRModule.convert_symbols_to_oral("<") == "小於"
        assert ASRModule.convert_symbols_to_oral("≥") == "大於等於"
        assert ASRModule.convert_symbols_to_oral("≤") == "小於等於"


class TestTranscriptionResult:
    """Tests for TranscriptionResult dataclass."""
    
    def test_basic_result(self):
        """Test basic transcription result."""
        result = TranscriptionResult(
            text="測試文字",
            confidence=0.95
        )
        assert result.text == "測試文字"
        assert result.confidence == 0.95
        assert result.timestamps == []
        assert result.duration == 0.0
        assert result.language == "zh"
    
    def test_result_with_timestamps(self):
        """Test transcription result with timestamps."""
        timestamps = [
            WordTimestamp(word="測試", start_time=0.0, end_time=0.5),
            WordTimestamp(word="文字", start_time=0.5, end_time=1.0)
        ]
        result = TranscriptionResult(
            text="測試文字",
            confidence=0.95,
            timestamps=timestamps,
            duration=1.0
        )
        assert len(result.timestamps) == 2
        assert result.timestamps[0].word == "測試"
        assert result.duration == 1.0


class TestWordTimestamp:
    """Tests for WordTimestamp dataclass."""
    
    def test_word_timestamp(self):
        """Test word timestamp creation."""
        ts = WordTimestamp(word="測試", start_time=0.0, end_time=0.5)
        assert ts.word == "測試"
        assert ts.start_time == 0.0
        assert ts.end_time == 0.5


class TestMathSymbolMappings:
    """Tests for math symbol mapping dictionaries."""
    
    def test_mappings_not_empty(self):
        """Test that mappings are not empty."""
        assert len(MATH_SYMBOL_MAPPINGS) > 0
        assert len(SYMBOL_TO_ORAL_MAPPINGS) > 0
    
    def test_key_mappings_exist(self):
        """Test that key mappings exist."""
        # Check some essential mappings
        assert "x平方" in MATH_SYMBOL_MAPPINGS
        assert "根號" in MATH_SYMBOL_MAPPINGS
        assert "大於" in MATH_SYMBOL_MAPPINGS
        assert "等於" in MATH_SYMBOL_MAPPINGS
    
    def test_reverse_mappings_exist(self):
        """Test that reverse mappings exist."""
        assert "x²" in SYMBOL_TO_ORAL_MAPPINGS
        assert "√" in SYMBOL_TO_ORAL_MAPPINGS
        assert ">" in SYMBOL_TO_ORAL_MAPPINGS
        assert "=" in SYMBOL_TO_ORAL_MAPPINGS
