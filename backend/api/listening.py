"""
Listening API - TTS and Dictation
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional
import json
import logging
from services.ai_tts import tts_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/listening", tags=["listening"])


class TTSRequest(BaseModel):
    text: str
    voice: str = "en-US-AriaNeural"
    speed: float = 1.0
    pitch: float = 0.0


class DictationRequest(BaseModel):
    text: Optional[str] = None  # 兼容前端发送的 text 字段
    user_text: Optional[str] = None  # 也可以直接用 user_text
    reference: str
    
    # 统一处理：优先使用 text，否则用 user_text
    def get_user_text(self) -> str:
        return self.text or self.user_text or ""


@router.get("/voices")
async def get_voices():
    """Get available TTS voices"""
    logger.info("Get available TTS voices")
    voices = tts_service.get_available_voices()
    return {"code": 0, "data": voices}


@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """Convert text to speech"""
    logger.info(f"TTS request: text_len={len(request.text)}, voice={request.voice}")
    
    # Convert speed float to rate string
    # 0.5 -> "-50%", 1.0 -> "+0%", 1.5 -> "+50%"
    rate = f"+{int((request.speed - 1.0) * 100)}%"
    pitch = f"+{int(request.pitch)}Hz"
    
    try:
        result = await tts_service.synthesize(
            text=request.text,
            voice=request.voice,
            rate=rate,
            pitch=pitch
        )
        
        if result.get("success"):
            logger.info(f"TTS generated successfully: audio_len={len(result.get('audio', ''))}")
            return {"code": 0, "data": result}
        else:
            logger.error(f"TTS failed: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get("error"))
    except Exception as e:
        logger.error(f"TTS error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dictation")
async def check_dictation(request: DictationRequest):
    """Check dictation result"""
    user_text = request.get_user_text()
    reference = request.reference
    logger.info(f"Dictation check: user_text_len={len(user_text)}, reference_len={len(reference)}")
    
    try:
        import difflib
        
        user_text_val = user_text.strip()
        reference_val = reference.strip()
        
        # Calculate similarity
        similarity = difflib.SequenceMatcher(None, user_text_val.lower(), reference_val.lower()).ratio()
        score = int(similarity * 100)
        
        # Find differences
        d = difflib.Differ()
        diff = list(d.compare([reference_val.lower()], [user_text_val.lower()]))
        
        errors = []
        correct_words = 0
        total_words = len(reference_val.split())
        
        # Simple word-level comparison
        ref_words = reference_val.lower().split()
        user_words = user_text_val.lower().split()
        
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
        
        logger.info(f"Dictation result: score={score}, accuracy={accuracy}, errors={len(errors)}")
        
        return {
            "code": 0,
            "data": {
                "score": score,
                "accuracy": accuracy,
                "correct_words": correct_words,
                "total_words": total_words,
                "errors": errors[:5],  # Show max 5 errors
                "reference": reference_val,
                "user_input": user_text_val
            }
        }
        
    except Exception as e:
        logger.error(f"Dictation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Pre-built listening materials
MATERIALS = [
    {
        "id": 1,
        "title": "Daily Greetings",
        "difficulty": "beginner",
        "difficulty_label": "初级",
        "text": "Good morning! How are you today? I hope you have a wonderful day.",
        "translation": "早上好！你今天好吗？祝你今天愉快。"
    },
    {
        "id": 2,
        "title": "At the Restaurant",
        "difficulty": "intermediate",
        "difficulty_label": "中级", 
        "text": "I would like to make a reservation for two people at seven o'clock tonight. Could you recommend some popular dishes?",
        "translation": "我想预订今晚七点两位。你能推荐一些热门菜品吗？"
    },
    {
        "id": 3,
        "title": "Academic Discussion",
        "difficulty": "advanced",
        "difficulty_label": "高级",
        "text": "The research demonstrates a significant correlation between economic development and environmental sustainability.",
        "translation": "这项研究显示了经济发展与环境可持续性之间的显著相关性。"
    }
]


@router.get("/materials")
async def get_materials(difficulty: str = None):
    """Get listening materials"""
    logger.info(f"Get listening materials: difficulty={difficulty}")
    
    if difficulty:
        filtered = [m for m in MATERIALS if m["difficulty"] == difficulty]
        logger.info(f"Materials filtered: count={len(filtered)}")
        return {"code": 0, "data": filtered}
    
    logger.info(f"Materials returned: count={len(MATERIALS)}")
    return {"code": 0, "data": MATERIALS}