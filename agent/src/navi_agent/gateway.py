import os
from typing import List, Dict, Optional
from openai import OpenAI
import structlog

logger = structlog.get_logger()

class LLMGateway:
    def __init__(self):
        self.primary_base = os.getenv("NAVI_PRIMARY_BASE", "http://localhost:11434/v1")
        self.primary_model = os.getenv("NAVI_PRIMARY_MODEL", "llama3.1")
        self.fallback_base = os.getenv("NAVI_FALLBACK_BASE", "https://api.groq.com/openai/v1")
        self.fallback_model = os.getenv("NAVI_FALLBACK_MODEL", "llama-3.1-70b-versatile")
        self.allow_cloud = os.getenv("NAVI_ALLOW_CLOUD", "false").lower() == "true"
        self.api_key = os.getenv("OPENAI_API_KEY")

        self._primary_client = OpenAI(base_url=self.primary_base, api_key="ollama")
        self._fallback_client = None
        if self.allow_cloud and self.api_key:
            self._fallback_client = OpenAI(base_url=self.fallback_base, api_key=self.api_key)

    async def generate(self, prompt: str, system: Optional[str] = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            resp = self._primary_client.chat.completions.create(
                model=self.primary_model,
                messages=messages,
                temperature=0.7,
                max_tokens=4096,
            )
            logger.info("llm_success", model=self.primary_model)
            return resp.choices[0].message.content
        except Exception as e:
            logger.warning("llm_primary_failed", error=str(e))
            if self._fallback_client:
                try:
                    resp = self._fallback_client.chat.completions.create(
                        model=self.fallback_model,
                        messages=messages,
                        temperature=0.7,
                        max_tokens=4096,
                    )
                    logger.info("llm_fallback_success", model=self.fallback_model)
                    return resp.choices[0].message.content
                except Exception as e2:
                    logger.error("llm_fallback_failed", error=str(e2))
                    raise RuntimeError("All LLM providers failed.")
            raise

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        system = next((m["content"] for m in messages if m["role"] == "system"), None)
        user = next((m["content"] for m in messages if m["role"] == "user"), "")
        return await self.generate(user, system=system)
