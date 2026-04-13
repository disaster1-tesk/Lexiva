"""
Settings API Routes
AI model configuration endpoints
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.connection import get_db
from models import AISettings
from datetime import datetime
from services.ai_chat import chat_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["Settings"])


# Request model
class AISettingsRequest(BaseModel):
    provider: str = "deepseek"
    api_key: str = ""
    model: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 1.0
    base_url: str = ""
    # TTS 配置
    tts_provider: str = "edge"
    tts_model: str = "en-US-AriaNeural"
    # 腾讯云 TTS 配置
    tencent_secret_id: str = ""
    tencent_secret_key: str = ""
    tencent_app_id: str = ""
    # 发音评测配置 (Whisper)
    whisper_provider: str = "faster-whisper"
    whisper_model: str = "base"


# Response model
class AISettingsResponse(BaseModel):
    id: int
    provider: str
    model: str
    temperature: float
    max_tokens: int
    top_p: float
    base_url: str
    # TTS 配置
    tts_provider: str
    tts_model: str
    tencent_secret_id: str = ""
    tencent_secret_key: str = ""
    tencent_app_id: str = ""
    # 发音评测配置 (Whisper)
    whisper_provider: str
    whisper_model: str
    created_at: str
    updated_at: str


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

# TTS 可用语音
TTS_VOICES = {
    "edge": [
        {"id": "en-US-AriaNeural", "name": "Aria (美式英语)", "gender": "女"},
        {"id": "en-US-GuyNeural", "name": "Guy (美式英语)", "gender": "男"},
        {"id": "en-GB-SoniaNeural", "name": "Sonia (英式英语)", "gender": "女"},
        {"id": "en-GB-RyanNeural", "name": "Ryan (英式英语)", "gender": "男"},
        {"id": "en-AU-NatashaNeural", "name": "Natasha (澳式英语)", "gender": "女"},
        {"id": "en-AU-ConnorNeural", "name": "Connor (澳式英语)", "gender": "男"},
        {"id": "zh-CN-XiaoxiaoNeural", "name": "晓晓 (中文)", "gender": "女"},
        {"id": "zh-CN-YunxiNeural", "name": "云希 (中文)", "gender": "男"}
    ],
    "tencent": [
        {"id": "cloud", "name": "默认云端语音", "gender": "混音"}
    ]
}

# Whisper 可用模型
WHISPER_MODELS = {
    "faster-whisper": [
        {"id": "tiny", "name": "Tiny (最快,最低精度)", "size": "~75MB"},
        {"id": "base", "name": "Base (平衡)", "size": "~150MB"},
        {"id": "small", "name": "Small (较高精度)", "size": "~250MB"},
        {"id": "medium", "name": "Medium (高精度)", "size": "~500MB"}
    ],
    "openai": [
        {"id": "whisper-1", "name": "Whisper-1", "description": "OpenAI 云端识别"}
    ],
    "tencent": [
        {"id": "16k", "name": "16k (中文普通话)", "description": "采样率16k"},
        {"id": "8k", "name": "8k (中文普通话)", "description": "采样率8k"}
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
                base_url="",
                tts_provider="edge",
                tts_model="en-US-AriaNeural",
                whisper_provider="faster-whisper",
                whisper_model="base"
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
            tts_provider=settings.tts_provider or "edge",
            tts_model=settings.tts_model or "en-US-AriaNeural",
            tencent_secret_id=settings.tencent_secret_id or "",
            tencent_secret_key=settings.tencent_secret_key or "",
            tencent_app_id=settings.tencent_app_id or "",
            whisper_provider=settings.whisper_provider or "faster-whisper",
            whisper_model=settings.whisper_model or "base",
            created_at=settings.created_at.isoformat(),
            updated_at=settings.updated_at.isoformat()
        )
    finally:
        try:
            session.close()
        except Exception:
            pass


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
        settings.updated_at = datetime.now()
        
        # TTS 配置
        settings.tts_provider = request.tts_provider
        settings.tts_model = request.tts_model
        # 腾讯云 TTS 配置
        if request.tencent_secret_id:
            settings.tencent_secret_id = request.tencent_secret_id
        if request.tencent_secret_key:
            settings.tencent_secret_key = request.tencent_secret_key
        if request.tencent_app_id:
            settings.tencent_app_id = request.tencent_app_id
        
        # Whisper 配置
        settings.whisper_provider = request.whisper_provider
        settings.whisper_model = request.whisper_model
        
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
            tts_provider=settings.tts_provider or "edge",
            tts_model=settings.tts_model or "en-US-AriaNeural",
            tencent_secret_id=settings.tencent_secret_id or "",
            tencent_secret_key=settings.tencent_secret_key or "",
            tencent_app_id=settings.tencent_app_id or "",
            whisper_provider=settings.whisper_provider or "faster-whisper",
            whisper_model=settings.whisper_model or "base",
            created_at=settings.created_at.isoformat(),
            updated_at=settings.updated_at.isoformat()
        )
    finally:
        try:
            session.close()
        except Exception:
            pass


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


@router.get("/ai/tts/voices")
async def get_tts_voices(provider: str = "edge"):
    """
    Get available TTS voices for a provider
    """
    voices = TTS_VOICES.get(provider, TTS_VOICES.get("edge", []))
    return {
        "provider": provider,
        "voices": voices
    }


@router.get("/ai/tts/providers")
async def get_tts_providers():
    """
    Get available TTS providers
    """
    return {
        "providers": [
            {"id": "edge", "name": "Edge TTS", "description": "微软 Edge 免费语音，免费稳定"},
            {"id": "tencent", "name": "腾讯云 TTS", "description": "付费云端语音，需配置密钥"}
        ]
    }


@router.get("/ai/whisper/models")
async def get_whisper_models(provider: str = "faster-whisper"):
    """
    Get available Whisper models for a provider
    """
    models = WHISPER_MODELS.get(provider, WHISPER_MODELS.get("faster-whisper", []))
    return {
        "provider": provider,
        "models": models
    }


@router.get("/ai/whisper/providers")
async def get_whisper_providers():
    """
    Get available Whisper providers
    """
    return {
        "providers": [
            {"id": "faster-whisper", "name": "Faster Whisper", "description": "本地模型，无需网络"},
            {"id": "openai", "name": "OpenAI Whisper", "description": "云端识别，需配置 API Key"},
            {"id": "tencent", "name": "腾讯云语音识别", "description": "云端识别，需配置密钥"}
        ]
    }