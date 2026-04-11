"""
Pronunciation API - Voice Recording and Evaluation
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional
import json
import logging
from services.ai_whisper import whisper_service
from services.ai_tts import tts_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/pronunciation", tags=["pronunciation"])


# Evaluation sentences database
SENTENCES = {
    "beginner": [
        {"id": 1, "text": "The cat is sleeping on the mat.", "difficulty": "beginner"},
        {"id": 2, "text": "I like to read books in the morning.", "difficulty": "beginner"},
        {"id": 3, "text": "She goes to school every day.", "difficulty": "beginner"},
        {"id": 4, "text": "They are playing in the park.", "difficulty": "beginner"},
        {"id": 5, "text": "The weather is very nice today.", "difficulty": "beginner"},
    ],
    "intermediate": [
        {"id": 11, "text": "Would you mind opening the window, please?", "difficulty": "intermediate"},
        {"id": 12, "text": "I have been studying English for three years.", "difficulty": "intermediate"},
        {"id": 13, "text": "If I had more time, I would travel around the world.", "difficulty": "intermediate"},
        {"id": 14, "text": "The movie we watched last night was really interesting.", "difficulty": "intermediate"},
        {"id": 15, "text": "She behaves as if she were the boss.", "difficulty": "intermediate"},
    ],
    "advanced": [
        {"id": 21, "text": "Notwithstanding the numerous challenges, the project was completed successfully.", "difficulty": "advanced"},
        {"id": 22, "text": "The aforementioned criteria will be evaluated by the committee.", "difficulty": "advanced"},
        {"id": 23, "text": "Had I been aware of the consequences, I would have acted differently.", "difficulty": "advanced"},
        {"id": 24, "text": "Nevertheless, the data suggests a significant correlation.", "difficulty": "advanced"},
        {"id": 25, "text": "It is imperative that all stakeholders participate actively.", "difficulty": "advanced"},
    ]
}


class EvaluateRequest(BaseModel):
    text: str
    reference: str


@router.get("/sentences")
async def get_sentences(difficulty: str = "beginner"):
    """Get evaluation sentences by difficulty"""
    sentences = SENTENCES.get(difficulty, SENTENCES["beginner"])
    return {"code": 0, "data": sentences}


@router.get("/sentences/all")
async def get_all_sentences():
    """Get all evaluation sentences"""
    all_sentences = []
    for diff, sentences in SENTENCES.items():
        all_sentences.extend(sentences)
    return {"code": 0, "data": all_sentences}


@router.post("/evaluate")
async def evaluate_pronunciation(
    audio: UploadFile = File(...),
    reference: str = Form(...)
):
    """Evaluate pronunciation"""
    try:
        # Read audio file
        audio_data = await audio.read()
        
        # Transcribe using Whisper
        result = await whisper_service.transcribe(audio_data, language="en")
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Transcription failed"))
        
        recognized_text = result.get("text", "")
        
        # Calculate score (simple similarity)
        import difflib
        similarity = difflib.SequenceMatcher(None, recognized_text.lower(), reference.lower()).ratio()
        score = int(similarity * 100)
        
        # Generate feedback
        feedback = []
        if score >= 90:
            feedback.append("Excellent pronunciation!")
        elif score >= 70:
            feedback.append("Good job! Keep practicing.")
        else:
            feedback.append("Keep trying! Listen to the reference and try again.")
        
        return {
            "code": 0,
            "data": {
                "recognized": recognized_text,
                "reference": reference,
                "score": score,
                "feedback": feedback
            }
        }
        
    except Exception as e:
        logger.error(f"Evaluation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/record")
async def record_audio(
    audio: UploadFile = File(...),
    sentence_id: str = Form(...)
):
    """Record and evaluate pronunciation"""
    try:
        # 获取参考句子文本
        reference = ""
        for sentences in SENTENCES.values():
            for s in sentences:
                if str(s["id"]) == sentence_id:
                    reference = s["text"]
                    break
            if reference:
                break
        
        if not reference:
            # 尝试从前端数据中查找
            pass
        
        # 读取音频文件
        audio_data = await audio.read()
        
        # 使用 Whisper 转写
        result = await whisper_service.transcribe(audio_data, language="en")
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Transcription failed"))
        
        recognized_text = result.get("text", "")
        
        # 计算得分
        import difflib
        similarity = difflib.SequenceMatcher(None, recognized_text.lower(), reference.lower()).ratio()
        score = int(similarity * 100)
        
        # 生成反馈
        feedback = []
        if score >= 90:
            feedback.append("Excellent pronunciation!")
        elif score >= 70:
            feedback.append("Good job! Keep practicing.")
        else:
            feedback.append("Keep trying! Listen to the reference and try again.")
        
        return {
            "score": score,
            "fluency": min(100, score + 10),
            "accuracy": score,
            "completeness": min(100, score + 5),
            "issues": [],
            "suggestions": feedback[0] if feedback else "Keep practicing!",
            "recognized": recognized_text,
            "reference": reference
        }
        
    except Exception as e:
        logger.error(f"Recording error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sentence/{sentence_id}/audio")
async def get_sentence_audio(sentence_id: int):
    """Get TTS audio for a sentence"""
    # Find the sentence text
    reference = ""
    for sentences in SENTENCES.values():
        for s in sentences:
            if s["id"] == sentence_id:
                reference = s["text"]
                break
        if reference:
            break

    if not reference:
        raise HTTPException(status_code=404, detail="Sentence not found")

    # Generate TTS audio
    try:
        import asyncio
        result = asyncio.run(tts_service.synthesize(reference))

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "TTS failed"))

        return {
            "code": 0,
            "data": {
                "audio": result.get("audio", ""),
                "text": reference
            }
        }
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))