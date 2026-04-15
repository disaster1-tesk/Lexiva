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
    # 火山引擎语音
    "zh_cn_female_shaonv": {"name": "小旭少女", "gender": "Female", "accent": "CN"},
    "zh_cn_male_jingying": {"name": "小旭精英", "gender": "Male", "accent": "CN"},
    "zh_cn_female_yujie": {"name": "小旭玉姐", "gender": "Female", "accent": "CN"},
    "zh_cn_male_badao": {"name": "小旭霸道", "gender": "Male", "accent": "CN"},
    # 阿里云语音
    "xiaoyun": {"name": "云小蜜-晓云", "gender": "Female", "accent": "CN"},
    "xiaogang": {"name": "云小蜜-晓刚", "gender": "Male", "accent": "CN"},
    "ruoxi": {"name": "若曦", "gender": "Female", "accent": "CN"},
    "aiqi": {"name": "艾琪", "gender": "Female", "accent": "CN"},
    # 百度语音
    "0": {"name": "度小美", "gender": "Female", "accent": "CN"},
    "1": {"name": "度小宇", "gender": "Male", "accent": "CN"},
    "3": {"name": "度小甜", "gender": "Female", "accent": "CN"},
    "4": {"name": "度小帅", "gender": "Male", "accent": "CN"},
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


# 文本预处理：清理特殊字符，保留可读的标点和格式
def clean_text_for_tts(text: str) -> str:
    """清理文本中的特殊字符，使TTS能正确朗读"""
    if not text:
        return text
    
    # 移除控制字符但保留基本标点
    import re
    # 保留字母、数字、基本标点、空格，换行转为空格
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    # 换行符和多个空格转为单个空格
    cleaned = re.sub(r'[\n\r]+', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    # 移除一些无法朗读的表情符号（保留基本emoji描述）
    cleaned = re.sub(r'[\U0001F600-\U0001F64F]', '', cleaned)  #  emoticons
    cleaned = re.sub(r'[\U0001F300-\U0001F5FF]', '', cleaned)  #  symbols pictographs
    cleaned = re.sub(r'[\U0001F680-\U0001F6FF]', '', cleaned)  #  transport & map
    cleaned = re.sub(r'[\U0001F700-\U0001F77F]', '', cleaned)  #  alchemical
    cleaned = re.sub(r'[\U0001F780-\U0001F7FF]', '', cleaned)  #  Geometric Shapes Extended
    cleaned = re.sub(r'[\U0001F800-\U0001F8FF]', '', cleaned)  #  Supplemental Arrows-C
    cleaned = re.sub(r'[\U0001F900-\U0001F9FF]', '', cleaned)  #  Supplemental Symbols
    cleaned = re.sub(r'[\U0001FA00-\U0001FA6F]', '', cleaned)  #  Chess,dice,domino
    cleaned = re.sub(r'[\U0001FA70-\U0001FAFF]', '', cleaned)  #  Symbols and Pictographs Extended-A
    cleaned = re.sub(r'[\U00002702-\U000027B0]', '', cleaned)  #  Dingbats
    # 移除多余空格
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


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
        
        # 清理文本，移除特殊字符
        text = clean_text_for_tts(text)
        
        start_time = time.time()
        logger.info(f"Edge TTS request: text_len={len(text)}, voice={voice}")
        
        try:
            communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, volume=volume)
            
            # 预热阶段：等待 Edge TTS 服务端初始化完成后再开始收集音频
            # 这样可以避免网络延迟导致的开头几个单词丢失
            await asyncio.sleep(1)  # 等待 300ms 让 Edge TTS 完成初始化
            
            # Collect audio data
            audio_data = bytearray()
            first_audio_received = False
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
        
        # 清理文本，移除特殊字符
        text = clean_text_for_tts(text)
        
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
                "Text": text[:500],  # 限制文本长度，提升到500字符支持更长回复
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


class VolcengineTTSProvider(TTSProvider):
    """火山引擎 TTS Provider (字节跳动)"""
    
    def __init__(self, app_id: str = "", secret_id: str = "", secret_key: str = ""):
        self.app_id = app_id
        self.secret_id = secret_id
        self.secret_key = secret_key
    
    async def synthesize(
        self,
        text: str,
        voice: str = "zh_cn_female_shaonv",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
    ) -> dict:
        """火山引擎 TTS 合成"""
        if not self.secret_id or not self.secret_key:
            return {
                "success": False,
                "error": "火山引擎 TTS 未配置 secret_id 或 secret_key，已自动降级到 Edge TTS",
                "audio": ""
            }
        
        if not text:
            return {"success": False, "error": "No text provided", "audio": ""}
        
        text = clean_text_for_tts(text)
        
        try:
            import httpx
            import hashlib
            import hmac
            import time
            from urllib.parse import quote
            
            # 解析参数
            rate_value = int(rate.replace("+", "").replace("%", ""))
            pitch_value = int(pitch.replace("+", "").replace("Hz", ""))
            
            # 火山引擎 TTS API
            url = "https://openspeech.bytedance.com/api/v2/tts"
            
            # 生成 Authorization header
            timestamp = str(int(time.time()))
            method = "POST"
            path = "/api/v2/tts"
            
            # 构造签名
            signature_str = f"{method} {path}\n{timestamp}\n{self.app_id}"
            signature = hmac.new(
                self.secret_key.encode("utf-8"),
                signature_str.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer; {signature}",
                "X-App-Id": self.app_id,
                "X-Timestamp": timestamp
            }
            
            # 语音映射
            voice_map = {
                "zh_cn_female_shaonv": "zh_cn_female_shaonv",
                "zh_cn_male_jingying": "zh_cn_male_jingying",
                "zh_cn_female_yujie": "zh_cn_female_yujie",
                "zh_cn_male_badao": "zh_cn_male_badao"
            }
            tts_voice = voice_map.get(voice, "zh_cn_female_shaonv")
            
            body = {
                "app": {"appid": self.app_id},
                "user": {"uid": "lexiva_user"},
                "audio": {
                    "voice": tts_voice,
                    "encoding": "mp3",
                    "speed_ratio": 1.0 + (rate_value / 100.0),
                    "pitch_ratio": 1.0 + (pitch_value / 100.0),
                    "volume_ratio": 1.0,
                    "rate": 24000
                },
                "request": {
                    "reqid": str(int(time.time() * 1000)),
                    "text": text[:500],
                    "text_type": "plain",
                    "operation": "submit"
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=body, headers=headers)
                
                if response.status_code != 200:
                    return {"success": False, "error": f"火山引擎 TTS API error: {response.status_code}", "audio": ""}
                
                result = response.json()
                
                if result.get("code") == 1000 or result.get("data"):
                    audio_data = result.get("data", {}).get("audio", "")
                    return {
                        "success": True,
                        "audio": audio_data,
                        "voice": voice,
                        "duration": len(audio_data) / 16000
                    }
                else:
                    return {"success": False, "error": f"火山引擎 TTS 错误: {result.get('message', '未知错误')}", "audio": ""}
                    
        except Exception as e:
            logger.error(f"Volcengine TTS error: {e}")
            return {"success": False, "error": f"火山引擎 TTS 调用失败: {str(e)}", "audio": ""}


class AliyunTTSProvider(TTSProvider):
    """阿里云 TTS Provider"""
    
    def __init__(self, access_key_id: str = "", access_key_secret: str = ""):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
    
    async def synthesize(
        self,
        text: str,
        voice: str = "xiaoyun",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
    ) -> dict:
        """阿里云 TTS 合成"""
        if not self.access_key_id or not self.access_key_secret:
            return {
                "success": False,
                "error": "阿里云 TTS 未配置 access_key_id 或 access_key_secret，已自动降级到 Edge TTS",
                "audio": ""
            }
        
        if not text:
            return {"success": False, "error": "No text provided", "audio": ""}
        
        text = clean_text_for_tts(text)
        
        try:
            import httpx
            import hashlib
            import base64
            import time
            import uuid
            from urllib.parse import quote
            
            # 阿里云 TTS API
            url = "https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/tts"
            
            # 解析参数
            rate_value = int(rate.replace("+", "").replace("%", ""))
            pitch_value = int(pitch.replace("+", "").replace("Hz", ""))
            
            # 语音映射
            voice_map = {
                "xiaoyun": "xiaoyun",
                "xiaogang": "xiaogang",
                "ruoxi": "ruoxi",
                "aiqi": "aiqi"
            }
            tts_voice = voice_map.get(voice, "xiaoyun")
            
            # 构造请求参数
            params = {
                "appkey": "LTAI5t",  # 需要在阿里云控制台获取
                "token": "",  # 需要通过阿里云 STS 获取
                "text": text[:300],
                "format": "mp3",
                "voice": tts_voice,
                "speech_rate": rate_value,
                "pitch_rate": pitch_value
            }
            
            # 注意：实际使用需要先获取 Access Token
            # 这里提供框架，token 获取需要额外实现
            return {
                "success": False,
                "error": "阿里云 TTS 需要先在阿里云控制台获取 AppKey 和 Token，当前版本暂未完整支持",
                "audio": ""
            }
            
        except Exception as e:
            logger.error(f"Aliyun TTS error: {e}")
            return {"success": False, "error": f"阿里云 TTS 调用失败: {str(e)}", "audio": ""}


class BaiduTTSProvider(TTSProvider):
    """百度语音 TTS Provider"""
    
    def __init__(self, app_id: str = "", api_key: str = "", secret_key: str = ""):
        self.app_id = app_id
        self.api_key = api_key
        self.secret_key = secret_key
        self._token = None
        self._token_expires = 0
    
    async def _get_token(self) -> str:
        """获取百度 API Token"""
        import time
        import httpx
        
        # 检查缓存的 token
        if self._token and time.time() < self._token_expires:
            return self._token
        
        if not self.api_key or not self.secret_key:
            return ""
        
        try:
            url = "https://aip.baidubce.com/oauth/2.0/token"
            params = {
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": self.secret_key
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, params=params)
                result = response.json()
                
                if "access_token" in result:
                    self._token = result["access_token"]
                    self._token_expires = time.time() + result.get("expires_in", 2592000) - 300
                    return self._token
        except Exception as e:
            logger.error(f"Baidu token error: {e}")
        
        return ""
    
    async def synthesize(
        self,
        text: str,
        voice: str = "0",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
    ) -> dict:
        """百度语音 TTS 合成"""
        if not self.api_key or not self.secret_key:
            return {
                "success": False,
                "error": "百度语音 TTS 未配置 API Key 或 Secret Key，已自动降级到 Edge TTS",
                "audio": ""
            }
        
        if not text:
            return {"success": False, "error": "No text provided", "audio": ""}
        
        text = clean_text_for_tts(text)
        
        try:
            import httpx
            
            # 获取 token
            token = await self._get_token()
            if not token:
                return {"success": False, "error": "百度语音 Token 获取失败", "audio": ""}
            
            # 解析参数
            rate_value = int(rate.replace("+", "").replace("%", ""))
            pitch_value = int(pitch.replace("+", "").replace("Hz", ""))
            
            # 百度 TTS API
            url = f"https://tsn.baidu.com/text2audio"
            
            params = {
                "tok": token,
                "tex": text[:1024],
                "per": voice,
                "spd": 5 + int(rate_value / 10),  # 0-15, 默认5
                "pit": 5 + int(pitch_value / 10),  # 0-15, 默认5
                "vol": 5,  # 0-15, 默认5
                "cuid": f"lexiva_{self.app_id}",
                "lan": "zh",
                "ctp": 1,
                "aue": 3  # mp3
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, data=params)
                
                # 百度返回二进制音频或 JSON 错误
                content_type = response.headers.get("Content-Type", "")
                if "audio" in content_type:
                    audio_data = base64.b64encode(response.content).decode("utf-8")
                    return {
                        "success": True,
                        "audio": audio_data,
                        "voice": voice,
                        "duration": len(response.content) / 16000
                    }
                else:
                    result = response.json()
                    return {
                        "success": False,
                        "error": f"百度语音 TTS 错误: {result.get('err_msg', '未知错误')}",
                        "audio": ""
                    }
                    
        except Exception as e:
            logger.error(f"Baidu TTS error: {e}")
            return {"success": False, "error": f"百度语音 TTS 调用失败: {str(e)}", "audio": ""}


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
        
        # 清理文本，移除特殊字符
        text = clean_text_for_tts(text)
        
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
        "volcengine": VolcengineTTSProvider,
        "aliyun": AliyunTTSProvider,
        "baidu": BaiduTTSProvider,
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
                    # 检查各云 TTS 是否配置了密钥，未配置则自动降级
                    provider = settings.tts_provider or "edge"
                    
                    if provider == "tencent" and not settings.tencent_secret_id:
                        logger.warning("Tencent TTS secret_id not configured, falling back to Edge TTS")
                        provider = "edge"
                    elif provider == "volcengine" and not settings.volcengine_secret_id:
                        logger.warning("Volcengine TTS secret_id not configured, falling back to Edge TTS")
                        provider = "edge"
                    elif provider == "aliyun" and not settings.aliyun_access_key_id:
                        logger.warning("Aliyun TTS access_key_id not configured, falling back to Edge TTS")
                        provider = "edge"
                    elif provider == "baidu" and not settings.baidu_api_key:
                        logger.warning("Baidu TTS api_key not configured, falling back to Edge TTS")
                        provider = "edge"
                    
                    self._settings = {
                        "provider": provider,
                        "model": settings.tts_model or "en-US-AriaNeural",
                        # 腾讯云
                        "tencent_secret_id": settings.tencent_secret_id or "",
                        "tencent_secret_key": settings.tencent_secret_key or "",
                        "tencent_app_id": settings.tencent_app_id or "",
                        # 火山引擎
                        "volcengine_app_id": settings.volcengine_app_id or "",
                        "volcengine_secret_id": settings.volcengine_secret_id or "",
                        "volcengine_secret_key": settings.volcengine_secret_key or "",
                        # 阿里云
                        "aliyun_access_key_id": settings.aliyun_access_key_id or "",
                        "aliyun_access_key_secret": settings.aliyun_access_key_secret or "",
                        # 百度
                        "baidu_app_id": settings.baidu_app_id or "",
                        "baidu_api_key": settings.baidu_api_key or "",
                        "baidu_secret_key": settings.baidu_secret_key or "",
                    }
                session.close()
            except Exception as e:
                logger.warning(f"Failed to load TTS settings: {e}")
                self._settings = {"provider": "edge", "model": "en-US-AriaNeural"}
        
        return self._settings
    
    def reload_settings(self):
        """重新加载配置"""
        self._settings = None
    
    def _get_provider(self) -> TTSProvider:
        """获取当前配置的 provider"""
        settings = self._get_settings()
        provider_name = settings.get("provider", "edge")
        
        provider_class = self.PROVIDERS.get(provider_name, EdgeTTSProvider)
        
        # 传递各厂商配置
        if provider_name == "tencent":
            return provider_class(
                secret_id=settings.get("tencent_secret_id", ""),
                secret_key=settings.get("tencent_secret_key", "")
            )
        elif provider_name == "volcengine":
            return provider_class(
                app_id=settings.get("volcengine_app_id", ""),
                secret_id=settings.get("volcengine_secret_id", ""),
                secret_key=settings.get("volcengine_secret_key", "")
            )
        elif provider_name == "aliyun":
            return provider_class(
                access_key_id=settings.get("aliyun_access_key_id", ""),
                access_key_secret=settings.get("aliyun_access_key_secret", "")
            )
        elif provider_name == "baidu":
            return provider_class(
                app_id=settings.get("baidu_app_id", ""),
                api_key=settings.get("baidu_api_key", ""),
                secret_key=settings.get("baidu_secret_key", "")
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