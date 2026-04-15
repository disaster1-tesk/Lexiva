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
        {"id": 1, "text": "The cat is sleeping on the mat.", "difficulty": "beginner", "translation": "猫正睡在垫子上。"},
        {"id": 2, "text": "I like to read books in the morning.", "difficulty": "beginner", "translation": "我喜欢在早晨读书。"},
        {"id": 3, "text": "She goes to school every day.", "difficulty": "beginner", "translation": "她每天去上学。"},
        {"id": 4, "text": "They are playing in the park.", "difficulty": "beginner", "translation": "他们正在公园里玩耍。"},
        {"id": 5, "text": "The weather is very nice today.", "difficulty": "beginner", "translation": "今天天气非常好。"},
    ],
    "intermediate": [
        {"id": 11, "text": "Would you mind opening the window, please?", "difficulty": "intermediate", "translation": "你介意打开窗户吗？"},
        {"id": 12, "text": "I have been studying English for three years.", "difficulty": "intermediate", "translation": "我已经学习英语三年了。"},
        {"id": 13, "text": "If I had more time, I would travel around the world.", "difficulty": "intermediate", "translation": "如果我有更多时间，我会环游世界。"},
        {"id": 14, "text": "The movie we watched last night was really interesting.", "difficulty": "intermediate", "translation": "我们昨晚看的那部电影非常有趣。"},
        {"id": 15, "text": "She behaves as if she were the boss.", "difficulty": "intermediate", "translation": "她表现得好像自己是老板。"},
    ],
    "advanced": [
        {"id": 21, "text": "Notwithstanding the numerous challenges, the project was completed successfully.", "difficulty": "advanced", "translation": "尽管面临众多挑战，项目还是成功完成了。"},
        {"id": 22, "text": "The aforementioned criteria will be evaluated by the committee.", "difficulty": "advanced", "translation": "上述标准将由委员会评估。"},
        {"id": 23, "text": "Had I been aware of the consequences, I would have acted differently.", "difficulty": "advanced", "translation": "如果我知道后果，我会采取不同的行动。"},
        {"id": 24, "text": "Nevertheless, the data suggests a significant correlation.", "difficulty": "advanced", "translation": "然而，数据表明存在显著的相关性。"},
        {"id": 25, "text": "It is imperative that all stakeholders participate actively.", "difficulty": "advanced", "translation": "所有利益相关者都必须积极参与。"},
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
    sentence_id: str = Form(...),
    sentence_text: str = Form(""),  # 接收前端传入的句子文本作为备选
    mime_type: str = Form("audio/webm")  # 接收录音格式
):
    """Record and evaluate pronunciation"""
    logger.info(f"Pronunciation record request: sentence_id={sentence_id}, mime_type={mime_type}")
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
        
        # 如果内存中找不到，使用前端传入的句子文本
        if not reference and sentence_text:
            reference = sentence_text
        
        if not reference:
            raise HTTPException(status_code=400, detail="未找到对应的句子，请刷新页面后重试")
        
        # 读取音频文件
        audio_data = await audio.read()
        
        # 使用 Whisper 转写，传递 mime_type
        result = await whisper_service.transcribe(audio_data, language="en", mime_type=mime_type)
        
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
        
        # ========== 持久化评测记录到数据库 ==========
        try:
            from db.connection import get_db
            from models import Statistics
            from datetime import datetime, timezone
            
            session = next(get_db())
            try:
                today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                stats = session.query(Statistics).filter(Statistics.date == today).first()
                if not stats:
                    stats = Statistics(date=today)
                    session.add(stats)
                    session.flush()
                
                stats.pronunciation_count += 1
                # 更新平均分（使用滑动平均）
                old_avg = stats.pronunciation_avg_score or 0
                count = stats.pronunciation_count
                stats.pronunciation_avg_score = ((old_avg * (count - 1)) + score) / count
                
                session.commit()
            except Exception as db_error:
                session.rollback()
                logger.warning(f"Failed to save pronunciation stats: {db_error}")
            finally:
                try:
                    session.close()
                except Exception:
                    pass
        except Exception as db_error:
            logger.warning(f"Database connection failed: {db_error}")
        # ========== 持久化结束 ==========
        
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
        
    except HTTPException:
        raise
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
        result = await tts_service.synthesize(reference)

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