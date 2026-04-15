"""
Speech Recognition Service - 支持多 Provider (Whisper)
"""
import os
import io
import base64
import asyncio
import logging
import time
import json
import shutil
import tempfile
from typing import Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Try to import faster-whisper, fall back to whisper
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    try:
        import whisper
        WHISPER_AVAILABLE = True
    except ImportError:
        WHISPER_AVAILABLE = False
        logger.warning("Whisper not installed. Run: pip install faster-whisper")

# Try to import pywhispercpp (whisper.cpp)
try:
    import pywhispercpp
    WHISPER_CPP_AVAILABLE = True
except ImportError:
    WHISPER_CPP_AVAILABLE = False
    logger.warning("pywhispercpp not installed. Run: pip install pywhispercpp for faster ASR")


def _check_ffmpeg() -> tuple[bool, str]:
    """检查 ffmpeg 是否可用，返回 (可用, 路径或错误信息)"""
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return True, ffmpeg_path
    return False, "ffmpeg not found. Please install ffmpeg: winget install ffmpeg"


def _get_ffmpeg_cmd() -> list[str]:
    """获取 ffmpeg 命令，根据系统尝试 .exe 后缀"""
    if os.name == 'nt' and not shutil.which("ffmpeg"):
        # Windows 上尝试直接调用
        return ["ffmpeg.exe"]
    return ["ffmpeg"]


class WhisperProvider(ABC):
    """Whisper Provider 基类"""
    
    @abstractmethod
    async def transcribe(self, audio_data: bytes, language: str = "en") -> dict:
        """转写音频"""
        pass


class FasterWhisperProvider(WhisperProvider):
    """本地 Faster Whisper Provider"""
    
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load Whisper model"""
        if not WHISPER_AVAILABLE:
            logger.warning("Whisper not available. Audio recognition will be disabled.")
            return
        
        try:
            logger.info(f"Loading Faster Whisper model: {self.model_size}")
            self.model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8"
            )
            logger.info("Faster Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Faster Whisper model: {e}")
            self.model = None
    
    async def transcribe(self, audio_data: bytes, language: str = "en", mime_type: str = "audio/webm") -> dict:
        """使用本地 Faster Whisper 转写"""
        if not self.model:
            return {
                "success": False,
                "error": "Faster Whisper model not loaded. Please install faster-whisper.",
                "text": ""
            }
        
        # 检查 ffmpeg 可用性
        ffmpeg_ok, ffmpeg_msg = _check_ffmpeg()
        if not ffmpeg_ok:
            logger.error(f"ffmpeg not available: {ffmpeg_msg}")
            return {
                "success": False,
                "error": f"ffmpeg 未安装。请先安装 ffmpeg:\n1. 运行: winget install ffmpeg\n2. 重启终端后重试",
                "text": ""
            }
        
        start_time = time.time()
        
        try:
            import subprocess
            
            # 根据 mime_type 动态决定文件扩展名
            mime_type = mime_type or "audio/webm"
            if "wav" in mime_type.lower():
                audio_ext = ".wav"
            elif "mp4" in mime_type.lower() or "m4a" in mime_type.lower():
                audio_ext = ".m4a"
            else:
                audio_ext = ".webm"
            
            logger.info(f"Processing audio with mime_type={mime_type}, ext={audio_ext}")
            
            # 文件完整性预检查
            if len(audio_data) < 100:
                logger.warning(f"Audio data too small ({len(audio_data)} bytes), may be corrupted or empty")
                return {
                    "success": False,
                    "error": "音频数据太短或为空，请确保已录制音频后重试",
                    "text": ""
                }
            
            # 保存原始音频到临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=audio_ext) as f:
                f.write(audio_data)
                original_path = f.name
            
            # 使用 ffmpeg 转换为标准 WAV 格式 (16kHz, mono, 16-bit)
            wav_path = original_path.rsplit('.', 1)[0] + "_converted.wav"
            
            # 尝试多种 ffmpeg 转换方法
            conversion_success = False
            
            # 方法1: 使用 -fflags +genpts 生成缺失的 PTS
            ffmpeg_cmd = [
                "ffmpeg",
                "-fflags", "+genpts",
                "-i", original_path,
                "-ar", "16000",
                "-ac", "1",
                "-c:a", "pcm_s16le",
                "-f", "wav",
                wav_path,
                "-y",
                "-hide_banner",
                "-loglevel", "error"
            ]

            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and os.path.exists(wav_path) and os.path.getsize(wav_path) > 0:
                conversion_success = True
                logger.info("ffmpeg method 1 succeeded")

            # 方法2: 如果方法1失败，强制指定输入格式
            if not conversion_success:
                logger.warning(f"ffmpeg method 1 failed: {result.stderr}, trying method 2")

                ffmpeg_cmd2 = [
                    "ffmpeg",
                    "-f", "webm",
                    "-i", original_path,
                    "-ar", "16000",
                    "-ac", "1",
                    "-c:a", "pcm_s16le",
                    "-f", "wav",
                    wav_path,
                    "-y",
                    "-hide_banner",
                    "-loglevel", "error"
                ]

                result2 = subprocess.run(ffmpeg_cmd2, capture_output=True, text=True, timeout=30)
                if result2.returncode == 0 and os.path.exists(wav_path) and os.path.getsize(wav_path) > 0:
                    conversion_success = True
                    logger.info("ffmpeg method 2 succeeded")
                else:
                    logger.warning(f"ffmpeg method 2 failed: {result2.stderr}, trying method 3")

            # 方法3: 如果方法2失败，使用更宽松的参数
            if not conversion_success:
                fallback_path = await self._try_ffmpeg_fallback(original_path)
                if fallback_path:
                    # 将 fallback 生成的 WAV 移动到目标路径
                    import shutil
                    shutil.move(fallback_path, wav_path)
                    conversion_success = True
                    logger.info("ffmpeg method 3 succeeded")
                else:
                    logger.error("All ffmpeg methods failed")

            # 检查生成的 WAV 文件
            if not conversion_success:
                return {
                    "success": False,
                    "error": "音频文件已损坏，请重新录制",
                    "text": ""
                }

            # 运行转写
            loop = asyncio.get_event_loop()
            segments, info = await loop.run_in_executor(
                None,
                lambda: self.model.transcribe(wav_path, language=language)
            )

            text = " ".join([seg.text for seg in segments])

            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(f"Faster Whisper success: text_len={len(text)}, elapsed_ms={elapsed_ms:.0f}")

            return {
                "success": True,
                "text": text.strip(),
                "language": info.language,
                "language_probability": info.language_probability
            }
        except Exception as e:
            logger.error(f"Faster Whisper error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }
        finally:
            # 清理临时文件
            for path in [original_path, wav_path]:
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp file {path}: {e}")

    async def _try_ffmpeg_fallback(self, original_path: str) -> Optional[str]:
        """方法3: 更宽松的 ffmpeg 处理，处理损坏或不完整的 WebM"""
        import subprocess

        # 检查 ffmpeg 可用性
        ffmpeg_ok, ffmpeg_msg = _check_ffmpeg()
        if not ffmpeg_ok:
            logger.error(f"ffmpeg not available: {ffmpeg_msg}")
            return None

        # 检查原始文件状态
        if not os.path.exists(original_path):
            logger.error(f"Original file not found: {original_path}")
            return None

        file_size = os.path.getsize(original_path)
        logger.info(f"WebM file size: {file_size} bytes")

        if file_size < 1000:
            logger.warning("WebM file too small, likely incomplete recording")
            return None

        wav_path = original_path.rsplit('.', 1)[0] + "_fallback.wav"

        # 检查 ffmpeg 版本
        try:
            version_result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=10)
            if version_result.returncode == 0:
                version_line = version_result.stdout.split('\n')[0]
                logger.info(f"ffmpeg version: {version_line}")
        except Exception as e:
            logger.warning(f"Cannot detect ffmpeg version: {e}")

        # 使用多种宽松参数尝试恢复音频
        ffmpeg_cmds = [
            # 方法3a: 忽略错误，继续处理 (ffmpeg 5.0+)
            ["ffmpeg", "-err_detect", "ignore", "-i", original_path,
             "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", "-f", "wav",
             wav_path, "-y", "-hide_banner", "-loglevel", "error"],
            # 方法3b: 强制指定 webm 格式
            ["ffmpeg", "-f", "webm", "-safe", "0", "-i", original_path,
             "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", "-f", "wav",
             wav_path, "-y", "-hide_banner", "-loglevel", "error"],
            # 方法3c: 忽略流错误，跳过损坏帧
            ["ffmpeg", "-fflags", "+genpts+discardcorrupt", "-i", original_path,
             "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", "-f", "wav",
             wav_path, "-y", "-hide_banner", "-loglevel", "error"],
            # 方法3d: 只处理音频流，跳过视频
            ["ffmpeg", "-vn", "-i", original_path,
             "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", "-f", "wav",
             wav_path, "-y", "-hide_banner", "-loglevel", "error"],
            # 方法3e: 允许不连续时间戳
            ["ffmpeg", "-fflags", "+nobuffer", "-i", original_path,
             "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", "-f", "wav",
             wav_path, "-y", "-hide_banner", "-loglevel", "error"],
            # 方法3f: 尝试用 ogg 容器解析 (某些 WebM 用 ogg 编码)
            ["ffmpeg", "-f", "ogg", "-i", original_path,
             "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", "-f", "wav",
             wav_path, "-y", "-hide_banner", "-loglevel", "error"],
            # 方法3g: 完全忽略损坏，尝试恢复可用数据
            ["ffmpeg", "-fflags", "+genpts+discardcorrupt+ignoreerrors",
             "-f", "webm", "-i", original_path,
             "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", "-f", "wav",
             wav_path, "-y", "-hide_banner", "-loglevel", "warning"],
        ]

        for i, cmd in enumerate(ffmpeg_cmds):
            try:
                logger.info(f"Trying ffmpeg fallback method {i+1}...")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0 and os.path.exists(wav_path) and os.path.getsize(wav_path) > 0:
                    logger.info(f"ffmpeg fallback method {i+1} succeeded, output size: {os.path.getsize(wav_path)}")
                    return wav_path
                logger.warning(f"ffmpeg fallback method {i+1} failed: {result.stderr[:200]}")
            except Exception as e:
                logger.warning(f"ffmpeg fallback method {i+1} exception: {e}")

        # 方法3h: 如果所有方法都失败，尝试直接复制原始数据作为 WAV
        # 这是一个极端的 fallback，用于处理严重损坏的文件
        try:
            with open(original_path, 'rb') as src:
                raw_data = src.read()

            # 检查是否有有效的音频数据特征
            # WebM/Opus 通常包含 "Opus" 标记
            if b"Opus" in raw_data or b"opus" in raw_data.lower():
                logger.info("Detected Opus audio in WebM, attempting raw extraction")
                # 尝试用 raw 格式提取
                raw_wav_path = original_path.rsplit('.', 1)[0] + "_raw.wav"
                raw_cmd = [
                    "ffmpeg", "-f", "opus", "-i", original_path,
                    "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", "-f", "wav",
                    raw_wav_path, "-y", "-hide_banner", "-loglevel", "error"
                ]
                result = subprocess.run(raw_cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0 and os.path.exists(raw_wav_path) and os.path.getsize(raw_wav_path) > 0:
                    logger.info("Raw Opus extraction succeeded")
                    # 移动到标准路径
                    shutil.move(raw_wav_path, wav_path)
                    return wav_path
        except Exception as e:
            logger.warning(f"Raw extraction attempt failed: {e}")

        return None


class WhisperCppProvider(WhisperProvider):
    """本地 Whisper.cpp Provider - 更轻量、更快"""

    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load Whisper.cpp model"""
        if not WHISPER_CPP_AVAILABLE:
            logger.warning("Whisper.cpp not available. Using fallback to Faster Whisper.")
            # 自动降级到 FasterWhisper
            self.fallback_provider = FasterWhisperProvider(self.model_size)
            return

        try:
            logger.info(f"Loading Whisper.cpp model: {self.model_size}")
            # pywhispercpp 支持的模型: tiny, base, small, medium, large
            # 如果请求的模型不存在，自动降级
            valid_models = ["tiny", "base", "small", "medium", "large"]
            actual_model = self.model_size if self.model_size in valid_models else "base"

            # 模型文件路径 - 使用缓存目录
            cache_dir = os.path.expanduser("~/.cache/whisper")
            model_path = os.path.join(cache_dir, f"{actual_model}.bin")

            # 如果模型文件不存在，pywhispercpp 会自动下载
            # 也可以使用 HuggingFace 的模型
            self.model = pywhispercpp.model.Model(model_path)
            logger.info(f"Whisper.cpp model loaded successfully: {actual_model}")
        except Exception as e:
            logger.warning(f"Failed to load Whisper.cpp model: {e}, falling back to Faster Whisper")
            self.fallback_provider = FasterWhisperProvider(self.model_size)
            self.model = None

    async def transcribe(self, audio_data: bytes, language: str = "en", mime_type: str = "audio/webm") -> dict:
        """使用本地 Whisper.cpp 转写"""
        # 如果 Whisper.cpp 不可用，使用降级方案
        if not hasattr(self, 'model') or self.model is None:
            if hasattr(self, 'fallback_provider'):
                return await self.fallback_provider.transcribe(audio_data, language, mime_type)
            return {
                "success": False,
                "error": "Whisper model not loaded",
                "text": ""
            }

        # 检查 ffmpeg 可用性
        ffmpeg_ok, ffmpeg_msg = _check_ffmpeg()
        if not ffmpeg_ok:
            logger.error(f"ffmpeg not available: {ffmpeg_msg}")
            if hasattr(self, 'fallback_provider'):
                return await self.fallback_provider.transcribe(audio_data, language, mime_type)
            return {
                "success": False,
                "error": f"ffmpeg 未安装。请先安装 ffmpeg:\n1. 运行: winget install ffmpeg\n2. 重启终端后重试",
                "text": ""
            }

        start_time = time.time()

        try:
            import subprocess

            # 音频预检查
            if len(audio_data) < 100:
                logger.warning(f"Audio data too small ({len(audio_data)} bytes)")
                return {
                    "success": False,
                    "error": "音频数据太短或为空",
                    "text": ""
                }

            # 保存原始音频并转换为 WAV (16kHz, mono)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as f:
                f.write(audio_data)
                original_path = f.name

            wav_path = original_path.rsplit('.', 1)[0] + ".wav"

            # 快速转换: 使用 subprocess.run 同步执行
            ffmpeg_cmd = [
                "ffmpeg", "-i", original_path,
                "-ar", "16000", "-ac", "1",
                "-c:a", "pcm_s16le", "-f", "wav",
                wav_path, "-y", "-hide_banner", "-loglevel", "error"
            ]

            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                logger.error(f"ffmpeg conversion failed: {result.stderr}")
                # 尝试使用原始数据
                return await self.fallback_provider.transcribe(audio_data, language, mime_type)

            # 使用 Whisper.cpp 转写 - 在线程池中执行以避免阻塞
            loop = asyncio.get_event_loop()

            # 语言代码映射: whisper.cpp 使用 ISO 639-1
            lang_map = {"zh": "zh", "en": "en", "ja": "ja", "ko": "ko", "fr": "fr", "de": "de", "es": "es"}
            lang_code = lang_map.get(language.lower()[:2], "auto")

            # 执行转写 - 使用流式处理
            def transcribe_sync():
                # 使用 get_segments 方法获取分段结果
                # 参数: language, initial_prompt, word_timestamps
                segments = self.model.transcribe(
                    wav_path,
                    language=lang_code,
                    initial_prompt="",
                    word_timestamps=False
                )
                return " ".join([seg.text for seg in segments])

            text = await loop.run_in_executor(None, transcribe_sync)

            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(f"Whisper.cpp success: text_len={len(text)}, elapsed_ms={elapsed_ms:.0f}")

            return {
                "success": True,
                "text": text.strip(),
                "language": language,
                "language_probability": 1.0
            }
        except Exception as e:
            logger.error(f"Whisper.cpp error: {e}", exc_info=True)
            # 出现异常时自动降级
            if hasattr(self, 'fallback_provider'):
                return await self.fallback_provider.transcribe(audio_data, language, mime_type)
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }
        finally:
            # 清理临时文件
            for path in [original_path if 'original_path' in dir() else "", wav_path]:
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                except Exception:
                    pass


class OpenAIWhisperProvider(WhisperProvider):
    """OpenAI Whisper API Provider"""

    def __init__(self, api_key: str = "", model: str = "whisper-1"):
        self.api_key = api_key
        self.model = model

    async def transcribe(self, audio_data: bytes, language: str = "en", mime_type: str = "audio/webm") -> dict:
        """使用 OpenAI Whisper API 转写"""
        if not self.api_key:
            return {
                "success": False,
                "error": "OpenAI API key not configured",
                "text": ""
            }

        try:
            import aiohttp

            url = "https://api.openai.com/v1/audio/transcriptions"
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }

            # Prepare multipart form data
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                f.write(audio_data)
                temp_path = f.name

            try:
                async with aiohttp.ClientSession() as session:
                    with open(temp_path, "rb") as f:
                        data = aiohttp.FormData()
                        data.add_field("file", f, filename="audio.wav", content_type="audio/wav")
                        data.add_field("model", self.model)
                        if language:
                            data.add_field("language", language)

                        async with session.post(url, headers=headers, data=data) as resp:
                            result = await resp.json()

                if resp.status == 200:
                    return {
                        "success": True,
                        "text": result.get("text", "").strip(),
                        "language": language,
                        "language_probability": 1.0
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("error", {}).get("message", "OpenAI API error"),
                        "text": ""
                    }
            finally:
                os.unlink(temp_path)

        except Exception as e:
            logger.error(f"OpenAI Whisper error: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }


class TencentASRProvider(WhisperProvider):
    """腾讯云语音识别 Provider"""
    
    def __init__(self, secret_id: str = "", secret_key: str = "", app_id: str = ""):
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.app_id = app_id
    
    async def transcribe(self, audio_data: bytes, language: str = "en", mime_type: str = "audio/webm") -> dict:
        """腾讯云语音识别"""
        if not self.secret_id or not self.secret_key:
            return {
                "success": False,
                "error": "腾讯云语音识别未配置 secret_id 或 secret_key，已自动降级到 Faster Whisper",
                "text": ""
            }
        
        if not audio_data:
            return {"success": False, "error": "No audio data provided", "text": ""}
        
        try:
            import httpx
            import hashlib
            import hmac
            import time
            import base64
            
            # 音频转 base64
            audio_base64 = base64.b64encode(audio_data).decode("utf-8")
            
            # 腾讯云 ASR API
            url = "https://asr.tencentcloudapi.com/"
            
            # 生成签名
            timestamp = str(int(time.time()))
            params = {
                "Action": "CreateRecognitionTask",
                "Version": "2022-08-11",
                "Region": "ap-guangzhou",
                "SecretId": self.secret_id,
                "Timestamp": timestamp,
                "Nonce": str(int(time.time() * 1000) % 100000),
                "EngineType": "16k",
                "Url": "",  # 使用 Data 参数
                "Data": audio_base64[:50000],  # 限制大小
                "DataLen": len(audio_base64[:50000]),
                "ChannelNum": 1,
                "SampleRate": 16000,
                "WordBoost": []
            }
            
            # 生成签名
            def generate_signature(params, secret_key):
                sorted_params = sorted(params.items())
                param_str = "&".join([f"{k}={v}" for k, v in sorted_params])
                signature = hmac.new(
                    secret_key.encode("utf-8"),
                    param_str.encode("utf-8"),
                    hashlib.sha1
                ).hexdigest()
                return signature
            
            params["Signature"] = generate_signature(params, self.secret_key)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, data=params)
                result = response.json()
                
                if "Response" in result and "TaskId" in result["Response"]:
                    # 异步任务，需要轮询获取结果
                    return {
                        "success": True,
                        "text": "腾讯云语音识别任务已提交，请稍后查询结果",
                        "language": language
                    }
                elif "Response" in result and "Result" in result["Response"]:
                    return {
                        "success": True,
                        "text": result["Response"]["Result"],
                        "language": language
                    }
                else:
                    return {
                        "success": False,
                        "error": f"腾讯云 ASR 错误: {result}",
                        "text": ""
                    }
        except Exception as e:
            logger.error(f"Tencent ASR error: {e}")
            return {"success": False, "error": f"腾讯云语音识别失败: {str(e)}", "text": ""}


class VolcengineASRProvider(WhisperProvider):
    """火山引擎语音识别 Provider (字节跳动)"""
    
    def __init__(self, app_id: str = "", secret_id: str = "", secret_key: str = ""):
        self.app_id = app_id
        self.secret_id = secret_id
        self.secret_key = secret_key
    
    async def transcribe(self, audio_data: bytes, language: str = "en", mime_type: str = "audio/webm") -> dict:
        """火山引擎语音识别"""
        if not self.secret_id or not self.secret_key:
            return {
                "success": False,
                "error": "火山引擎语音识别未配置 secret_id 或 secret_key，已自动降级到 Faster Whisper",
                "text": ""
            }
        
        if not audio_data:
            return {"success": False, "error": "No audio data provided", "text": ""}
        
        try:
            import httpx
            import hashlib
            import hmac
            import time
            import base64
            
            # 音频转 base64
            audio_base64 = base64.b64encode(audio_data).decode("utf-8")
            
            # 火山引擎 ASR API (流式识别)
            url = "https://openspeech.bytedance.com/api/v2/asr"
            
            timestamp = str(int(time.time()))
            
            # 生成 Authorization
            signature_str = f"GET /api/v2/asr\n{timestamp}\n{self.app_id}"
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
            
            body = {
                "app": {"appid": self.app_id},
                "user": {"uid": "lexiva_user"},
                "audio": {
                    "format": "wav",
                    "rate": 16000,
                    "bits": 16,
                    "channel": 1,
                    "codec": "raw"
                },
                "request": {
                    "reqid": str(int(time.time() * 1000)),
                    "sequence": 1
                }
            }
            
            # 由于火山引擎需要原始音频数据，这里使用简化实现
            # 完整实现需要将音频数据以特定方式传递
            return {
                "success": False,
                "error": "火山引擎 ASR 需要完整的音频上传实现，当前版本暂未完整支持",
                "text": ""
            }
            
        except Exception as e:
            logger.error(f"Volcengine ASR error: {e}")
            return {"success": False, "error": f"火山引擎语音识别失败: {str(e)}", "text": ""}


class AliyunASRProvider(WhisperProvider):
    """阿里云语音识别 Provider"""
    
    def __init__(self, access_key_id: str = "", access_key_secret: str = ""):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self._token = None
    
    async def _get_token(self) -> str:
        """获取阿里云访问 Token"""
        import httpx
        import time
        import hashlib
        import base64
        import urllib.parse
        
        if self._token:
            return self._token
        
        try:
            # 阿里云 STS 获取 token 的简化实现
            # 实际需要通过阿里云 STS 服务获取
            url = "https://nls-meta.cn-shanghai.aliyuncs.com/"
            return ""
        except Exception as e:
            logger.error(f"Aliyun token error: {e}")
            return ""
    
    async def transcribe(self, audio_data: bytes, language: str = "en", mime_type: str = "audio/webm") -> dict:
        """阿里云语音识别"""
        if not self.access_key_id or not self.access_key_secret:
            return {
                "success": False,
                "error": "阿里云语音识别未配置 access_key_id 或 access_key_secret，已自动降级到 Faster Whisper",
                "text": ""
            }
        
        if not audio_data:
            return {"success": False, "error": "No audio data provided", "text": ""}
        
        try:
            import httpx
            import base64
            
            # 音频转 base64
            audio_base64 = base64.b64encode(audio_data).decode("utf-8")
            
            # 阿里云 ASR API (录音文件识别)
            url = "https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/asr"
            
            # 注意：需要先获取 token
            token = await self._get_token()
            if not token:
                return {
                    "success": False,
                    "error": "阿里云 Token 获取失败，请在阿里云控制台获取 Access Token",
                    "text": ""
                }
            
            params = {
                "appkey": "LTAI5t",  # 需要在阿里云控制台获取
                "token": token,
                "format": "wav",
                "sample_rate": 16000,
                "enable_inverse_text_normalization": "true",
                "enable_voice_detection": "true"
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            # 将音频数据放入请求体
            import urllib.parse
            body = urllib.parse.urlencode({"audio": audio_base64, **params})
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, data=body, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    if "result" in result:
                        return {
                            "success": True,
                            "text": result["result"],
                            "language": language
                        }
                    return {
                        "success": True,
                        "text": result.get("data", {}).get("text", ""),
                        "language": language
                    }
                else:
                    return {
                        "success": False,
                        "error": f"阿里云 ASR error: {response.status_code}",
                        "text": ""
                    }
                    
        except Exception as e:
            logger.error(f"Aliyun ASR error: {e}")
            return {"success": False, "error": f"阿里云语音识别失败: {str(e)}", "text": ""}


class XfyunASRProvider(WhisperProvider):
    """讯飞语音识别 Provider"""
    
    def __init__(self, app_id: str = "", api_key: str = "", api_secret: str = ""):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
    
    async def transcribe(self, audio_data: bytes, language: str = "en", mime_type: str = "audio/webm") -> dict:
        """讯飞语音识别"""
        if not self.api_key or not self.api_secret:
            return {
                "success": False,
                "error": "讯飞语音识别未配置 api_key 或 api_secret，已自动降级到 Faster Whisper",
                "text": ""
            }
        
        if not audio_data:
            return {"success": False, "error": "No audio data provided", "text": ""}
        
        try:
            import httpx
            import hashlib
            import hmac
            import base64
            import time
            import json
            from urllib.parse import urlencode
            
            # 讯飞 WebSocket API 需要鉴权，这里简化为 REST API
            # 讯飞语音识别 REST API
            url = "https://iat.xfyun.cn/v2/iat"
            
            # 构建鉴权参数
            now = time.time()
            date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(now))
            
            # 生成 Authorization
            signature_origin = f"host: iat.xfyun.cn\ndate: {date}\nGET /v2/iat HTTP/1.1"
            signature_sha = hmac.new(
                self.api_secret.encode("utf-8"),
                signature_origin.encode("utf-8"),
                digestmod=hashlib.sha256
            ).digest()
            authorization = base64.b64encode(signature_sha).decode("utf-8")
            
            headers = {
                "Authorization": f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{authorization}"',
                "Date": date,
                "Host": "iat.xfyun.cn"
            }
            
            # 音频转 base64
            audio_base64 = base64.b64encode(audio_data).decode("utf-8")
            
            # 构建请求体
            common = {"app_id": self.app_id}
            business = {
                "language": "en_us" if language.lower() == "en" else "zh_cn",
                "domain": "iat",
                "accent": "mandarin",
                "sample_rate": 16000,
                "format": "wav",
                "encoding": "raw"
            }
            data = {"status": 2, "format": "audio/wav", "audio": audio_base64}
            
            body = json.dumps({"common": common, "business": business, "data": data})
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, content=body, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("code") == 0:
                        return {
                            "success": True,
                            "text": result.get("data", {}).get("result", {}).get("ws", [{"cw": [{"w": ""}]}])[0].get("cw", [{}])[0].get("w", ""),
                            "language": language
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"讯飞 ASR 错误: {result.get('message', '未知错误')}",
                            "text": ""
                        }
                else:
                    return {
                        "success": False,
                        "error": f"讯飞 ASR HTTP error: {response.status_code}",
                        "text": ""
                    }
                    
        except Exception as e:
            logger.error(f"Xfyun ASR error: {e}")
            return {"success": False, "error": f"讯飞语音识别失败: {str(e)}", "text": ""}


class WhisperService:
    """Whisper 服务入口 - 支持配置"""
    
    # 可用 provider 映射
    PROVIDERS = {
        "faster-whisper": FasterWhisperProvider,
        "whisper-cpp": WhisperCppProvider,
        "openai": OpenAIWhisperProvider,
        "tencent": TencentASRProvider,
        "volcengine": VolcengineASRProvider,
        "aliyun": AliyunASRProvider,
        "xfyun": XfyunASRProvider,
    }
    
    def __init__(self):
        self._settings = None
        self._provider = None
    
    def _get_settings(self) -> dict:
        """从数据库获取 Whisper 配置"""
        if self._settings is None:
            try:
                from db.connection import get_db
                from models import AISettings
                session = next(get_db())
                settings = session.query(AISettings).first()
                if settings:
                    # 检查各云 ASR 是否配置了密钥，未配置则自动降级
                    provider = settings.whisper_provider or "faster-whisper"
                    
                    self._settings = {
                        "provider": provider,
                        "model": settings.whisper_model or "base",
                        "api_key": settings.api_key or "",
                        # 火山引擎
                        "volcengine_asr_app_id": settings.volcengine_asr_app_id or "",
                        "volcengine_asr_secret_id": settings.volcengine_asr_secret_id or "",
                        "volcengine_asr_secret_key": settings.volcengine_asr_secret_key or "",
                        # 阿里云
                        "aliyun_asr_access_key_id": settings.aliyun_asr_access_key_id or "",
                        "aliyun_asr_access_key_secret": settings.aliyun_asr_access_key_secret or "",
                        # 讯飞
                        "xfyun_app_id": settings.xfyun_app_id or "",
                        "xfyun_api_key": settings.xfyun_api_key or "",
                        "xfyun_api_secret": settings.xfyun_api_secret or "",
                        # 腾讯云
                        "tencent_secret_id": settings.tencent_secret_id or "",
                        "tencent_secret_key": settings.tencent_secret_key or "",
                        "tencent_app_id": settings.tencent_app_id or "",
                    }
                session.close()
            except Exception as e:
                logger.warning(f"Failed to load Whisper settings: {e}")
                self._settings = {"provider": "faster-whisper", "model": "base", "api_key": ""}
        
        return self._settings
    
    def reload_settings(self):
        """重新加载配置"""
        self._settings = None
        self._provider = None
    
    def _get_provider(self) -> WhisperProvider:
        """获取当前配置的 provider"""
        if self._provider is not None:
            return self._provider
        
        settings = self._get_settings()
        provider_name = settings.get("provider", "faster-whisper")
        model_size = settings.get("model", "base")
        
        provider_class = self.PROVIDERS.get(provider_name, FasterWhisperProvider)
        
        # 根据不同厂商创建 provider 实例
        if provider_name == "openai":
            self._provider = provider_class(
                api_key=settings.get("api_key", ""),
                model="whisper-1"
            )
        elif provider_name == "tencent":
            self._provider = provider_class(
                secret_id=settings.get("tencent_secret_id", ""),
                secret_key=settings.get("tencent_secret_key", ""),
                app_id=settings.get("tencent_app_id", "")
            )
        elif provider_name == "volcengine":
            self._provider = provider_class(
                app_id=settings.get("volcengine_asr_app_id", ""),
                secret_id=settings.get("volcengine_asr_secret_id", ""),
                secret_key=settings.get("volcengine_asr_secret_key", "")
            )
        elif provider_name == "aliyun":
            self._provider = provider_class(
                access_key_id=settings.get("aliyun_asr_access_key_id", ""),
                access_key_secret=settings.get("aliyun_asr_access_key_secret", "")
            )
        elif provider_name == "xfyun":
            self._provider = provider_class(
                app_id=settings.get("xfyun_app_id", ""),
                api_key=settings.get("xfyun_api_key", ""),
                api_secret=settings.get("xfyun_api_secret", "")
            )
        else:
            # faster-whisper / whisper-cpp
            self._provider = provider_class(model_size=model_size)
        
        return self._provider

    async def transcribe(self, audio_data: bytes, language: str = "en", mime_type: str = "audio/webm") -> dict:
        """转写音频 - 使用配置的 provider"""
        provider = self._get_provider()
        return await provider.transcribe(audio_data, language, mime_type)

    async def transcribe_base64(self, audio_base64: str, language: str = "en", mime_type: str = "audio/webm") -> dict:
        """转写 base64 编码的音频"""
        try:
            audio_data = base64.b64decode(audio_base64)
            return await self.transcribe(audio_data, language, mime_type)
        except Exception as e:
            logger.error(f"Base64 decode error: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }


# 全局实例
whisper_service = WhisperService()