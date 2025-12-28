"""
ASR (Automatic Speech Recognition) API routes for the AI Math Tutor system.

Implements:
- POST /api/asr/transcribe - Transcribe audio to text
- GET /api/asr/status - Check ASR model status
- POST /api/asr/warmup - Pre-load ASR model

Requirements: 5.1
"""
import tempfile
import os
import subprocess
import logging
import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from backend.services.asr_module import (
    ASRModule,
    ASRConfig,
    ASRError,
    ASRConnectionError,
    ASRTranscriptionError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/asr", tags=["asr"])

# Global ASR module instance (lazy loaded)
_asr_module: Optional[ASRModule] = None
_model_loading: bool = False
_model_load_error: Optional[str] = None


def get_asr_module() -> ASRModule:
    """Get or create the ASR module instance."""
    global _asr_module, _model_loading, _model_load_error
    if _asr_module is None:
        if _model_loading:
            raise ASRConnectionError("ASR 模型正在載入中，請稍後再試（首次載入約需 1-2 分鐘）")
        if _model_load_error:
            raise ASRConnectionError(f"ASR 模型載入失敗: {_model_load_error}")
        _model_loading = True
        _model_load_error = None
        try:
            logger.info("Initializing ASR module...")
            _asr_module = ASRModule(ASRConfig())
            # Pre-load the model
            logger.info("Pre-loading Whisper model (this may take 1-2 minutes)...")
            _asr_module.load_model()
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            _model_load_error = str(e)
            logger.error(f"Failed to load ASR model: {e}")
            raise
        finally:
            _model_loading = False
    return _asr_module


def _load_model_background():
    """Background task to pre-load the model."""
    try:
        get_asr_module()
    except Exception as e:
        logger.error(f"Background model loading failed: {e}")


def convert_to_wav(input_path: str, output_path: str) -> bool:
    """
    Convert audio file to WAV format using ffmpeg.
    
    Args:
        input_path: Path to input audio file
        output_path: Path to output WAV file
        
    Returns:
        True if conversion successful, False otherwise
    """
    try:
        result = subprocess.run(
            [
                'ffmpeg', '-y', '-i', input_path,
                '-ar', '16000',  # 16kHz sample rate (Whisper requirement)
                '-ac', '1',      # Mono
                '-c:a', 'pcm_s16le',  # 16-bit PCM
                output_path
            ],
            capture_output=True,
            timeout=30
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.warning(f"ffmpeg conversion failed: {e}")
        return False


class TranscriptionResponse(BaseModel):
    """Response model for transcription."""
    text: str
    confidence: float
    duration: float
    language: str


class TranscriptionTextRequest(BaseModel):
    """Request model for text-based transcription (for testing)."""
    text: str


class MathSymbolResponse(BaseModel):
    """Response model for math symbol conversion."""
    original: str
    converted: str


class ASRStatusResponse(BaseModel):
    """Response model for ASR status."""
    ready: bool
    loading: bool
    error: Optional[str] = None
    model_size: str = "small"


class WarmupResponse(BaseModel):
    """Response model for warmup."""
    status: str
    message: str


@router.get("/status", response_model=ASRStatusResponse)
async def get_asr_status():
    """
    Check ASR model status.
    
    Returns whether the model is ready, loading, or has an error.
    """
    global _asr_module, _model_loading, _model_load_error
    
    return ASRStatusResponse(
        ready=_asr_module is not None and _asr_module.is_loaded,
        loading=_model_loading,
        error=_model_load_error,
        model_size="small"
    )


@router.post("/warmup", response_model=WarmupResponse)
async def warmup_asr(background_tasks: BackgroundTasks):
    """
    Pre-load the ASR model in the background.
    
    Call this endpoint when the app starts to avoid delay on first transcription.
    """
    global _asr_module, _model_loading, _model_load_error
    
    if _asr_module is not None and _asr_module.is_loaded:
        return WarmupResponse(
            status="ready",
            message="ASR 模型已載入完成"
        )
    
    if _model_loading:
        return WarmupResponse(
            status="loading",
            message="ASR 模型正在載入中..."
        )
    
    if _model_load_error:
        # Reset error and try again
        _model_load_error = None
    
    # Start loading in background
    background_tasks.add_task(_load_model_background)
    
    return WarmupResponse(
        status="loading",
        message="ASR 模型開始載入，首次載入約需 1-2 分鐘"
    )


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Transcribe audio file to text.
    
    Requirements: 5.1
    - Accepts audio file (webm, mp4, wav, etc.)
    - Returns transcribed text with confidence score
    """
    # Get content type - browsers may send various types
    content_type = audio.content_type or "application/octet-stream"
    filename = audio.filename or "recording"
    
    # Log detailed request info
    logger.info(f"ASR Request - filename: {filename}, content_type: {content_type}")
    
    # Determine file extension based on content type or filename
    if "webm" in content_type or "webm" in filename.lower():
        suffix = ".webm"
    elif "mp4" in content_type or "m4a" in content_type or "mp4" in filename.lower():
        suffix = ".mp4"
    elif "ogg" in content_type or "ogg" in filename.lower():
        suffix = ".ogg"
    elif "mpeg" in content_type or "mp3" in content_type or "mp3" in filename.lower():
        suffix = ".mp3"
    elif "wav" in content_type or "wav" in filename.lower():
        suffix = ".wav"
    else:
        # Default to webm for unknown types (most browsers use webm)
        suffix = ".webm"
        logger.info(f"Unknown content type '{content_type}', defaulting to webm")
    
    tmp_input_path = None
    tmp_wav_path = None
    
    try:
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
            content = await audio.read()
            tmp_file.write(content)
            tmp_input_path = tmp_file.name
        
        logger.info(f"Saved audio to: {tmp_input_path}, size: {len(content)} bytes")
        
        # Check if file is too small (likely empty or corrupted)
        if len(content) < 100:
            logger.warning(f"Audio file too small: {len(content)} bytes")
            return TranscriptionResponse(
                text="",
                confidence=0.0,
                duration=0.0,
                language="zh"
            )
        
        # Convert to WAV if not already WAV format
        if suffix != ".wav":
            tmp_wav_path = tmp_input_path.replace(suffix, ".wav")
            if convert_to_wav(tmp_input_path, tmp_wav_path):
                logger.info(f"Converted to WAV: {tmp_wav_path}")
                transcribe_path = tmp_wav_path
            else:
                # Try to transcribe original file directly
                logger.warning("ffmpeg conversion failed, trying original file")
                transcribe_path = tmp_input_path
        else:
            transcribe_path = tmp_input_path
        
        # Get ASR module and transcribe
        asr = get_asr_module()
        
        logger.info("Starting Whisper transcription...")
        import time
        start_time = time.time()
        
        try:
            result = asr.transcribe(transcribe_path)
            elapsed = time.time() - start_time
            logger.info(f"Whisper transcription completed in {elapsed:.2f}s")
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Whisper transcription failed after {elapsed:.2f}s: {e}")
            raise ASRTranscriptionError(f"Whisper 轉錄失敗: {str(e)}")
        
        logger.info(f"Transcription result: '{result.text}', confidence: {result.confidence}")
        
        # Post-process with LLM correction (Whisper Small + Gemma3:4b)
        if asr.config.use_llm_correction and result.text.strip():
            logger.info("Starting LLM post-processing...")
            try:
                processed_text = ASRModule.full_post_process_with_llm(
                    result.text,
                    model=asr.config.llm_model,
                    base_url=asr.config.llm_base_url
                )
            except Exception as e:
                logger.warning(f"LLM post-processing failed: {e}, using basic processing")
                processed_text = ASRModule.full_post_process(result.text)
        else:
            # Fallback to basic post-processing without LLM
            processed_text = ASRModule.full_post_process(result.text)
        
        logger.info(f"Post-processed text: '{processed_text}'")
        
        return TranscriptionResponse(
            text=processed_text,
            confidence=result.confidence,
            duration=result.duration,
            language=result.language
        )
        
    except ASRConnectionError as e:
        logger.error(f"ASR connection error: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"ASR service unavailable: {str(e)}"
        )
    except ASRTranscriptionError as e:
        logger.error(f"ASR transcription error: {e}")
        raise HTTPException(
            status_code=422,
            detail=f"Transcription failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in ASR: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        # Clean up temp files
        if tmp_input_path and os.path.exists(tmp_input_path):
            os.unlink(tmp_input_path)
        if tmp_wav_path and os.path.exists(tmp_wav_path):
            os.unlink(tmp_wav_path)


@router.post("/convert-symbols", response_model=MathSymbolResponse)
async def convert_math_symbols(request: TranscriptionTextRequest):
    """
    Convert oral math descriptions to mathematical symbols.
    
    Requirements: 5.3
    - Converts text like "x平方" to "x²"
    """
    converted = ASRModule.post_process_math_symbols(request.text)
    return MathSymbolResponse(
        original=request.text,
        converted=converted
    )


class SimplifiedToTraditionalResponse(BaseModel):
    """Response model for simplified to traditional conversion."""
    original: str
    converted: str


@router.post("/convert-traditional", response_model=SimplifiedToTraditionalResponse)
async def convert_to_traditional(request: TranscriptionTextRequest):
    """
    Convert simplified Chinese to traditional Chinese.
    
    Useful for testing the conversion mapping.
    """
    converted = ASRModule.convert_simplified_to_traditional(request.text)
    return SimplifiedToTraditionalResponse(
        original=request.text,
        converted=converted
    )


@router.post("/full-process", response_model=MathSymbolResponse)
async def full_process_text(request: TranscriptionTextRequest):
    """
    Apply full post-processing to text.
    
    Combines:
    1. Simplified to Traditional Chinese conversion
    2. Math symbol conversion
    """
    converted = ASRModule.full_post_process(request.text)
    return MathSymbolResponse(
        original=request.text,
        converted=converted
    )
