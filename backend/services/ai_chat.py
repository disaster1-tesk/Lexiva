"""
AI Chat Service
Supports multiple AI providers: DeepSeek, OpenAI, Ollama
"""
import os
import httpx
import logging
import time
import json
import asyncio
from typing import Optional
from db.connection import get_db
from models import AISettings

logger = logging.getLogger(__name__)


class AIChatService:
    """Service for AI-powered chat functionality with multiple providers"""
    
    # Provider configurations
    PROVIDERS = {
        "deepseek": {
            "base_url": "https://api.deepseek.com/v1/chat/completions",
            "default_model": "deepseek-chat",
            "env_key": "DEEPSEEK_API_KEY",
            "auth_type": "bearer"  # OpenAI compatible
        },
        "openai": {
            "base_url": "https://api.openai.com/v1/chat/completions",
            "default_model": "gpt-4o-mini",
            "env_key": "OPENAI_API_KEY",
            "auth_type": "bearer"
        },
        "ollama": {
            "base_url": "http://localhost:11434/v1/chat/completions",
            "default_model": "llama3",
            "env_key": "OLLAMA_API_KEY",
            "auth_type": "bearer",
            "is_local": True
        },
        # 通义千问 (阿里云)
        "qwen": {
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            "default_model": "qwen-turbo",
            "env_key": "QWEN_API_KEY",
            "auth_type": "bearer"
        },
        # 智谱清言 (ChatGLM)
        "zhipu": {
            "base_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
            "default_model": "glm-4-flash",
            "env_key": "ZHIPU_API_KEY",
            "auth_type": "bearer"
        },
        # Claude (Anthropic)
        "anthropic": {
            "base_url": "https://api.anthropic.com/v1/messages",
            "default_model": "claude-3-5-sonnet-20241022",
            "env_key": "ANTHROPIC_API_KEY",
            "auth_type": "anthropic"  # Special header format
        },
        # Gemini (Google)
        "google": {
            "base_url": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            "default_model": "gemini-1.5-flash",
            "env_key": "GOOGLE_API_KEY",
            "auth_type": "google"  # URL parameter format
        }
    }
    
    def __init__(self):
        self.conversation_history: list[dict] = []
        self._settings_cache = None
    
    def _get_settings(self) -> AISettings:
        """Get AI settings from database"""
        if self._settings_cache is not None:
            return self._settings_cache
        
        session = next(get_db())
        try:
            settings = session.query(AISettings).first()
            if not settings:
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
            self._settings_cache = settings
            return settings
        finally:
            session.close()

    def reload_settings(self):
        """Clear settings cache to force reload from database"""
        self._settings_cache = None
    
    def _get_provider_config(self, provider: str) -> dict:
        """Get provider configuration"""
        return self.PROVIDERS.get(provider, self.PROVIDERS["deepseek"])
    
    def _get_api_key(self, settings: AISettings) -> str:
        """Get API key from settings or environment"""
        # First try settings
        if settings.api_key:
            return settings.api_key
        # Fall back to environment
        provider_config = self._get_provider_config(settings.provider)
        return os.getenv(provider_config["env_key"], "")
    
    def _get_base_url(self, settings: AISettings) -> str:
        """Get base URL for provider"""
        if settings.provider == "ollama" and settings.base_url:
            return settings.base_url
        return self.PROVIDERS[settings.provider]["base_url"]
    
    def _is_local_url(self, url: str) -> bool:
        """检测 URL 是否为本地地址"""
        if not url:
            return False
        local_patterns = ["localhost", "127.0.0.1", "0.0.0.0", "[::1]"]
        url_lower = url.lower()
        return any(pattern in url_lower for pattern in local_patterns)
    
    async def chat(self, message: str, scene: str = "daily") -> dict:
        """
        Send message to AI and get response
        
        Args:
            message: User's message
            scene: Conversation scene (daily, exam, campus, business)
        
        Returns:
            dict with 'reply' and optional 'corrections'
        """
        logger.info(f"Chat request: scene={scene}, message_len={len(message)}")
        
        settings = self._get_settings()
        provider = settings.provider
        model = settings.model
        temperature = settings.temperature
        max_tokens = settings.max_tokens
        top_p = settings.top_p
        
        api_key = self._get_api_key(settings)
        provider_config = self._get_provider_config(provider)
        base_url = self._get_base_url(settings)
        auth_type = provider_config.get("auth_type", "bearer")
        
        # Ollama 本地模型（localhost/127.0.0.1）不需要 API Key
        is_local_ollama = settings.provider == "ollama" and self._is_local_url(base_url)
        if not api_key and not is_local_ollama:
            if settings.provider == "ollama":
                logger.warning("Ollama remote API requires API Key")
                return {
                    "reply": "Ollama 远程 API 需要配置 API Key，请前往设置页面配置。",
                    "corrections": []
                }
            logger.warning("API Key not configured")
            return {
                "reply": "API Key 未配置，请在设置页面配置 AI 模型。",
                "corrections": []
            }
        
        system_prompt = self._get_scene_prompt(scene)
        
        messages = [
            {"role": "system", "content": system_prompt},
            *self.conversation_history[-5:],
            {"role": "user", "content": message}
        ]
        
        try:
            request_params = {
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": top_p,
                "messages_count": len(messages)
            }
            logger.info(f"Calling AI API: provider={provider}, model={model}, params={request_params}")
            
            start_time = time.time()
            
            # 根据认证类型构建请求
            headers, request_url, request_body = self._build_request(
                provider=provider,
                auth_type=auth_type,
                base_url=base_url,
                api_key=api_key,
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p
            )
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    request_url,
                    json=request_body,
                    headers=headers
                )
                response.raise_for_status()
                result = response.json()
            
            # 根据响应格式解析回复
            reply = self._parse_response(provider, result)
            
            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(f"AI response received: provider={provider}, status={response.status_code}, elapsed_ms={elapsed_ms:.0f}, reply_len={len(reply)}")
            
            # Parse corrections if any
            corrections = self._parse_corrections(message, reply)
            
            # Save to history
            self.conversation_history.extend([
                {"role": "user", "content": message},
                {"role": "assistant", "content": reply}
            ])
            
            return {
                "reply": reply,
                "corrections": corrections
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"AI API HTTP error: {e.response.status_code}", exc_info=True)
            return {
                "reply": f"API 请求失败 ({e.response.status_code})，请检查 API Key 和网络配置。",
                "corrections": []
            }
        except Exception as e:
            logger.error(f"AI API error: {e}", exc_info=True)
            return {
                "reply": f"发生了错误: {str(e)}，请重试。",
                "corrections": []
            }
    
    def _build_request(self, provider: str, auth_type: str, base_url: str, api_key: str,
                       model: str, messages: list, temperature: float, max_tokens: int, top_p: float) -> tuple:
        """根据不同厂商构建请求头、URL 和请求体"""
        headers = {"Content-Type": "application/json"}
        request_body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p
        }
        
        if auth_type == "bearer":
            # OpenAI 兼容格式
            headers["Authorization"] = f"Bearer {api_key}"
            request_url = base_url
            
        elif auth_type == "anthropic":
            # Anthropic Claude 格式
            headers["x-api-key"] = api_key
            headers["anthropic-version"] = "2023-06-01"
            request_url = base_url
            # 转换消息格式
            request_body = {
                "model": model,
                "max_tokens": max_tokens,
                "system": messages[0]["content"] if messages[0]["role"] == "system" else "",
                "messages": [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"]
            }
            
        elif auth_type == "google":
            # Google Gemini 格式
            request_url = base_url.replace("{model}", model)
            request_url += f"?key={api_key}"
            # 转换为 Gemini 格式
            contents = []
            for m in messages:
                if m["role"] == "system":
                    continue
                role = "user" if m["role"] == "user" else "model"
                contents.append({"role": role, "parts": [{"text": m["content"]}]})
            request_body = {"contents": contents}
            if messages[0].get("role") == "system":
                request_body["systemInstruction"] = {"parts": [{"text": messages[0]["content"]}]}
            # Gemini 不支持 top_p
            del request_body["top_p"]
            
        else:
            # 默认 OpenAI 格式
            headers["Authorization"] = f"Bearer {api_key}"
            request_url = base_url
        
        return headers, request_url, request_body
    
    def _parse_response(self, provider: str, result: dict) -> str:
        """根据不同厂商解析响应"""
        # 标准 OpenAI 格式
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        
        # Anthropic 格式
        if "content" in result and len(result["content"]) > 0:
            return result["content"][0].get("text", "")
        
        # Google Gemini 格式
        if "candidates" in result and len(result["candidates"]) > 0:
            return result["candidates"][0]["content"]["parts"][0].get("text", "")
        
        # 备用：返回 JSON 字符串
        return str(result)
    
    def _get_scene_prompt(self, scene: str) -> str:
        """Get system prompt based on scene"""
        prompts = {
            "daily": "You are a friendly English conversation partner. Help the user practice everyday English. Keep responses natural and conversational. If the user makes grammar or vocabulary mistakes, gently correct them.",
            "exam": "You are an English exam preparation tutor. Help the user practice test-taking English. Provide formal and accurate responses. Include exam-style vocabulary and structures.",
            "campus": "You are a campus English guide. Help the user practice English for school life, including talking to professors, making friends, and participating in activities.",
            "business": "You are a business English coach. Help the user practice professional English for workplace communication, meetings, and presentations."
        }
        return prompts.get(scene, prompts["daily"])
    
    def _parse_corrections(self, user_message: str, ai_response: str) -> list:
        """Parse corrections from conversation"""
        corrections = []
        
        # Simple grammar check patterns
        common_mistakes = [
            ("i ", "I "),
            ("dont ", "don't "),
            ("cant ", "can't "),
            ("isnt ", "isn't "),
            ("arent ", "aren't "),
            ("wasnt ", "wasn't "),
            ("werent ", "weren't "),
            ("hasnt ", "hasn't "),
            ("havent ", "haven't "),
            ("didnt ", "didn't "),
            ("wont ", "won't "),
            ("couldnt ", "couldn't "),
            ("wouldnt ", "wouldn't "),
            ("shouldnt ", "shouldn't "),
            ("thats ", "that's "),
            ("hes ", "he's "),
            ("shes ", "she's "),
            ("its ", "it's "),
            ("youre ", "you're "),
            ("were ", "we're "),
            ("theyre ", "they're "),
            ("ive ", "I've "),
            ("youve ", "you've "),
            ("weve ", "we've "),
            ("theyve ", "they've "),
            ("ill ", "I'll "),
            ("youll ", "you'll "),
            ("well ", "we'll "),
            ("theyll ", "they'll "),
            ("theres ", "there's "),
            ("heres ", "here's "),
            ("wheres ", "where's "),
            ("whos ", "who's ")
        ]
        
        lower_message = user_message.lower()
        for wrong, correct in common_mistakes:
            if wrong in lower_message:
                idx = lower_message.find(wrong)
                corrections.append({
                    "type": "capitalization",
                    "wrong": wrong.strip(),
                    "correct": correct.strip(),
                    "position": idx,
                    "explanation": f"Always capitalize '{correct.strip()}' at the beginning of a sentence."
                })
        
        return corrections
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def reload_settings(self):
        """Clear settings cache to force reload"""
        self._settings_cache = None

    async def stream_chat(self, message: str, scene: str = "daily"):
        """
        Send message to AI and yield response as streaming

        Yields:
            dict with 'chunk' (text chunk), 'done' (boolean), 'reply' (full reply when done)
        """
        logger.info(f"Stream chat request: scene={scene}, message_len={len(message)}")

        settings = self._get_settings()
        provider = settings.provider
        model = settings.model
        temperature = settings.temperature
        max_tokens = settings.max_tokens
        top_p = settings.top_p

        api_key = self._get_api_key(settings)
        provider_config = self._get_provider_config(provider)
        base_url = self._get_base_url(settings)
        auth_type = provider_config.get("auth_type", "bearer")

        # Ollama 本地模型不需要 API Key
        is_local_ollama = settings.provider == "ollama" and self._is_local_url(base_url)
        if not api_key and not is_local_ollama:
            if settings.provider == "ollama":
                yield {"chunk": "Ollama 远程 API 需要配置 API Key，请前往设置页面配置。", "done": True, "reply": "Ollama 远程 API 需要配置 API Key，请前往设置页面配置。"}
            else:
                yield {"chunk": "API Key 未配置，请在设置页面配置 AI 模型。", "done": True, "reply": "API Key 未配置，请在设置页面配置 AI 模型。"}
            return

        system_prompt = self._get_scene_prompt(scene)

        messages = [
            {"role": "system", "content": system_prompt},
            *self.conversation_history[-5:],
            {"role": "user", "content": message}
        ]

        try:
            # 根据认证类型构建请求
            headers, request_url, request_body = self._build_request(
                provider=provider,
                auth_type=auth_type,
                base_url=base_url,
                api_key=api_key,
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p
            )

            # 添加 streaming 参数
            if provider == "anthropic":
                request_body["stream"] = True
            else:
                request_body["stream"] = True

            full_reply = ""
            async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                async with client.stream("POST", request_url, json=request_body, headers=headers) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        if line.startswith("data: "):
                            data = line[6:]
                        else:
                            continue

                        if data == "[DONE]":
                            # 完成
                            self.conversation_history.extend([
                                {"role": "user", "content": message},
                                {"role": "assistant", "content": full_reply}
                            ])
                            # 解析语法纠错
                            corrections = self._parse_corrections(message, full_reply)
                            yield {"chunk": "", "done": True, "reply": full_reply, "corrections": corrections}
                            return

                        try:
                            chunk_data = json.loads(data)
                        except json.JSONDecodeError:
                            continue

                        # 根据不同厂商解析流式响应
                        chunk_content = self._parse_stream_chunk(provider, chunk_data)
                        if chunk_content:
                            full_reply += chunk_content
                            yield {"chunk": chunk_content, "done": False, "reply": ""}

                    # 如果没有流式响应，返回完整响应
                    if full_reply:
                        self.conversation_history.extend([
                            {"role": "user", "content": message},
                            {"role": "assistant", "content": full_reply}
                        ])
                        corrections = self._parse_corrections(message, full_reply)
                        yield {"chunk": "", "done": True, "reply": full_reply, "corrections": corrections}
                    else:
                        # 尝试非流式请求作为后备
                        logger.info("Stream failed, falling back to non-stream request")
                        request_body.pop("stream", None)
                        async with httpx.AsyncClient(timeout=60.0) as client:
                            response = await client.post(request_url, json=request_body, headers=headers)
                            result = response.json()
                            full_reply = self._parse_response(provider, result)
                            self.conversation_history.extend([
                                {"role": "user", "content": message},
                                {"role": "assistant", "content": full_reply}
                            ])
                            corrections = self._parse_corrections(message, full_reply)
                            yield {"chunk": full_reply, "done": True, "reply": full_reply, "corrections": corrections}

        except httpx.HTTPStatusError as e:
            logger.error(f"AI API HTTP error: {e.response.status_code}", exc_info=True)
            yield {"chunk": f"API 请求失败 ({e.response.status_code})，请检查 API Key 和网络配置。", "done": True, "reply": f"API 请求失败 ({e.response.status_code})，请检查 API Key 和网络配置。", "corrections": []}
        except Exception as e:
            logger.error(f"AI API error: {e}", exc_info=True)
            yield {"chunk": f"发生了错误: {str(e)}，请重试。", "done": True, "reply": f"发生了错误: {str(e)}，请重试。", "corrections": []}

    def _parse_stream_chunk(self, provider: str, chunk: dict) -> str:
        """Parse streaming chunk from different providers"""
        # OpenAI / DeepSeek 格式
        if "choices" in chunk and len(chunk["choices"]) > 0:
            delta = chunk["choices"][0].get("delta", {})
            return delta.get("content", "")

        # Anthropic 格式
        if "type" in chunk:
            if chunk["type"] == "content_block_delta":
                return chunk.get("delta", {}).get("text", "")
            elif chunk["type"] == "message_delta":
                return chunk.get("text", "")

        return ""


# Singleton instance
chat_service = AIChatService()