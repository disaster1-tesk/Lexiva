"""
AI Chat Service
Supports multiple AI providers: DeepSeek, OpenAI, Ollama
"""
import os
import httpx
import logging
import time
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
            "env_key": "DEEPSEEK_API_KEY"
        },
        "openai": {
            "base_url": "https://api.openai.com/v1/chat/completions",
            "default_model": "gpt-4o-mini",
            "env_key": "OPENAI_API_KEY"
        },
        "ollama": {
            "base_url": "http://localhost:11434/v1/chat/completions",
            "default_model": "llama3",
            "env_key": "OLLAMA_API_KEY"
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
        base_url = self._get_base_url(settings)
        
        if not api_key:
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
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    base_url,
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "top_p": top_p
                    },
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                reply = result["choices"][0]["message"]["content"]
                
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


# Singleton instance
chat_service = AIChatService()