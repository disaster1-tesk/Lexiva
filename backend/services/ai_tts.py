"""
Text-to-Speech Service - 支持多 Provider
"""
import os
import io
import base64
import asyncio
import logging
import time
from typing import Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Try to import edge-tts
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    logger.warning("edge-tts not installed. Run: pip install edge-tts")

# Try to import CosyVoice
try:
    from cosyvoice.cli.cosyvoice import CosyVoice
    from cosyvoice.dataset.preprocess import perphone
    COSYVOICE_AVAILABLE = True
except ImportError:
    COSYVOICE_AVAILABLE = False
    logger.warning("CosyVoice not installed. Run: pip install cosyvoice for high-quality Chinese TTS")


# Available Edge TTS voices
VOICES = {
    "en-US-AriaNeural": {"name": "Aria", "gender": "Female", "accent": "US"},
    "en-US-GuyNeural": {"name": "Guy", "gender": "Male", "accent": "US"},
    "en-GB-SoniaNeural": {"name": "Sonia", "gender": "Female", "accent": "UK"},
    "en-GB-RyanNeural": {"name": "Ryan", "gender": "Male", "accent": "UK"},
    "en-AU-NatashaNeural": {"name": "Natasha", "gender": "Female", "accent": "AU"},
    "en-AU-ConnorNeural": {"name": "Connor", "gender": "Male", "accent": "AU"},
    "zh-CN-XiaoxiaoNeural": {"name": "晓晓", "gender": "Female", "accent": "CN"},
    "zh-CN-YunxiNeural": {"name": "云希", "gender": "Male", "accent": "CN"},
}


class TTSProvider(ABC):
    """TTS Provider 基类"""
    
    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice: str,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
    ) -> dict:
        """合成语音"""
        pass


class EdgeTTSProvider(TTSProvider):
    """Microsoft Edge TTS Provider"""
    
    async def synthesize(
        self,
        text: str,
        voice: str = "en-US-AriaNeural",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
    ) -> dict:
        """Convert text to speech using Edge TTS"""
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
        
        start_time = time.time()
        logger.info(f"Edge TTS request: text_len={len(text)}, voice={voice}")
        
        try:
            communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, volume=volume)
            
            # Collect audio data
            audio_data = bytearray()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data.extend(chunk["data"])
            
            if not audio_data:
                raise Exception("No audio was received")
            
            # Encode to base64
            audio_base64 = base64.b64encode(bytes(audio_data)).decode("utf-8")
            
            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(f"Edge TTS success: voice={voice}, audio_size={len(audio_data)}, elapsed_ms={elapsed_ms:.0f}")
            
            return {
                "success": True,
                "audio": audio_base64,
                "voice": voice,
                "duration": len(audio_data) / 16000
            }
            
        except Exception as e:
            logger.error(f"Edge TTS error: {e}")
            error_msg = str(e)
            if "No audio was received" in error_msg:
                return {
                    "success": False,
                    "error": "语音服务暂时不可用，请稍后重试或更换语音类型。",
                    "audio": ""
                }
            return {
                "success": False,
                "error": error_msg,
                "audio": ""
            }


class TencentTTSProvider(TTSProvider):
    """腾讯云 TTS Provider"""
    
    def __init__(self, secret_id: str = "", secret_key: str = ""):
        self.secret_id = secret_id
        self.secret_key = secret_key
    
    async def synthesize(
        self,
        text: str,
        voice: str = "cloud",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
    ) -> dict:
        """腾讯云 TTS 合成"""
        # 检查是否配置了密钥
        if not self.secret_id or not self.secret_key:
            return {
                "success": False,
                "error": "腾讯云 TTS 未配置 secret_id 或 secret_key，已自动降级到 Edge TTS",
                "audio": ""
            }
        
        if not text:
            return {
                "success": False,
                "error": "No text provided",
                "audio": ""
            }
        
        try:
            import httpx
            import hashlib
            import hmac
            import time
            from urllib.parse import urlencode
            
            # 解析 rate 参数 (如 "+0%" -> "0")
            rate_value = rate.replace("+", "").replace("%", "")
            pitch_value = pitch.replace("+", "").replace("Hz", "")
            
            # 腾讯云 TTS API 参数
            params = {
                "Action": "TextToSpeech",
                "Version": "2020-04-01",
                "Region": "ap-guangzhou",
                "SecretId": self.secret_id,
                "Timestamp": str(int(time.time())),
                "Nonce": str(int(time.time() * 1000) % 100000),
                "Text": text[:200],  # 限制文本长度
                "SessionId": str(int(time.time() * 1000)),
                "ModelType": 1,  # 基础模型
                "VoiceType": 1,  # 1: 基础音库, 0: 精品音库
                "Speed": int(rate_value),
                "Pitch": int(pitch_value),
                "Volume": 0,
                "Codec": "mp3",
                "Format": "mp3"
            }
            
            # 生成签名 (简单的 hmac-sha1)
            def generate_signature(params, secret_key):
                # 排序参数
                sorted_params = sorted(params.items())
                param_str = "&".join([f"{k}={v}" for k, v in sorted_params])
                # 生成签名
                signature = hmac.new(
                    secret_key.encode("utf-8"),
                    param_str.encode("utf-8"),
                    hashlib.sha1
                ).hexdigest()
                return signature
            
            params["Signature"] = generate_signature(params, self.secret_key)
            
            # 发送请求
            url = "https://tts.tencentcloudapi.com/"
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, data=params)
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"TTS API error: {response.status_code}",
                        "audio": ""
                    }
                
                # 检查响应
                result_data = response.json()
                
                if "Response" in result_data and "Audio" in result_data["Response"]:
                    audio_base64 = result_data["Response"]["Audio"]
                    return {
                        "success": True,
                        "audio": audio_base64,
                        "voice": "tencent-cloud",
                        "duration": len(audio_base64) / 16000
                    }
                elif "Response" in result_data and "Error" in result_data["Response"]:
                    error = result_data["Response"]["Error"]
                    return {
                        "success": False,
                        "error": f"腾讯云 TTS 错误: {error.get('Message', '未知错误')}",
                        "audio": ""
                    }
                else:
                    return {
                        "success": False,
                        "error": "腾讯云 TTS 响应格式错误",
                        "audio": ""
                    }
                    
        except Exception as e:
            logger.error(f"Tencent TTS error: {e}")
            return {
                "success": False,
                "error": f"腾讯云 TTS 调用失败: {str(e)}",
                "audio": ""
            }


class CosyVoiceProvider(TTSProvider):
    """本地 CosyVoice TTS Provider - 高音质中文语音合成"""
    
    def __init__(self):
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load CosyVoice model"""
        if not COSYVOICE_AVAILABLE:
            logger.warning("CosyVoice not available. Using fallback to Edge TTS.")
            self.fallback_provider = EdgeTTSProvider()
            return
        
        try:
            logger.info("Loading CosyVoice model...")
            # CosyVoice 会自动下载默认模型
            # 如果需要指定模型路径，可以在初始化时配置
            # 使用 CPU 模式以支持流式
            self.model = CosyVoice('cpu')
            logger.info("CosyVoice model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load CosyVoice model: {e}, falling back to Edge TTS")
            self.fallback_provider = EdgeTTSProvider()
            self.model = None
    
    async def synthesize(
        self,
        text: str,
        voice: str = "female",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
    ) -> dict:
        """使用 CosyVoice 合成语音"""
        # 如果 CosyVoice 不可用，使用降级方案
        if self.model is None:
            if hasattr(self, 'fallback_provider'):
                return await self.fallback_provider.synthesize(text, voice, rate, pitch, volume)
            return {
                "success": False,
                "error": "CosyVoice model not loaded",
                "audio": ""
            }
        
        if not text:
            return {
                "success": False,
                "error": "No text provided",
                "audio": ""
            }
        
        start_time = time.time()
        
        try:
            # CosyVoice 音色映射
            # 支持的音色: female, male, 或者是自定义音色
            voice_map = {
                "female": "Female",
                "male": "Male",
                "zh-CN-XiaoxiaoNeural": "Female",  # 兼容 Edge TTS 语音名
                "zh-CN-YunxiNeural": "Male",
                "en-US-AriaNeural": "Female",
                "en-US-GuyNeural": "Male",
            }
            cosyvoice_voice = voice_map.get(voice, "Female")
            
            # 解析 rate 参数 (+0% -> 0)
            rate_value = int(rate.replace("+", "").replace("%", ""))
            # 语速调整: CosyVoice 的 speed 参数范围通常在 0.5-2.0
            speed = 1.0 + (rate_value / 100.0)
            
            # 使用 CosyVoice 合成
            loop = asyncio.get_event_loop()
            
            def synthesize_sync():
                # CosyVoice 的 API 调用方式
                # 返回生成音频的列表
                result = self.model.inference(
                    text,
                    cosyvoice_voice,
                    stream=False
                )
                return result
            
            # 执行合成 (在线程池中以避免阻塞)
            audio_result = await loop.run_in_executor(None, synthesize_sync)
            
            # 收集音频数据
            audio_data = bytearray()
            if hasattr(audio_result, '__iter__'):
                for chunk in audio_result:
                    # 可能是音频数据块
                    if hasattr(chunk, 'numpy'):
                        # 如果是 tensor，转换为 bytes
                        import numpy as np
                        chunk = chunk.numpy()
                    if isinstance(chunk, np.ndarray):
                        # numpy array 转 bytes (16-bit PCM)
                        audio_data.extend(chunk.tobytes())
                    elif isinstance(chunk, bytes):
                        audio_data.extend(chunk)
            
            if not audio_data:
                # 如果没有收集到数据，尝试降级
                return await self.fallback_provider.synthesize(text, voice, rate, pitch, volume)
            
            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(f"CosyVoice success: voice={voice}, audio_size={len(audio_data)}, elapsed_ms={elapsed_ms:.0f}")
            
            # 转换为 base64
            audio_base64 = base64.b64encode(bytes(audio_data)).decode("utf-8")
            
            return {
                "success": True,
                "audio": audio_base64,
                "voice": voice,
                "duration": len(audio_data) / 16000  # 假设 16kHz
            }
            
        except Exception as e:
            logger.error(f"CosyVoice error: {e}", exc_info=True)
            # 出现异常时自动降级
            if hasattr(self, 'fallback_provider'):
                return await self.fallback_provider.synthesize(text, voice, rate, pitch, volume)
            return {
                "success": False,
                "error": str(e),
                "audio": ""
            }
    
    async def synthesize_stream(
        self,
        text: str,
        voice: str = "female"
    ) -> dict:
        """流式合成 - 用于实时语音通话
        
        返回格式: {
            "success": True,
            "chunks": [{"audio": base64, "is_final": bool}, ...],
            "voice": str
        }
        """
        if self.model is None:
            if hasattr(self, 'fallback_provider'):
                return await self.fallback_provider.synthesize(text, voice)
            return {
                "success": False,
                "error": "CosyVoice model not loaded",
                "chunks": []
            }
        
        try:
            voice_map = {"female": "Female", "male": "Male"}
            cosyvoice_voice = voice_map.get(voice, "Female")
            
            loop = asyncio.get_event_loop()
            chunks = []
            
            def synthesize_stream_sync():
                # 流式生成
                for i, chunk in enumerate(self.model.inference(text, cosyvoice_voice, stream=True)):
                    audio_bytes = chunk.numpy().tobytes() if hasattr(chunk, 'numpy') else b''
                    chunks.append({
                        "audio": base64.b64encode(audio_bytes).decode("utf-8"),
                        "is_final": False
                    })
                # 标记最后一个 chunk
                if chunks:
                    chunks[-1]["is_final"] = True
            
            await loop.run_in_executor(None, synthesize_stream_sync)
            
            return {
                "success": True,
                "chunks": chunks,
                "voice": voice
            }
        except Exception as e:
            logger.error(f"CosyVoice stream error: {e}")
            return {
                "success": False,
                "error": str(e),
                "chunks": []
            }


class TTService:
    """TTS 服务入口 - 支持配置和自动降级"""
    
    # 可用 provider 映射
    PROVIDERS = {
        "edge": EdgeTTSProvider,
        "cosyvoice": CosyVoiceProvider,
        "tencent": TencentTTSProvider,
    }
    
    # 重试备用语音列表
    FALLBACK_VOICES = [
        "en-US-AriaNeural",
        "en-GB-SoniaNeural",
        "en-US-GuyNeural",
        "en-GB-RyanNeural",
    ]
    
    def __init__(self):
        self._settings = None
    
    def _get_settings(self) -> dict:
        """从数据库获取 TTS 配置"""
        if self._settings is None:
            try:
                from db.connection import get_db
                from models import AISettings
                session = next(get_db())
                settings = session.query(AISettings).first()
                if settings:
                    # 检查腾讯云 TTS 是否配置了密钥
                    provider = settings.tts_provider or "cosyvoice"
                    if provider == "tencent" and not settings.tencent_secret_id:
                        # 未配置密钥，自动降级到 CosyVoice
                        logger.warning("Tencent TTS secret_id not configured, falling back to CosyVoice")
                        provider = "cosyvoice"
                    
                    self._settings = {
                        "provider": provider,
                        "model": settings.tts_model or "female",
                        "tencent_secret_id": settings.tencent_secret_id or "",
                        "tencent_secret_key": settings.tencent_secret_key or "",
                        "tencent_app_id": settings.tencent_app_id or "",
                    }
                session.close()
            except Exception as e:
                logger.warning(f"Failed to load TTS settings: {e}")
                self._settings = {"provider": "cosyvoice", "model": "female"}
        
        return self._settings
    
    def reload_settings(self):
        """重新加载配置"""
        self._settings = None
    
    def _get_provider(self) -> TTSProvider:
        """获取当前配置的 provider"""
        settings = self._get_settings()
        provider_name = settings.get("provider", "edge")
        
        provider_class = self.PROVIDERS.get(provider_name, EdgeTTSProvider)
        
        # 传递腾讯云配置
        if provider_name == "tencent":
            return provider_class(
                secret_id=settings.get("tencent_secret_id", ""),
                secret_key=settings.get("tencent_secret_key", "")
            )
        
        return provider_class()
    
    async def synthesize(
        self,
        text: str,
        voice: str = None,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
    ) -> dict:
        """合成语音 - 支持自动重试和降级"""
        settings = self._get_settings()
        voice = voice or settings.get("model", "en-US-AriaNeural")
        
        # 第一次尝试
        result = await self._synthesize_with_provider(voice, text, rate, pitch, volume)
        
        # 如果失败，尝试切换语音重试
        if not result.get("success"):
            logger.warning(f"TTS failed, trying fallback voices...")
            for fallback_voice in self.FALLBACK_VOICES:
                if fallback_voice == voice:
                    continue
                logger.info(f"TTS fallback: trying voice={fallback_voice}")
                result = await self._synthesize_with_provider(fallback_voice, text, rate, pitch, volume)
                if result.get("success"):
                    break
        
        # 如果 Edge 也失败，尝试降级到其他 provider
        if not result.get("success") and settings.get("provider") == "edge":
            logger.warning("Edge TTS failed, trying alternative providers...")
            for alt_provider in ["tencent"]:
                if alt_provider == "edge":
                    continue
                alt_provider_class = self.PROVIDERS.get(alt_provider)
                if alt_provider_class:
                    alt_provider = alt_provider_class()
                    result = await alt_provider.synthesize(text, voice, rate, pitch, volume)
                    if result.get("success"):
                        break
        
        return result
    
    async def _synthesize_with_provider(
        self,
        voice: str,
        text: str,
        rate: str,
        pitch: str,
        volume: str
    ) -> dict:
        """使用当前 provider 合成"""
        provider = self._get_provider()
        return await provider.synthesize(text, voice, rate, pitch, volume)
    
    def get_available_voices(self) -> list:
        """获取可用语音列表"""
        return [
            {"value": key, "label": f"{v['name']} ({v['gender']}) - {v['accent']}"}
            for key, v in VOICES.items()
        ]


# 全局实例
tts_service = TTService()