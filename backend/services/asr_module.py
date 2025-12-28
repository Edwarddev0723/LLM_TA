"""
ASR Module - Whisper-based Automatic Speech Recognition

This module provides speech-to-text transcription using OpenAI's Whisper model,
with support for streaming transcription and math symbol post-processing.

Requirements: 5.1, 5.3
"""

import os
# Fix OpenMP duplicate library issue on macOS
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

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
    model_size: WhisperModelSize = WhisperModelSize.SMALL  # 使用 small 模型提升速度
    language: str = "zh"  # Chinese
    task: str = "transcribe"
    fp16: bool = False  # Use FP32 for CPU compatibility
    device: str = "cpu"  # Default to CPU for MacBook compatibility
    silence_threshold: float = 0.5  # Seconds of silence to detect pause
    max_audio_length: float = 30.0  # Maximum audio length in seconds
    # 繁體中文優化參數
    initial_prompt: str = "以下是繁體中文數學教學對話。"  # 引導模型輸出繁體中文
    temperature: float = 0.0  # 降低隨機性，提高準確度
    beam_size: int = 3  # 降低 beam search 寬度以加速（原本 5）
    best_of: int = 3  # 降低候選數量以加速（原本 5）
    condition_on_previous_text: bool = False  # 禁用以加速處理
    # LLM 後處理設定 - 暫時禁用以測試性能
    use_llm_correction: bool = False  # 是否使用 LLM 修正（暫時禁用）
    llm_model: str = "gemma3:4b"  # LLM 模型名稱
    llm_base_url: str = "http://localhost:11434"  # Ollama API URL


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
    
    # Arithmetic operators (Chinese) - use more specific terms to avoid false matches
    "加上": "+",
    "加法": "+",
    "減去": "-",
    "减去": "-",
    "減法": "-",
    "减法": "-",
    "乘以": "×",
    "乘法": "×",
    "除以": "÷",
    "除法": "÷",
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
    "邏輯非": "¬",
    "逻辑非": "¬",
    "若且唯若": "⟺",
    "若則": "⟹",
    "若则": "⟹",
    "因此": "∴",
    "因為": "∵",
    "因为": "∵",
}

# 簡體轉繁體常用字對照表（數學教學相關）
# 包含單字和詞組，處理時會按長度排序（長詞優先）
SIMPLIFIED_TO_TRADITIONAL = {
    # 重要單字（確保基本轉換）
    "于": "於",  # 用於 "大于" -> "大於" 等
    "与": "與",
    "为": "為",
    "从": "從",
    "会": "會",
    "这": "這",
    "学": "學",
    "问": "問",
    "说": "說",
    "让": "讓",
    "给": "給",
    "对": "對",
    "错": "錯",
    "变": "變",
    "换": "換",
    "开": "開",
    "关": "關",
    "过": "過",
    "进": "進",
    "来": "來",
    "发": "發",
    "现": "現",
    "见": "見",
    "听": "聽",
    "写": "寫",
    "读": "讀",
    "认": "認",
    "识": "識",
    "应": "應",
    "该": "該",
    "须": "須",
    "经": "經",
    "继": "繼",
    "连": "連",
    "还": "還",
    "并": "並",
    "数": "數",
    "计": "計",
    "题": "題",
    "答": "答",
    "解": "解",
    "证": "證",
    "验": "驗",
    "设": "設",
    "条": "條",
    "结": "結",
    "论": "論",
    "则": "則",
    "当": "當",
    "时": "時",
    "点": "點",
    "线": "線",
    "边": "邊",
    "长": "長",
    "宽": "寬",
    "面": "面",
    "积": "積",
    "体": "體",
    "图": "圖",
    "形": "形",
    "圆": "圓",
    "周": "周",
    "角": "角",
    "方": "方",
    "程": "程",
    "式": "式",
    "等": "等",
    "号": "號",
    "符": "符",
    "项": "項",
    "移": "移",
    "系": "係",
    "根": "根",
    "次": "次",
    "元": "元",
    "正": "正",
    "负": "負",
    "整": "整",
    "分": "分",
    "比": "比",
    "较": "較",
    "倍": "倍",
    "余": "餘",
    "商": "商",
    "和": "和",
    "差": "差",
    "乘": "乘",
    "除": "除",
    "加": "加",
    "减": "減",
    "平": "平",
    "立": "立",
    "幂": "冪",
    "指": "指",
    "底": "底",
    "函": "函",
    "常": "常",
    "未": "未",
    "已": "已",
    "求": "求",
    "得": "得",
    "所": "所",
    "因": "因",
    "如": "如",
    "果": "果",
    "那": "那",
    "么": "麼",
    "什": "什",
    "怎": "怎",
    "样": "樣",
    "哪": "哪",
    "里": "裡",
    "几": "幾",
    "个": "個",
    "两": "兩",
    "双": "雙",
    "单": "單",
    "位": "位",
    "第": "第",
    "每": "每",
    "全": "全",
    "部": "部",
    "总": "總",
    "共": "共",
    "同": "同",
    "异": "異",
    "类": "類",
    "种": "種",
    "组": "組",
    "排": "排",
    "列": "列",
    "选": "選",
    "择": "擇",
    "确": "確",
    "定": "定",
    "满": "滿",
    "足": "足",
    "够": "夠",
    "多": "多",
    "少": "少",
    "大": "大",
    "小": "小",
    "最": "最",
    "极": "極",
    "值": "值",
    "范": "範",
    "围": "圍",
    "区": "區",
    "间": "間",
    "内": "內",
    "外": "外",
    "上": "上",
    "下": "下",
    "左": "左",
    "右": "右",
    "前": "前",
    "后": "後",
    "先": "先",
    "再": "再",
    "又": "又",
    "也": "也",
    "都": "都",
    "只": "只",
    "就": "就",
    "才": "才",
    "很": "很",
    "太": "太",
    "更": "更",
    "非": "非",
    "特": "特",
    "别": "別",
    "真": "真",
    "假": "假",
    "实": "實",
    "际": "際",
    "其": "其",
    "他": "他",
    "她": "她",
    "它": "它",
    "我": "我",
    "你": "你",
    "们": "們",
    "自": "自",
    "己": "己",
    "本": "本",
    "原": "原",
    "新": "新",
    "旧": "舊",
    "好": "好",
    "坏": "壞",
    "难": "難",
    "困": "困",
    "易": "易",
    "容": "容",
    "简": "簡",
    "复": "複",
    "杂": "雜",
    "清": "清",
    "楚": "楚",
    "明": "明",
    "白": "白",
    "懂": "懂",
    "理": "理",
    "道": "道",
    "知": "知",
    "想": "想",
    "思": "思",
    "考": "考",
    "虑": "慮",
    "记": "記",
    "住": "住",
    "忘": "忘",
    "注": "注",
    "意": "意",
    "看": "看",
    "试": "試",
    "尝": "嘗",
    "做": "做",
    "作": "作",
    "用": "用",
    "使": "使",
    "利": "利",
    "帮": "幫",
    "助": "助",
    "需": "需",
    "要": "要",
    "能": "能",
    "可": "可",
    "以": "以",
    "必": "必",
    
    # 常用詞組（長詞優先處理）
    "这个": "這個", "这里": "這裡", "这样": "這樣",
    "那个": "那個", "那里": "那裡", "那样": "那樣",
    "学会": "學會", "不会": "不會",
    "学习": "學習", "数学": "數學",
    "问题": "問題", "请问": "請問",
    "说明": "說明",
    "让我": "讓我",
    "给你": "給你",
    "对不对": "對不對", "对的": "對的",
    "错误": "錯誤", "错了": "錯了",
    "变成": "變成", "改变": "改變",
    "交换": "交換",
    "开始": "開始",
    "关系": "關係",
    "经过": "經過", "通过": "通過",
    "进行": "進行",
    "出来": "出來", "起来": "起來",
    "发现": "發現",
    "现在": "現在", "出现": "出現",
    "看见": "看見",
    "听说": "聽說",
    "写出": "寫出",
    "读作": "讀作",
    "认为": "認為",
    "认识": "認識", "知识": "知識",
    "应该": "應該",
    "必须": "必須",
    "已经": "已經", "经常": "經常",
    "继续": "繼續",
    "连接": "連接",
    "还是": "還是", "还有": "還有",
    "并且": "並且",
    # 數學術語詞組
    "数字": "數字", "数值": "數值", "数量": "數量",
    "计算": "計算", "设计": "設計",
    "题目": "題目", "习题": "習題",
    "答案": "答案", "回答": "回答",
    "解答": "解答", "解题": "解題", "解方程": "解方程",
    "证明": "證明", "验证": "驗證",
    "假设": "假設",
    "条件": "條件",
    "结果": "結果", "结论": "結論",
    "否则": "否則",
    "当时": "當時",
    "时候": "時候",
    "点数": "點數",
    "直线": "直線", "曲线": "曲線",
    "边长": "邊長",
    "长度": "長度",
    "宽度": "寬度",
    "面积": "面積",
    "体积": "體積", "乘积": "乘積",
    "图形": "圖形",
    "圆形": "圓形", "圆周": "圓周",
    "周长": "周長",
    "角度": "角度", "三角": "三角",
    "方程": "方程", "方向": "方向",
    "公式": "公式", "等式": "等式",
    "等号": "等號", "符号": "符號",
    "移项": "移項",
    "系数": "係數",
    "根号": "根號",
    "一次": "一次", "二次": "二次",
    "一元": "一元", "二元": "二元",
    "正数": "正數", "正确": "正確",
    "负数": "負數",
    "整数": "整數",
    "分数": "分數", "分母": "分母", "分子": "分子",
    "比例": "比例", "比较": "比較",
    "余数": "餘數",
    "平方": "平方", "平均": "平均",
    "立方": "立方",
    "次幂": "次冪",
    "指数": "指數",
    "对数": "對數",
    "底数": "底數",
    "函数": "函數",
    "变量": "變量", "变数": "變數",
    "常数": "常數",
    "未知": "未知", "未知数": "未知數",
    "已知": "已知",
    "得到": "得到",
    "所以": "所以",
    "因为": "因為", "因此": "因此",
    "如果": "如果",
    "那么": "那麼",
    "什么": "什麼",
    "怎么": "怎麼", "怎样": "怎樣",
    "哪个": "哪個", "哪里": "哪裡",
    "几个": "幾個",
    "单位": "單位",
    "总共": "總共", "总和": "總和",
    "相同": "相同", "同样": "同樣",
    "不同": "不同",
    "分类": "分類",
    "种类": "種類",
    "一组": "一組",
    "排列": "排列",
    "选择": "選擇",
    "确定": "確定",
    "满足": "滿足",
    "足够": "足夠",
    "多少": "多少",
    "最大": "最大", "最小": "最小",
    "极值": "極值",
    "范围": "範圍",
    "区间": "區間",
    "然后": "然後", "之后": "之後",
    "首先": "首先",
    "非常": "非常",
    "特别": "特別",
    "实际": "實際", "其实": "其實",
    "其他": "其他",
    "我们": "我們",
    "你们": "你們",
    "自己": "自己",
    "原来": "原來",
    "困难": "困難",
    "容易": "容易",
    "简单": "簡單",
    "复杂": "複雜",
    "清楚": "清楚",
    "明白": "明白",
    "道理": "道理", "理解": "理解",
    "知道": "知道",
    "想想": "想想",
    "思考": "思考",
    "考虑": "考慮",
    "记住": "記住",
    "忘记": "忘記",
    "注意": "注意",
    "看看": "看看",
    "试试": "試試", "尝试": "嘗試",
    "使用": "使用", "利用": "利用",
    "帮助": "幫助",
    "需要": "需要",
    "能够": "能夠",
    "可以": "可以", "可能": "可能",
    "以后": "以後",
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
            # 使用優化參數進行轉錄（優化速度）
            result = self._model.transcribe(
                audio_path,
                language=language or self.config.language,
                task=self.config.task,
                fp16=self.config.fp16,
                # 繁體中文優化參數
                initial_prompt=self.config.initial_prompt,
                temperature=self.config.temperature,
                beam_size=self.config.beam_size,
                best_of=self.config.best_of,
                condition_on_previous_text=self.config.condition_on_previous_text,
                # 禁用 word timestamps 以加速處理
                word_timestamps=False,
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
    
    @staticmethod
    def convert_simplified_to_traditional(text: str) -> str:
        """
        Convert simplified Chinese characters to traditional Chinese.
        
        Args:
            text: Text potentially containing simplified Chinese characters.
        
        Returns:
            Text with simplified characters converted to traditional.
        
        This helps improve ASR output quality for Traditional Chinese users,
        as Whisper sometimes outputs simplified Chinese even with zh-TW settings.
        
        Examples:
            "这个数学问题" -> "這個數學問題"
            "计算结果" -> "計算結果"
        """
        result = text
        
        # Sort mappings by length (longest first) to handle multi-character words first
        # This prevents partial replacements (e.g., "数学" should be replaced before "数")
        sorted_mappings = sorted(
            SIMPLIFIED_TO_TRADITIONAL.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )
        
        for simplified, traditional in sorted_mappings:
            result = result.replace(simplified, traditional)
        
        return result
    
    @staticmethod
    def full_post_process(text: str) -> str:
        """
        Apply all post-processing steps to transcribed text.
        
        This combines:
        1. Math symbol conversion (oral to symbols) - FIRST to catch both simplified/traditional
        2. Simplified to Traditional Chinese conversion - SECOND for remaining text
        
        Args:
            text: Raw transcribed text from Whisper.
        
        Returns:
            Fully processed text ready for display.
        """
        # First convert oral math descriptions to symbols
        # (math mappings include both simplified and traditional versions)
        result = ASRModule.post_process_math_symbols(text)
        # Then convert remaining simplified to traditional Chinese
        result = ASRModule.convert_simplified_to_traditional(result)
        return result
    
    @staticmethod
    def llm_correct_transcription(
        text: str,
        model: str = "gemma3:4b",
        base_url: str = "http://localhost:11434"
    ) -> str:
        """
        Use LLM to correct and improve ASR transcription.
        
        Args:
            text: Raw transcribed text from Whisper.
            model: Ollama model name for correction.
            base_url: Ollama API base URL.
        
        Returns:
            Corrected text with improved accuracy.
        """
        import requests
        import logging
        
        logger = logging.getLogger(__name__)
        
        if not text or not text.strip():
            return text
        
        # Prompt for ASR correction - focused on math education context
        prompt = f"""修正語音辨識錯誤，簡體轉繁體。保持數字為阿拉伯數字(1,2,3...)，不要改成中文數字。

{text}"""

        try:
            response = requests.post(
                f"{base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistent output
                        "num_predict": 200,  # Limit output length
                    }
                },
                timeout=30  # 30 second timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                corrected = result.get("response", "").strip()
                
                # Validate the correction - if it's too different or empty, use original
                if corrected and len(corrected) > 0:
                    # Remove any leading/trailing quotes or extra whitespace
                    corrected = corrected.strip('"\'').strip()
                    
                # If LLM returned something reasonable, use it
                    if len(corrected) >= len(text) * 0.5 and len(corrected) <= len(text) * 2:
                        # Clean up: remove trailing punctuation that LLM might add
                        corrected = corrected.rstrip('。，！？.!?,')
                        logger.info(f"LLM correction: '{text}' -> '{corrected}'")
                        return corrected
                
                logger.warning(f"LLM correction rejected, using original: '{text}'")
                return text
            else:
                logger.warning(f"LLM API error {response.status_code}, using original text")
                return text
                
        except requests.exceptions.Timeout:
            logger.warning("LLM correction timeout, using original text")
            return text
        except requests.exceptions.ConnectionError:
            logger.warning("LLM service unavailable, using original text")
            return text
        except Exception as e:
            logger.warning(f"LLM correction failed: {e}, using original text")
            return text
    
    @staticmethod
    def convert_chinese_numbers_to_arabic(text: str) -> str:
        """
        Convert Chinese numbers to Arabic numerals.
        
        Args:
            text: Text containing Chinese numbers.
        
        Returns:
            Text with Chinese numbers converted to Arabic.
        """
        import re
        
        # Single digit mapping
        digit_map = {
            "零": "0", "〇": "0",
            "一": "1", "二": "2", "三": "3", "四": "4",
            "五": "5", "六": "6", "七": "7", "八": "8", "九": "9",
        }
        
        result = text
        
        # Handle "十X" pattern (10-19)
        result = re.sub(r'十([一二三四五六七八九])', lambda m: f"1{digit_map[m.group(1)]}", result)
        result = result.replace("十", "10")
        
        # Handle single digits
        for chinese, arabic in digit_map.items():
            result = result.replace(chinese, arabic)
        
        return result
    
    @staticmethod
    def full_post_process_with_llm(
        text: str,
        model: str = "gemma3:4b",
        base_url: str = "http://localhost:11434"
    ) -> str:
        """
        Apply all post-processing steps including LLM correction.
        
        Pipeline:
        1. Whisper Small output
        2. LLM correction (gemma3:4b) - fix typos, convert to traditional Chinese
        3. Math symbol conversion
        
        Args:
            text: Raw transcribed text from Whisper.
            model: Ollama model name for correction.
            base_url: Ollama API base URL.
        
        Returns:
            Fully processed and corrected text.
        """
        if not text or not text.strip():
            return text
        
        # Step 1: LLM correction (handles typos and simplified->traditional)
        corrected = ASRModule.llm_correct_transcription(text, model, base_url)
        
        # Step 2: Math symbol conversion (oral -> symbols)
        result = ASRModule.post_process_math_symbols(corrected)
        
        # Step 3: Convert Chinese numbers back to Arabic (LLM sometimes converts them)
        result = ASRModule.convert_chinese_numbers_to_arabic(result)
        
        # Step 4: Final simplified->traditional pass (in case LLM missed some)
        result = ASRModule.convert_simplified_to_traditional(result)
        
        return result
