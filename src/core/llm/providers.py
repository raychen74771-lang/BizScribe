import os
import asyncio
import google.generativeai as genai
from openai import AsyncOpenAI
from typing import Optional, Dict
from src.core.llm.interface import BaseLLMProvider
from src.config.definitions import LLMProfile
from src.utils.logger import logger

class GeminiProvider(BaseLLMProvider):
    def __init__(self, profile: LLMProfile):
        super().__init__(profile)
        if profile.api_key:
            genai.configure(api_key=profile.api_key.get_secret_value())
        self.model = genai.GenerativeModel(profile.model_name)

    async def generate(self, prompt: str, system_instruction: Optional[str] = None, audio_path: Optional[str] = None) -> str:
        try:
            content_parts =[]
            if audio_path:
                logger.info(f"📤 云端直连上传音频: {os.path.basename(audio_path)}")
                audio_file = await asyncio.to_thread(genai.upload_file, path=audio_path)
                while audio_file.state.name == "PROCESSING":
                    await asyncio.sleep(1)
                    audio_file = await asyncio.to_thread(genai.get_file, audio_file.name)
                if audio_file.state.name == "FAILED":
                    raise ValueError("Gemini audio processing failed")
                content_parts.append(audio_file)
            
            final_prompt = prompt
            if system_instruction:
                final_prompt = f"System: {system_instruction}\n\n{prompt}"
            content_parts.append(final_prompt)
            
            response = await self.model.generate_content_async(content_parts)
            
            # 💎 核心防抖设计：安全提取文本
            try:
                return response.text
            except ValueError as ve:
                # 捕获 finish_reason = 1 但没有 valid Part 的情况
                logger.warning(f"⚠️ 拦截到空输出 (该切片可能全为韩语或静音)。已安全跳过。")
                return "" # 返回空字符串，不影响合订本的拼接

        except Exception as e:
            logger.error(f"❌ Gemini 云端请求失败: {e}")
            raise

    def get_token_usage(self) -> Dict[str, int]:
        return {"total": 0}

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, profile: LLMProfile):
        super().__init__(profile)
        api_key = profile.api_key.get_secret_value() if profile.api_key else "empty"
        self.client = AsyncOpenAI(api_key=api_key, base_url=profile.base_url or "https://api.deepseek.com")

    async def generate(self, prompt: str, system_instruction: Optional[str] = None, audio_path: Optional[str] = None) -> str:
        messages = [{"role": "user", "content": prompt}]
        if system_instruction:
            messages.insert(0, {"role": "system", "content": system_instruction})
        response = await self.client.chat.completions.create(model=self.model_name, messages=messages)
        return response.choices[0].message.content or ""

    def get_token_usage(self) -> Dict[str, int]: return {"total": 0}

class OllamaProvider(OpenAIProvider): pass