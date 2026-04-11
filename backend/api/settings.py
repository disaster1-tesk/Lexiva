"""
Settings API Routes
AI model configuration endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.connection import get_db
from models import AISettings
from datetime import datetime
from services.ai_chat import chat_service


# Request model
class AISettingsRequest(BaseModel):
    provider: str = "deepseek"
    api_key: str = ""
    model: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 1.0
    base_url: str = ""


# Response model
class AISettingsResponse(BaseModel):
    id: int
    provider: str
    model: str
    temperature: float
    max_tokens: int
    top_p: float
    base_url: str
    created_at: str
    updated_at: str


router = APIRouter(prefix="/api/settings", tags=["Settings"])


# Available models per provider
AVAILABLE_MODELS = {
    "deepseek": [
        "deepseek-chat",
        "deepseek-coder"
    ],
    "openai": [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-3.5-turbo"
    ],
    "ollama": [
        "llama3",
        "llama3.2",
        "mistral",
        "qwen2",
        "phi3"
    ]
}


@router.get("/ai", response_model=AISettingsResponse)
async def get_ai_settings():
    """
    Get AI settings (returns first record or creates default)
    """
    session = next(get_db())
    try:
        settings = session.query(AISettings).first()
        
        if not settings:
            # Create default settings
            settings = AISettings(
                provider="deepseek",
                api_key="",
                model="deepseek-chat",
                temperature=0.7,
                max_tokens=1000,
                top_p=1.0,
                base_url=""
            )
            session.add(settings)
            session.commit()
            session.refresh(settings)
        
        return AISettingsResponse(
            id=settings.id,
            provider=settings.provider,
            model=settings.model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            top_p=settings.top_p,
            base_url=settings.base_url or "",
            created_at=settings.created_at.isoformat(),
            updated_at=settings.updated_at.isoformat()
        )
    finally:
        session.close()


@router.post("/ai", response_model=AISettingsResponse)
async def update_ai_settings(request: AISettingsRequest):
    """
    Update AI settings
    """
    session = next(get_db())
    try:
        settings = session.query(AISettings).first()
        
        if not settings:
            settings = AISettings()
            session.add(settings)
        
        # Update fields
        settings.provider = request.provider
        settings.model = request.model
        settings.temperature = request.temperature
        settings.max_tokens = request.max_tokens
        settings.top_p = request.top_p
        settings.base_url = request.base_url
        settings.updated_at = datetime.utcnow()
        
        # Only update api_key if provided (don't clear existing)
        if request.api_key:
            settings.api_key = request.api_key
        
        session.commit()
        session.refresh(settings)

        # Clear chat service cache to apply new settings
        chat_service.reload_settings()

        return AISettingsResponse(
            id=settings.id,
            provider=settings.provider,
            model=settings.model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            top_p=settings.top_p,
            base_url=settings.base_url or "",
            created_at=settings.created_at.isoformat(),
            updated_at=settings.updated_at.isoformat()
        )
    finally:
        session.close()


@router.get("/ai/models")
async def get_available_models(provider: str = "deepseek"):
    """
    Get available models for a provider
    """
    models = AVAILABLE_MODELS.get(provider, AVAILABLE_MODELS["deepseek"])
    return {
        "provider": provider,
        "models": models
    }


@router.get("/ai/providers")
async def get_providers():
    """
    Get available providers
    """
    return {
        "providers": [
            {"id": "deepseek", "name": "DeepSeek", "description": "国产大模型，国内可用"},
            {"id": "openai", "name": "OpenAI", "description": "GPT系列，需科学上网"},
            {"id": "ollama", "name": "Ollama", "description": "本地部署模型"}
        ]
    }