"""
Chat API Routes
AI conversation endpoints
"""
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from services.ai_chat import chat_service
from services.ai_whisper import whisper_service
from services.ai_tts import tts_service
from db.connection import get_db
from models import Conversation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat"])


# Pydantic Models
class ChatRequest(BaseModel):
    message: str
    scene: str = "daily"


class ChatResponse(BaseModel):
    reply: str
    corrections: Optional[List[dict]] = None


@router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Send a message and get AI response
    """
    logger.info(f"Chat request: scene={request.scene}, message_len={len(request.message)}")
    
    if not request.message.strip():
        logger.warning("Empty message received")
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    try:
        result = await chat_service.chat(request.message, request.scene)
        logger.info(f"Chat response generated: reply_len={len(result.get('reply', ''))}")
    except Exception as e:
        logger.error(f"Chat service error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Chat service failed")
    
    # 保存到数据库并记录统计
    session = next(get_db())
    try:
        conversation = Conversation(
            scene=request.scene,
            user_message=request.message,
            ai_message=result["reply"],
            corrections=result.get("corrections", [])
        )
        session.add(conversation)
        
        # 更新今日统计
        from models import Statistics
        today = datetime.now().strftime("%Y-%m-%d")
        stats = session.query(Statistics).filter(Statistics.date == today).first()
        if not stats:
            stats = Statistics(date=today)
            session.add(stats)
            session.flush()
        stats.chat_count += 1
        
        session.commit()
        logger.info(f"Chat saved: conversation_id={conversation.id}")
    finally:
        try:
            session.close()
        except Exception:
            pass
    
    return ChatResponse(**result)


@router.get("/history")
async def get_history(page: int = 1, limit: int = 20):
    """
    Get conversation history
    """
    session = next(get_db())
    try:
        offset = (page - 1) * limit
        conversations = (
            session.query(Conversation)
            .order_by(Conversation.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        total = session.query(Conversation).count()
        
        return {
            "items": [
                {
                    "id": c.id,
                    "scene": c.scene,
                    "user_message": c.user_message,
                    "ai_message": c.ai_message,
                    "corrections": c.corrections,
                    "created_at": c.created_at.isoformat()
                }
                for c in conversations
            ],
            "total": total,
            "page": page,
            "limit": limit
        }
    finally:
        try:
            session.close()
        except Exception:
            pass


@router.post("/clear")
async def clear_history():
    """
    Clear conversation history
    """
    chat_service.clear_history()
    
    session = next(get_db())
    try:
        session.query(Conversation).delete()
        session.commit()
        return {"message": "History cleared"}
    finally:
        try:
            session.close()
        except Exception:
            pass


class VoiceChatResponse(BaseModel):
    reply: str
    audio: str  # base64 encoded audio
    corrections: Optional[List[dict]] = None
    recognized_text: str  # 用户说的文字


@router.post("/voice", response_model=VoiceChatResponse)
async def voice_chat(
    audio: UploadFile = File(...),
    scene: str = Form("daily"),
    mime_type: str = Form("audio/webm")
):
    """
    Voice conversation: receive audio → Whisper → AI → TTS → return text + audio
    """
    logger.info(f"Voice chat request: scene={scene}, filename={audio.filename}, mime_type={mime_type}")
    
    # Check file type
    if not audio.filename or not audio.filename.endswith(('.webm', '.wav', '.mp3', '.ogg', '.m4a', '.mp4')):
        logger.warning(f"Invalid audio file type: {audio.filename}")
        raise HTTPException(status_code=400, detail="不支持的音频格式，请使用 webm, wav, mp3, m4a 或 ogg")
    
    try:
        # Read audio data
        audio_data = await audio.read()
        if len(audio_data) < 1000:  # Less than 1KB is likely empty
            logger.warning("Audio data too small")
            raise HTTPException(status_code=400, detail="录音太短，请重试")
        
        logger.info(f"Audio received: size={len(audio_data)} bytes")
        
        # Step 1: Whisper speech recognition
        whisper_result = await whisper_service.transcribe(audio_data, language="en", mime_type=mime_type)
        if not whisper_result.get("success"):
            logger.error(f"Whisper failed: {whisper_result.get('error')}")
            raise HTTPException(status_code=500, detail=f"语音识别失败: {whisper_result.get('error')}")
        
        recognized_text = whisper_result.get("text", "")
        if not recognized_text.strip():
            logger.warning("Whisper returned empty text")
            raise HTTPException(status_code=400, detail="未能识别语音，请重试")
        
        logger.info(f"Whisper success: recognized='{recognized_text[:100]}...'")
        
        # Step 2: AI chat
        chat_result = await chat_service.chat(recognized_text, scene)
        reply = chat_result.get("reply", "")
        
        if not reply:
            logger.error("Chat service returned empty reply")
            raise HTTPException(status_code=500, detail="AI 回复为空")
        
        logger.info(f"AI reply: '{reply[:100]}...'")
        
        # Step 3: TTS synthesis
        tts_result = await tts_service.synthesize(reply)
        if not tts_result.get("success"):
            logger.warning(f"TTS failed: {tts_result.get('error')}, returning text only")
            # If TTS fails, still return text response
            return VoiceChatResponse(
                reply=reply,
                audio="",
                corrections=chat_result.get("corrections", []),
                recognized_text=recognized_text
            )
        
        audio_base64 = tts_result.get("audio", "")
        logger.info(f"TTS success: audio_size={len(audio_base64)} bytes")
        
        # Save to database
        session = next(get_db())
        try:
            conversation = Conversation(
                scene=scene,
                user_message=recognized_text,
                ai_message=reply,
                corrections=chat_result.get("corrections", [])
            )
            session.add(conversation)
            
            # Update statistics
            from models import Statistics
            today = datetime.now().strftime("%Y-%m-%d")
            stats = session.query(Statistics).filter(Statistics.date == today).first()
            if not stats:
                stats = Statistics(date=today)
                session.add(stats)
                session.flush()
            stats.chat_count += 1
            
            session.commit()
            logger.info(f"Voice chat saved: conversation_id={conversation.id}")
        finally:
            try:
                session.close()
            except Exception:
                pass
        
        return VoiceChatResponse(
            reply=reply,
            audio=audio_base64,
            corrections=chat_result.get("corrections", []),
            recognized_text=recognized_text
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"语音对话失败: {str(e)}")