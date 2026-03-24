from typing import Dict
from src.config.definitions import LLMProfile
from src.core.llm.interface import BaseLLMProvider
from src.core.llm.providers import GeminiProvider, OpenAIProvider, OllamaProvider
from src.utils.logger import logger

class LLMRegistry:
    @staticmethod
    def create_llm(profile: LLMProfile) -> BaseLLMProvider:
        if profile.provider == "gemini": return GeminiProvider(profile)
        elif profile.provider in ["openai", "deepseek", "ollama"]: return OpenAIProvider(profile)
        raise ValueError(f"Unknown provider: {profile.provider}")

    @staticmethod
    def build_registry(profiles: Dict[str, LLMProfile]) -> Dict[str, BaseLLMProvider]:
        registry = {}
        for name, p in profiles.items():
            try:
                registry[name] = LLMRegistry.create_llm(p)
            except Exception as e:
                logger.error(f"Failed to init {name}: {e}")
        return registry
