"""
ASR (Automatic Speech Recognition) API routes for the AI Math Tutor system.

Implements:
- POST /api/asr/transcribe - Transcribe audio to text

Requirements: 5.1
"""
import tempfile
import os
import subprocess
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
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


def get_asr_module() -> ASRModule:
    """Get or create the ASR module instance."""
    global _asr_module
    if _asr_module is None:
        _asr_module = ASRModule(ASRConfig())
    return _asr_module


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
        result = asr.transcribe(transcribe_path)
        
        logger.info(f"Transcription result: '{result.text}', confidence: {result.confidence}")
        
        # Post-process with LLM correction (Whisper Small + Gemma3:4b)
        if asr.config.use_llm_correction:
            processed_text = ASRModule.full_post_process_with_llm(
                result.text,
                model=asr.config.llm_model,
                base_url=asr.config.llm_base_url
            )
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
