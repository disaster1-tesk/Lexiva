"""
Speech Recognition Service using Faster Whisper
"""
import os
import io
import base64
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import faster-whisper, fall back to whisper
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    try:
        import whisper
        WHISPER_AVAILABLE = True
    except ImportError:
        WHISPER_AVAILABLE = False
        logger.warning("Whisper not installed. Run: pip install faster-whisper")


class WhisperService:
    """Speech-to-text service using Whisper"""
    
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load Whisper model"""
        if not WHISPER_AVAILABLE:
            logger.warning("Whisper not available. Audio recognition will be disabled.")
            return
        
        try:
            # Use faster-whisper for better performance
            logger.info(f"Loading Whisper model: {self.model_size}")
            self.model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8"
            )
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            self.model = None
    
    async def transcribe(self, audio_data: bytes, language: str = "en") -> dict:
        """Transcribe audio to text"""
        if not self.model:
            return {
                "success": False,
                "error": "Whisper model not loaded. Please install faster-whisper.",
                "text": ""
            }
        
        try:
            # Save audio to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                f.write(audio_data)
                temp_path = f.name
            
            try:
                # Run transcription in executor to avoid blocking
                loop = asyncio.get_event_loop()
                segments, info = await loop.run_in_executor(
                    None,
                    lambda: self.model.transcribe(temp_path, language=language)
                )
                
                text = " ".join([seg.text for seg in segments])
                
                return {
                    "success": True,
                    "text": text.strip(),
                    "language": info.language,
                    "language_probability": info.language_probability
                }
            finally:
                # Clean up temp file
                os.unlink(temp_path)
                
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }
    
    async def transcribe_base64(self, audio_base64: str, language: str = "en") -> dict:
        """Transcribe base64 encoded audio"""
        try:
            audio_data = base64.b64decode(audio_base64)
            return await self.transcribe(audio_data, language)
        except Exception as e:
            logger.error(f"Base64 decode error: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }


# Global instance
whisper_service = WhisperService()