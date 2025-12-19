"""
ASR Module - Whisper-based Automatic Speech Recognition

This module provides speech-to-text transcription using OpenAI's Whisper model,
with support for streaming transcription and math symbol post-processing.

Requirements: 5.1, 5.3
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional, List
import threading
import queue
import time


class ASRError(Exception):
    """Base exception for ASR-related errors."""
    pass


class ASRConnectionError(ASRError):
    """Raised when ASR model cannot be loaded."""
    pass


class ASRTranscriptionError(ASRError):
    """Raised when transcription fails."""
    pass


class WhisperModelSize(str, Enum):
    """Available Whisper model sizes."""
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


@dataclass
class WordTimestamp:
    """Represents a word with its timing information."""
    word: str
    start_time: float
    end_time: float


@dataclass
class TranscriptionResult:
    """Result of a transcription operation."""
    text: str
    confidence: float
    timestamps: List[WordTimestamp] = field(default_factory=list)
    duration: float = 0.0
    language: str = "zh"


@dataclass
class ASRConfig:
    """Configuration for the ASR module."""
    model_size: WhisperModelSize = WhisperModelSize.BASE
    language: str = "zh"  # Chinese
    task: str = "transcribe"
    fp16: bool = False  # Use FP32 for CPU compatibility
    device: str = "cpu"  # Default to CPU for MacBook compatibility
    silence_threshold: float = 0.5  # Seconds of silence to detect pause
    max_audio_length: float = 30.0  # Maximum audio length in seconds


class TranscriptionStream:
    """
    Handles streaming transcription with callbacks for partial and final results.
    """
    
    def __init__(self):
        self._partial_callbacks: List[Callable[[str], None]] = []
        self._final_callbacks: List[Callable[[TranscriptionResult], None]] = []
        self._error_callbacks: List[Callable[[Exception], None]] = []
        self._is_active = False
        self._audio_queue: queue.Queue = queue.Queue()
        self._processing_thread: Optional[threading.Thread] = None
    
    def on_partial_result(self, callback: Callable[[str], None]) -> None:
        """Register a callback for partial transcription results."""
        self._partial_callbacks.append(callback)
    
    def on_final_result(self, callback: Callable[[TranscriptionResult], None]) -> None:
        """Register a callback for final transcription results."""
        self._final_callbacks.append(callback)
    
    def on_error(self, callback: Callable[[Exception], None]) -> None:
        """Register a callback for errors."""
        self._error_callbacks.append(callback)
    
    def _emit_partial(self, text: str) -> None:
        """Emit partial result to all registered callbacks."""
        for callback in self._partial_callbacks:
            try:
                callback(text)
            except Exception:
                pass  # Don't let callback errors break the stream
    
    def _emit_final(self, result: TranscriptionResult) -> None:
        """Emit final result to all registered callbacks."""
        for callback in self._final_callbacks:
            try:
                callback(result)
            except Exception:
                pass
    
    def _emit_error(self, error: Exception) -> None:
        """Emit error to all registered callbacks."""
        for callback in self._error_callbacks:
            try:
                callback(error)
            except Exception:
                pass
    
    @property
    def is_active(self) -> bool:
        """Check if the stream is currently active."""
        return self._is_active
    
    def start(self) -> None:
        """Start the transcription stream."""
        self._is_active = True
    
    def stop(self) -> None:
        """Stop the transcription stream."""
        self._is_active = False
    
    def add_audio_chunk(self, audio_data: bytes) -> None:
        """Add an audio chunk to the processing queue."""
        if self._is_active:
            self._audio_queue.put(audio_data)


# Math symbol mapping: oral description -> mathematical symbol
MATH_SYMBOL_MAPPINGS = {
    # Powers and roots (Chinese)
    "x平方": "x²",
    "X平方": "x²",
    "y平方": "y²",
    "Y平方": "y²",
    "a平方": "a²",
    "b平方": "b²",
    "n平方": "n²",
    "x的平方": "x²",
    "y的平方": "y²",
    "a的平方": "a²",
    "b的平方": "b²",
    "x立方": "x³",
    "X立方": "x³",
    "y立方": "y³",
    "x的立方": "x³",
    "y的立方": "y³",
    "根號": "√",
    "根号": "√",
    "開根號": "√",
    "开根号": "√",
    "根號2": "√2",
    "根号2": "√2",
    "根號3": "√3",
    "根号3": "√3",
    "根號x": "√x",
    "根号x": "√x",
    
    # Fractions (Chinese)
    "二分之一": "½",
    "三分之一": "⅓",
    "四分之一": "¼",
    "三分之二": "⅔",
    "四分之三": "¾",
    "分之": "/",
    
    # Greek letters (Chinese)
    "派": "π",
    "圓周率": "π",
    "圆周率": "π",
    "阿爾法": "α",
    "阿尔法": "α",
    "貝塔": "β",
    "贝塔": "β",
    "伽馬": "γ",
    "伽马": "γ",
    "德爾塔": "δ",
    "德尔塔": "δ",
    "西塔": "θ",
    "theta": "θ",
    
    # Comparison operators (Chinese)
    "大於": ">",
    "大于": ">",
    "小於": "<",
    "小于": "<",
    "大於等於": "≥",
    "大于等于": "≥",
    "小於等於": "≤",
    "小于等于": "≤",
    "不等於": "≠",
    "不等于": "≠",
    "等於": "=",
    "等于": "=",
    "約等於": "≈",
    "约等于": "≈",
    
    # Arithmetic operators (Chinese)
    "加": "+",
    "減": "-",
    "减": "-",
    "乘": "×",
    "乘以": "×",
    "除": "÷",
    "除以": "÷",
    "正負": "±",
    "正负": "±",
    
    # Set notation (Chinese)
    "屬於": "∈",
    "属于": "∈",
    "不屬於": "∉",
    "不属于": "∉",
    "子集": "⊂",
    "聯集": "∪",
    "联集": "∪",
    "交集": "∩",
    "空集": "∅",
    
    # Calculus (Chinese)
    "無限": "∞",
    "无限": "∞",
    "無窮": "∞",
    "无穷": "∞",
    "積分": "∫",
    "积分": "∫",
    "微分": "d",
    "偏微分": "∂",
    "求和": "Σ",
    "連乘": "∏",
    "连乘": "∏",
    
    # Geometry (Chinese)
    "角": "∠",
    "度": "°",
    "垂直": "⊥",
    "平行": "∥",
    "三角形": "△",
    "圓": "○",
    "圆": "○",
    
    # Logic (Chinese)
    "且": "∧",
    "或": "∨",
    "非": "¬",
    "若且唯若": "⟺",
    "若則": "⟹",
    "若则": "⟹",
    "因此": "∴",
    "因為": "∵",
    "因为": "∵",
}

# Reverse mapping for converting symbols back to oral descriptions
SYMBOL_TO_ORAL_MAPPINGS = {
    "x²": "x平方",
    "y²": "y平方",
    "a²": "a平方",
    "b²": "b平方",
    "n²": "n平方",
    "x³": "x立方",
    "y³": "y立方",
    "√": "根號",
    "√2": "根號2",
    "√3": "根號3",
    "√x": "根號x",
    "½": "二分之一",
    "⅓": "三分之一",
    "¼": "四分之一",
    "⅔": "三分之二",
    "¾": "四分之三",
    "π": "圓周率",
    "α": "阿爾法",
    "β": "貝塔",
    "γ": "伽馬",
    "δ": "德爾塔",
    "θ": "西塔",
    ">": "大於",
    "<": "小於",
    "≥": "大於等於",
    "≤": "小於等於",
    "≠": "不等於",
    "=": "等於",
    "≈": "約等於",
    "+": "加",
    "-": "減",
    "×": "乘",
    "÷": "除",
    "±": "正負",
    "∈": "屬於",
    "∉": "不屬於",
    "⊂": "子集",
    "∪": "聯集",
    "∩": "交集",
    "∅": "空集",
    "∞": "無限",
    "∫": "積分",
    "∂": "偏微分",
    "Σ": "求和",
    "∏": "連乘",
    "∠": "角",
    "°": "度",
    "⊥": "垂直",
    "∥": "平行",
    "△": "三角形",
    "○": "圓",
    "∧": "且",
    "∨": "或",
    "¬": "非",
    "⟺": "若且唯若",
    "⟹": "若則",
    "∴": "因此",
    "∵": "因為",
}


class ASRModule:
    """
    ASR Module using OpenAI's Whisper for speech-to-text transcription.
    
    Provides:
    - Audio file transcription
    - Streaming transcription support
    - Math symbol post-processing
    - Confidence scoring
    
    Requirements: 5.1 (語音輸入與即時轉錄)
    """
    
    def __init__(self, config: Optional[ASRConfig] = None):
        """
        Initialize the ASR module.
        
        Args:
            config: ASR configuration. Uses defaults if not provided.
        """
        self.config = config or ASRConfig()
        self._model = None
        self._current_stream: Optional[TranscriptionStream] = None
        self._last_confidence: float = 0.0
        self._is_loaded = False
    
    def load_model(self) -> None:
        """
        Load the Whisper model.
        
        Raises:
            ASRConnectionError: If model cannot be loaded.
        """
        try:
            import whisper
            self._model = whisper.load_model(
                self.config.model_size.value,
                device=self.config.device
            )
            self._is_loaded = True
        except ImportError:
            raise ASRConnectionError(
                "Whisper is not installed. Please install with: pip install openai-whisper"
            )
        except Exception as e:
            raise ASRConnectionError(f"Failed to load Whisper model: {str(e)}")
    
    @property
    def is_loaded(self) -> bool:
        """Check if the model is loaded."""
        return self._is_loaded
    
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """
        Transcribe an audio file.
        
        Args:
            audio_path: Path to the audio file.
            language: Language code (e.g., 'zh' for Chinese). Uses config default if not provided.
        
        Returns:
            TranscriptionResult with transcribed text and metadata.
        
        Raises:
            ASRConnectionError: If model is not loaded.
            ASRTranscriptionError: If transcription fails.
        """
        if not self._is_loaded:
            self.load_model()
        
        try:
            result = self._model.transcribe(
                audio_path,
                language=language or self.config.language,
                task=self.config.task,
                fp16=self.config.fp16
            )
            
            # Extract word timestamps if available
            timestamps = []
            if "segments" in result:
                for segment in result["segments"]:
                    if "words" in segment:
                        for word_info in segment["words"]:
                            timestamps.append(WordTimestamp(
                                word=word_info.get("word", ""),
                                start_time=word_info.get("start", 0.0),
                                end_time=word_info.get("end", 0.0)
                            ))
            
            # Calculate confidence from segments
            confidence = 1.0
            if "segments" in result and result["segments"]:
                avg_no_speech_prob = sum(
                    seg.get("no_speech_prob", 0) for seg in result["segments"]
                ) / len(result["segments"])
                confidence = 1.0 - avg_no_speech_prob
            
            self._last_confidence = confidence
            
            # Calculate duration
            duration = 0.0
            if "segments" in result and result["segments"]:
                duration = result["segments"][-1].get("end", 0.0)
            
            transcription_result = TranscriptionResult(
                text=result.get("text", "").strip(),
                confidence=confidence,
                timestamps=timestamps,
                duration=duration,
                language=result.get("language", self.config.language)
            )
            
            return transcription_result
            
        except FileNotFoundError:
            raise ASRTranscriptionError(f"Audio file not found: {audio_path}")
        except Exception as e:
            raise ASRTranscriptionError(f"Transcription failed: {str(e)}")
    
    def transcribe_audio_data(
        self,
        audio_data: bytes,
        sample_rate: int = 16000,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """
        Transcribe raw audio data.
        
        Args:
            audio_data: Raw audio bytes (PCM format expected).
            sample_rate: Audio sample rate in Hz.
            language: Language code.
        
        Returns:
            TranscriptionResult with transcribed text and metadata.
        """
        import tempfile
        import os
        import numpy as np
        
        if not self._is_loaded:
            self.load_model()
        
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Resample to 16kHz if needed (Whisper expects 16kHz)
            if sample_rate != 16000:
                # Simple resampling - for production, use librosa or scipy
                ratio = 16000 / sample_rate
                new_length = int(len(audio_array) * ratio)
                indices = np.linspace(0, len(audio_array) - 1, new_length).astype(int)
                audio_array = audio_array[indices]
            
            # Save to temporary file for Whisper
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_path = tmp_file.name
                # Write WAV header and data
                self._write_wav(tmp_file, audio_array, 16000)
            
            try:
                result = self.transcribe(tmp_path, language)
                return result
            finally:
                os.unlink(tmp_path)
                
        except Exception as e:
            raise ASRTranscriptionError(f"Failed to transcribe audio data: {str(e)}")
    
    def _write_wav(self, file, audio_array, sample_rate: int) -> None:
        """Write audio array to WAV file."""
        import struct
        
        # Convert float32 to int16
        audio_int16 = (audio_array * 32767).astype('int16')
        
        # WAV header
        num_channels = 1
        bits_per_sample = 16
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8
        data_size = len(audio_int16) * 2
        
        # Write RIFF header
        file.write(b'RIFF')
        file.write(struct.pack('<I', 36 + data_size))
        file.write(b'WAVE')
        
        # Write fmt chunk
        file.write(b'fmt ')
        file.write(struct.pack('<I', 16))  # Chunk size
        file.write(struct.pack('<H', 1))   # Audio format (PCM)
        file.write(struct.pack('<H', num_channels))
        file.write(struct.pack('<I', sample_rate))
        file.write(struct.pack('<I', byte_rate))
        file.write(struct.pack('<H', block_align))
        file.write(struct.pack('<H', bits_per_sample))
        
        # Write data chunk
        file.write(b'data')
        file.write(struct.pack('<I', data_size))
        file.write(audio_int16.tobytes())
    
    def start_streaming(self) -> TranscriptionStream:
        """
        Start a streaming transcription session.
        
        Returns:
            TranscriptionStream for receiving results.
        
        Requirements: 5.1 (串流轉錄支援)
        """
        if self._current_stream and self._current_stream.is_active:
            self.stop_streaming()
        
        self._current_stream = TranscriptionStream()
        self._current_stream.start()
        return self._current_stream
    
    def stop_streaming(self) -> None:
        """Stop the current streaming session."""
        if self._current_stream:
            self._current_stream.stop()
            self._current_stream = None
    
    def get_confidence(self) -> float:
        """
        Get the confidence score of the last transcription.
        
        Returns:
            Confidence score between 0.0 and 1.0.
        """
        return self._last_confidence
    
    @staticmethod
    def post_process_math_symbols(text: str) -> str:
        """
        Convert oral math descriptions to standard mathematical symbols.
        
        Args:
            text: Text containing oral math descriptions.
        
        Returns:
            Text with math symbols converted.
        
        Requirements: 5.3 (數學符號轉換)
        
        Examples:
            "x平方" -> "x²"
            "根號2" -> "√2"
            "大於等於" -> "≥"
        """
        result = text
        
        # Sort mappings by length (longest first) to avoid partial replacements
        sorted_mappings = sorted(
            MATH_SYMBOL_MAPPINGS.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )
        
        for oral, symbol in sorted_mappings:
            result = result.replace(oral, symbol)
        
        return result
    
    @staticmethod
    def convert_symbols_to_oral(text: str) -> str:
        """
        Convert mathematical symbols back to oral descriptions.
        
        Args:
            text: Text containing mathematical symbols.
        
        Returns:
            Text with symbols converted to oral descriptions.
        
        This is the inverse of post_process_math_symbols for round-trip testing.
        """
        result = text
        
        # Sort by symbol length (longest first)
        sorted_mappings = sorted(
            SYMBOL_TO_ORAL_MAPPINGS.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )
        
        for symbol, oral in sorted_mappings:
            result = result.replace(symbol, oral)
        
        return result
