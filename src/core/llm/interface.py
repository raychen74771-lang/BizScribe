from abc import ABC, abstractmethod
from typing import Optional, Dict
from src.config.definitions import LLMProfile

class BaseLLMProvider(ABC):
    def __init__(self, profile: LLMProfile):
        self.profile = profile
        self.model_name = profile.model_name
        
    @abstractmethod
    async def generate(self, prompt: str, system_instruction: Optional[str] = None, audio_path: Optional[str] = None) -> str:
        pass

    @abstractmethod
    def get_token_usage(self) -> Dict[str, int]:
        pass
