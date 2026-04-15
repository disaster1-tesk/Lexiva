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
    # 火山引擎 TTS 配置
    volcengine_app_id: str = ""
    volcengine_secret_id: str = ""
    volcengine_secret_key: str = ""
    # 阿里云 TTS 配置
    aliyun_access_key_id: str = ""
    aliyun_access_key_secret: str = ""
    # 百度语音 TTS 配置
    baidu_app_id: str = ""
    baidu_api_key: str = ""
    baidu_secret_key: str = ""
    # 发音评测配置 (Whisper)
    whisper_provider: str = "faster-whisper"
    whisper_model: str = "base"
    # 火山引擎 ASR 配置
    volcengine_asr_app_id: str = ""
    volcengine_asr_secret_id: str = ""
    volcengine_asr_secret_key: str = ""
    # 阿里云 ASR 配置
    aliyun_asr_access_key_id: str = ""
    aliyun_asr_access_key_secret: str = ""
    # 讯飞语音 ASR 配置
    xfyun_app_id: str = ""
    xfyun_api_key: str = ""
    xfyun_api_secret: str = ""


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
    volcengine_app_id: str = ""
    volcengine_secret_id: str = ""
    volcengine_secret_key: str = ""
    aliyun_access_key_id: str = ""
    aliyun_access_key_secret: str = ""
    baidu_app_id: str = ""
    baidu_api_key: str = ""
    baidu_secret_key: str = ""
    # 发音评测配置 (Whisper)
    whisper_provider: str
    whisper_model: str
    volcengine_asr_app_id: str = ""
    volcengine_asr_secret_id: str = ""
    volcengine_asr_secret_key: str = ""
    aliyun_asr_access_key_id: str = ""
    aliyun_asr_access_key_secret: str = ""
    xfyun_app_id: str = ""
    xfyun_api_key: str = ""
    xfyun_api_secret: str = ""
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
    ],
    "qwen": [  # 通义千问
        "qwen-turbo",
        "qwen-plus",
        "qwen-max",
        "qwen-long"
    ],
    "zhipu": [  # 智谱清言
        "glm-4",
        "glm-4-flash",
        "glm-4-plus",
        "glm-3-turbo"
    ],
    "anthropic": [  # Claude
        "claude-3-5-sonnet-20241022",
        "claude-3-5-sonnet-20240620",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229"
    ],
    "google": [  # Gemini
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b"
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
    ],
    "volcengine": [  # 火山引擎
        {"id": "zh_cn_female_shaonv", "name": "小旭少女", "gender": "女"},
        {"id": "zh_cn_male_jingying", "name": "小旭精英", "gender": "男"},
        {"id": "zh_cn_female_yujie", "name": "小旭玉姐", "gender": "女"},
        {"id": "zh_cn_male_badao", "name": "小旭霸道", "gender": "男"}
    ],
    "aliyun": [  # 阿里云
        {"id": "xiaoyun", "name": "云小蜜-晓云", "gender": "女"},
        {"id": "xiaogang", "name": "云小蜜-晓刚", "gender": "男"},
        {"id": "ruoxi", "name": "若曦", "gender": "女"},
        {"id": "aiqi", "name": "艾琪", "gender": "女"}
    ],
    "baidu": [  # 百度语音
        {"id": "0", "name": "度小美 (女声)", "gender": "女"},
        {"id": "1", "name": "度小宇 (男声)", "gender": "男"},
        {"id": "3", "name": "度小甜 (女声)", "gender": "女"},
        {"id": "4", "name": "度小帅 (男声)", "gender": "男"}
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
    ],
    "volcengine": [  # 火山引擎
        {"id": "volcengine_streaming", "name": "实时语音识别", "description": "流式识别，低延迟"},
        {"id": "volcengine_non_streaming", "name": "非实时语音识别", "description": "整段音频识别"}
    ],
    "aliyun": [  # 阿里云
        {"id": "paraformer-plus", "name": "Paraformer Plus", "description": "新一代非流式识别"},
        {"id": "paraformer", "name": "Paraformer", "description": "非流式识别"}
    ],
    "xfyun": [  # 讯飞语音
        {"id": "sms16k", "name": "16k 中文普通话", "description": "16k采样率中文"},
        {"id": "sms8k", "name": "8k 中文普通话", "description": "8k采样率中文"}
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
            volcengine_app_id=settings.volcengine_app_id or "",
            volcengine_secret_id=settings.volcengine_secret_id or "",
            volcengine_secret_key=settings.volcengine_secret_key or "",
            aliyun_access_key_id=settings.aliyun_access_key_id or "",
            aliyun_access_key_secret=settings.aliyun_access_key_secret or "",
            baidu_app_id=settings.baidu_app_id or "",
            baidu_api_key=settings.baidu_api_key or "",
            baidu_secret_key=settings.baidu_secret_key or "",
            whisper_provider=settings.whisper_provider or "faster-whisper",
            whisper_model=settings.whisper_model or "base",
            volcengine_asr_app_id=settings.volcengine_asr_app_id or "",
            volcengine_asr_secret_id=settings.volcengine_asr_secret_id or "",
            volcengine_asr_secret_key=settings.volcengine_asr_secret_key or "",
            aliyun_asr_access_key_id=settings.aliyun_asr_access_key_id or "",
            aliyun_asr_access_key_secret=settings.aliyun_asr_access_key_secret or "",
            xfyun_app_id=settings.xfyun_app_id or "",
            xfyun_api_key=settings.xfyun_api_key or "",
            xfyun_api_secret=settings.xfyun_api_secret or "",
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
        # 火山引擎 TTS 配置
        if request.volcengine_app_id:
            settings.volcengine_app_id = request.volcengine_app_id
        if request.volcengine_secret_id:
            settings.volcengine_secret_id = request.volcengine_secret_id
        if request.volcengine_secret_key:
            settings.volcengine_secret_key = request.volcengine_secret_key
        # 阿里云 TTS 配置
        if request.aliyun_access_key_id:
            settings.aliyun_access_key_id = request.aliyun_access_key_id
        if request.aliyun_access_key_secret:
            settings.aliyun_access_key_secret = request.aliyun_access_key_secret
        # 百度语音 TTS 配置
        if request.baidu_app_id:
            settings.baidu_app_id = request.baidu_app_id
        if request.baidu_api_key:
            settings.baidu_api_key = request.baidu_api_key
        if request.baidu_secret_key:
            settings.baidu_secret_key = request.baidu_secret_key
        
        # Whisper 配置
        settings.whisper_provider = request.whisper_provider
        settings.whisper_model = request.whisper_model
        # 火山引擎 ASR 配置
        if request.volcengine_asr_app_id:
            settings.volcengine_asr_app_id = request.volcengine_asr_app_id
        if request.volcengine_asr_secret_id:
            settings.volcengine_asr_secret_id = request.volcengine_asr_secret_id
        if request.volcengine_asr_secret_key:
            settings.volcengine_asr_secret_key = request.volcengine_asr_secret_key
        # 阿里云 ASR 配置
        if request.aliyun_asr_access_key_id:
            settings.aliyun_asr_access_key_id = request.aliyun_asr_access_key_id
        if request.aliyun_asr_access_key_secret:
            settings.aliyun_asr_access_key_secret = request.aliyun_asr_access_key_secret
        # 讯飞语音 ASR 配置
        if request.xfyun_app_id:
            settings.xfyun_app_id = request.xfyun_app_id
        if request.xfyun_api_key:
            settings.xfyun_api_key = request.xfyun_api_key
        if request.xfyun_api_secret:
            settings.xfyun_api_secret = request.xfyun_api_secret
        
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
            volcengine_app_id=settings.volcengine_app_id or "",
            volcengine_secret_id=settings.volcengine_secret_id or "",
            volcengine_secret_key=settings.volcengine_secret_key or "",
            aliyun_access_key_id=settings.aliyun_access_key_id or "",
            aliyun_access_key_secret=settings.aliyun_access_key_secret or "",
            baidu_app_id=settings.baidu_app_id or "",
            baidu_api_key=settings.baidu_api_key or "",
            baidu_secret_key=settings.baidu_secret_key or "",
            whisper_provider=settings.whisper_provider or "faster-whisper",
            whisper_model=settings.whisper_model or "base",
            volcengine_asr_app_id=settings.volcengine_asr_app_id or "",
            volcengine_asr_secret_id=settings.volcengine_asr_secret_id or "",
            volcengine_asr_secret_key=settings.volcengine_asr_secret_key or "",
            aliyun_asr_access_key_id=settings.aliyun_asr_access_key_id or "",
            aliyun_asr_access_key_secret=settings.aliyun_asr_access_key_secret or "",
            xfyun_app_id=settings.xfyun_app_id or "",
            xfyun_api_key=settings.xfyun_api_key or "",
            xfyun_api_secret=settings.xfyun_api_secret or "",
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
            {"id": "ollama", "name": "Ollama", "description": "本地部署模型"},
            {"id": "qwen", "name": "通义千问", "description": "阿里云，国内可用"},
            {"id": "zhipu", "name": "智谱清言", "description": "ChatGLM，国内可用"},
            {"id": "anthropic", "name": "Claude", "description": "Anthropic，需科学上网"},
            {"id": "google", "name": "Gemini", "description": "Google AI，需科学上网"}
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
            {"id": "tencent", "name": "腾讯云 TTS", "description": "付费云端语音，需配置密钥"},
            {"id": "volcengine", "name": "火山引擎 TTS", "description": "字节跳动语音合成，需配置密钥"},
            {"id": "aliyun", "name": "阿里云 TTS", "description": "阿里云语音合成，需配置密钥"},
            {"id": "baidu", "name": "百度语音 TTS", "description": "百度语音合成，需配置密钥"}
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
            {"id": "tencent", "name": "腾讯云语音识别", "description": "云端识别，需配置密钥"},
            {"id": "volcengine", "name": "火山引擎语音识别", "description": "字节跳动云端识别，需配置密钥"},
            {"id": "aliyun", "name": "阿里云语音识别", "description": "阿里云云端识别，需配置密钥"},
            {"id": "xfyun", "name": "讯飞语音识别", "description": "讯飞云端识别，需配置密钥"}
        ]
    }