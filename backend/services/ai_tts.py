"""
Text-to-Speech Service using Edge TTS
"""
import os
import io
import base64
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import edge-tts
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    logger.warning("edge-tts not installed. Run: pip install edge-tts")


# Available voices
VOICES = {
    "en-US-AriaNeural": {"name": "Aria", "gender": "Female", "accent": "US"},
    "en-US-GuyNeural": {"name": "Guy", "gender": "Male", "accent": "US"},
    "en-GB-SoniaNeural": {"name": "Sonia", "gender": "Female", "accent": "UK"},
    "en-GB-RyanNeural": {"name": "Ryan", "gender": "Male", "accent": "UK"},
    "en-AU-NatashaNeural": {"name": "Natasha", "gender": "Female", "accent": "AU"},
    "en-AU-ConnorNeural": {"name": "Connor", "gender": "Male", "accent": "AU"},
}

# Voice options for UI
VOICE_OPTIONS = [
    {"value": key, "label": f"{v['name']} ({v['gender']}) - {v['accent']}"}
    for key, v in VOICES.items()
]


class EdgeTTSService:
    """Text-to-speech service using Microsoft Edge TTS"""
    
    def __init__(self, default_voice: str = "en-US-AriaNeural"):
        self.default_voice = default_voice
    
    async def synthesize(
        self,
        text: str,
        voice: str = None,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
    ) -> dict:
        """Convert text to speech"""
        if not EDGE_TTS_AVAILABLE:
            return {
                "success": False,
                "error": "edge-tts not installed. Run: pip install edge-tts",
                "audio": ""
            }
        
        if not text:
            return {
                "success": False,
                "error": "No text provided",
                "audio": ""
            }
        
        voice = voice or self.default_voice
        
        try:
            communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, volume=volume)
            
            # Collect audio data
            audio_data = bytearray()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data.extend(chunk["data"])
            
            # Encode to base64
            audio_base64 = base64.b64encode(bytes(audio_data)).decode("utf-8")
            
            return {
                "success": True,
                "audio": audio_base64,
                "voice": voice,
                "duration": len(audio_data) / 16000  # Approximate duration
            }
            
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return {
                "success": False,
                "error": str(e),
                "audio": ""
            }
    
    async def synthesize_to_file(
        self,
        text: str,
        output_path: str,
        voice: str = None,
        rate: str = "+0%",
        pitch: str = "+0Hz"
    ) -> dict:
        """Save TTS audio to file"""
        if not EDGE_TTS_AVAILABLE:
            return {
                "success": False,
                "error": "edge-tts not installed"
            }
        
        voice = voice or self.default_voice
        
        try:
            communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
            await communicate.save(output_path)
            
            return {
                "success": True,
                "file_path": output_path
            }
            
        except Exception as e:
            logger.error(f"TTS file error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_available_voices(self) -> list:
        """Get list of available voices"""
        return VOICE_OPTIONS


# Global instance
tts_service = EdgeTTSService()