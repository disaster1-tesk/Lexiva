"""
Listening API - TTS and Dictation
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional
import json
import logging
from services.ai_tts import tts_service, VOICE_OPTIONS

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/listening", tags=["listening"])


class TTSRequest(BaseModel):
    text: str
    voice: str = "en-US-AriaNeural"
    speed: float = 1.0
    pitch: float = 0.0


class DictationRequest(BaseModel):
    user_text: str
    reference: str


@router.get("/voices")
async def get_voices():
    """Get available TTS voices"""
    return {"code": 0, "data": VOICE_OPTIONS}


@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """Convert text to speech"""
    # Convert speed float to rate string
    # 0.5 -> "-50%", 1.0 -> "+0%", 1.5 -> "+50%"
    rate = f"+{int((request.speed - 1.0) * 100)}%"
    pitch = f"+{int(request.pitch)}Hz"
    
    result = await tts_service.synthesize(
        text=request.text,
        voice=request.voice,
        rate=rate,
        pitch=pitch
    )
    
    if result.get("success"):
        return {"code": 0, "data": result}
    else:
        raise HTTPException(status_code=500, detail=result.get("error"))


@router.post("/dictation")
async def check_dictation(request: DictationRequest):
    """Check dictation result"""
    try:
        import difflib
        
        user_text = request.user_text.strip()
        reference = request.reference.strip()
        
        # Calculate similarity
        similarity = difflib.SequenceMatcher(None, user_text.lower(), reference.lower()).ratio()
        score = int(similarity * 100)
        
        # Find differences
        d = difflib.Differ()
        diff = list(d.compare([reference.lower()], [user_text.lower()]))
        
        errors = []
        correct_words = 0
        total_words = len(reference.split())
        
        # Simple word-level comparison
        ref_words = reference.lower().split()
        user_words = user_text.lower().split()
        
        for i, ref_word in enumerate(ref_words):
            if i < len(user_words) and ref_word == user_words[i]:
                correct_words += 1
            else:
                errors.append({
                    "position": i,
                    "expected": ref_word,
                    "actual": user_words[i] if i < len(user_words) else "[missing]"
                })
        
        accuracy = int(correct_words / total_words * 100) if total_words > 0 else 0
        
        return {
            "code": 0,
            "data": {
                "score": score,
                "accuracy": accuracy,
                "correct_words": correct_words,
                "total_words": total_words,
                "errors": errors[:5],  # Show max 5 errors
                "reference": reference,
                "user_input": user_text
            }
        }
        
    except Exception as e:
        logger.error(f"Dictation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Pre-built listening materials
MATERIALS = [
    {
        "id": 1,
        "title": "Daily Greetings",
        "difficulty": "beginner",
        "text": "Good morning! How are you today? I hope you have a wonderful day."
    },
    {
        "id": 2,
        "title": "At the Restaurant",
        "difficulty": "intermediate", 
        "text": "I would like to make a reservation for two people at seven o'clock tonight. Could you recommend some popular dishes?"
    },
    {
        "id": 3,
        "title": "Academic Discussion",
        "difficulty": "advanced",
        "text": "The research demonstrates a significant correlation between economic development and environmental sustainability."
    }
]


@router.get("/materials")
async def get_materials(difficulty: str = None):
    """Get listening materials"""
    if difficulty:
        filtered = [m for m in MATERIALS if m["difficulty"] == difficulty]
        return {"code": 0, "data": filtered}
    return {"code": 0, "data": MATERIALS}