"""
Chat API Routes
AI conversation endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.ai_chat import chat_service
from db.connection import get_db
from models import Conversation


# Request model
class ChatRequest(BaseModel):
    message: str
    scene: str = "daily"


# Response model
class ChatResponse(BaseModel):
    reply: str
    corrections: list


router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Send a message and get AI response
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    result = await chat_service.chat(request.message, request.scene)
    
    # Save to database
    session = next(get_db())
    try:
        conversation = Conversation(
            scene=request.scene,
            user_message=request.message,
            ai_message=result["reply"],
            corrections=result.get("corrections", [])
        )
        session.add(conversation)
        session.commit()
    finally:
        session.close()
    
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
        session.close()


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
        session.close()