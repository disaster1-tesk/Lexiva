"""
Writing Correction Service
AI-powered writing correction
"""
import os
import httpx
from typing import Optional
from db.connection import get_db
from models import AISettings


class WritingService:
    """Service for AI-powered writing correction"""
    
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
    
    def _get_api_key(self, settings: AISettings) -> str:
        """Get API key from settings or environment"""
        if settings.api_key:
            return settings.api_key
        provider_config = self.PROVIDERS.get(settings.provider, self.PROVIDERS["deepseek"])
        return os.getenv(provider_config["env_key"], "")
    
    def _get_base_url(self, settings: AISettings) -> str:
        """Get base URL for provider"""
        if settings.provider == "ollama" and settings.base_url:
            return settings.base_url
        return self.PROVIDERS[settings.provider]["base_url"]
    
    async def correct(self, text: str, exam_type: str = "general") -> dict:
        """
        Correct and improve writing
        
        Args:
            text: Text to correct
            exam_type: Exam type (general, CET-4, CET-6, IELTS, TOEFL)
        
        Returns:
            dict with corrections and score
        """
        settings = self._get_settings()
        provider = settings.provider
        model = settings.model
        temperature = settings.temperature
        max_tokens = settings.max_tokens
        
        api_key = self._get_api_key(settings)
        base_url = self._get_base_url(settings)
        
        if not api_key:
            return {
                "original_text": text,
                "corrected_text": text,
                "corrections": [],
                "score": {"grammar": 0, "vocabulary": 0, "fluency": 0, "overall": 0},
                "error": "API Key 未配置，请在设置页面配置 AI 模型。"
            }
        
        prompt = self._build_prompt(text, exam_type)
        
        messages = [
            {"role": "system", "content": "You are an English writing teacher. Correct the student's writing, explain errors, and provide improvement suggestions."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    base_url,
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    },
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                content = result["choices"][0]["message"]["content"]
                return self._parse_correction(text, content)
        except Exception as e:
            return {
                "original_text": text,
                "corrected_text": text,
                "corrections": [],
                "score": {"grammar": 0, "vocabulary": 0, "fluency": 0, "overall": 0},
                "error": str(e)
            }
    
    def _build_prompt(self, text: str, exam_type: str) -> str:
        """Build correction prompt"""
        prompts = {
            "general": f"Please correct and improve this English text:\n\n{text}\n\nProvide:\n1. Corrected version\n2. Grammar corrections\n3. Vocabulary improvements\n4. Scores (grammar, vocabulary, fluency out of 100)",
            "CET-4": f"Please correct this English text for CET-4 level:\n\n{text}\n\nProvide:\n1. Corrected version\n2. Errors with explanations\n3. Better vocabulary choices\n4. Scores",
            "CET-6": f"Please correct this English text for CET-6 level:\n\n{text}\n\nProvide:\n1. Corrected version\n2. Sophisticated corrections\n3. Advanced vocabulary\n4. Scores",
            "IELTS": f"Please correct this English text for IELTS Writing:\n\n{text}\n\nProvide:\n1. Corrected version\n2. Coherence and cohesion suggestions\n3. Lexical resource improvements\n4. Band score estimation",
            "TOEFL": f"Please correct this English text for TOEFL iBT:\n\n{text}\n\nProvide:\n1. Corrected version\n2. Development and organization\n3. Language use\n4. Score"
        }
        return prompts.get(exam_type, prompts["general"])
    
    def _parse_correction(self, original: str, content: str) -> dict:
        """Parse AI response into structured correction"""
        corrections = []
        
        # Simple correction parsing
        lines = content.split('\n')
        corrected_text = original
        
        # Try to extract corrected version
        for i, line in enumerate(lines):
            if line.lower().startswith('corrected') or line.lower().startswith('1.'):
                if i + 1 < len(lines):
                    corrected_text = lines[i + 1].strip()
                    break
        
        # Score estimation based on content
        score_grammar = 70
        score_vocabulary = 70
        score_fluency = 70
        
        if "good" in content.lower() or "excellent" in content.lower():
            score_grammar = min(95, score_grammar + 10)
            score_vocabulary = min(95, score_vocabulary + 10)
        
        if "error" in content.lower():
            corrections.append({
                "type": "general",
                "position": 0,
                "wrong": "See above",
                "correct": "AI analysis needed",
                "explanation": "Errors found in text. Check corrected version."
            })
        
        overall = (score_grammar + score_vocabulary + score_fluency) // 3
        
        return {
            "original_text": original,
            "corrected_text": corrected_text,
            "corrections": corrections,
            "score": {
                "grammar": score_grammar,
                "vocabulary": score_vocabulary,
                "fluency": score_fluency,
                "overall": overall
            }
        }


# Singleton instance
writing_service = WritingService()