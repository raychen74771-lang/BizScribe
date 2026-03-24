import os

# --- 核心代码定义 ---

FILES = {
    # 1. 配置文件
    "requirements.txt": """pydub\ngoogle-generativeai\nopenai\npydantic\npydantic-settings\npyyaml\npython-dotenv\nrich\ntyper""",
    
    ".env": """# 填入您的 API KEY
GOOGLE_API_KEY=
DEEPSEEK_API_KEY=
""",

    "config.yaml": """llm_profiles:
  gemini_flash:
    provider: "gemini"
    model_name: "gemini-2.5-flash"
    api_key_env_var: "GOOGLE_API_KEY"
    context_window: 1000000
    cost_per_million_tokens: 0.10

  deepseek_v3:
    provider: "deepseek"
    model_name: "deepseek-chat"
    api_key_env_var: "DEEPSEEK_API_KEY"
    base_url: "https://api.deepseek.com"
    context_window: 64000
    cost_per_million_tokens: 0.2

workflow:
  transcribe:
    use_profile: "gemini_flash"
    prompt:
      template_path: "transcribe_default.yaml"
      temperature: 0.3
  
  repair:
    use_profile: "deepseek_v3"
    prompt:
      template_path: "repair_strict.yaml"
      temperature: 0.1
""",

    # 2. 核心入口
    "main.py": """import asyncio
import os
import sys
import argparse
from src.config.loader import load_settings
from src.core.engine import WorkflowEngine
from src.core.audio import AudioProcessor
from rich.console import Console
from rich.panel import Panel

console = Console()

async def run_pipeline(audio_path: str):
    try:
        settings = load_settings()
    except Exception:
        return

    console.print(Panel(f"🚀 FlowScribe V2 Starting\\nTarget: {audio_path}", style="bold green"))

    processor = AudioProcessor(settings)
    try:
        chunks = processor.process_audio(audio_path)
    except Exception as e:
        console.print(f"[red]❌ Audio Processing Failed: {e}[/red]")
        return

    engine = WorkflowEngine(settings)
    await engine.run_batch(chunks)

    final_output_path = os.path.join(settings.output_dir, "FINAL_BOOK.md")
    with open(final_output_path, 'w', encoding='utf-8') as f:
        f.write(f"# Transcription: {os.path.basename(audio_path)}\\n\\n")
        sorted_chunks = sorted(engine.state_manager.state.chunks.values(), key=lambda x: x.chunk_id)
        for chunk in sorted_chunks:
            if chunk.status == "completed" and chunk.final_text:
                f.write(f"## {chunk.chunk_id}\\n\\n")
                f.write(chunk.final_text + "\\n\\n")
    
    console.print(Panel(f"🏁 DONE! Output saved to:\\n{final_output_path}", style="bold green"))

def main():
    parser = argparse.ArgumentParser(description="FlowScribe V2")
    parser.add_argument("audio_file", help="Path to input audio")
    args = parser.parse_args()
    
    if not os.path.isfile(args.audio_file):
        console.print(f"[red]Error: File {args.audio_file} not found.[/red]")
        sys.exit(1)
        
    asyncio.run(run_pipeline(args.audio_file))

if __name__ == "__main__":
    main()
""",

    # 3. 源代码结构
    "src/__init__.py": "",
    "src/config/__init__.py": "",
    "src/core/__init__.py": "",
    "src/core/llm/__init__.py": "from src.core.llm.interface import BaseLLMProvider\nfrom src.core.llm.providers import GeminiProvider, OpenAIProvider, OllamaProvider\nfrom src.core.llm.registry import LLMRegistry",
    "src/utils/__init__.py": "",

    # definitions.py
    "src/config/definitions.py": """from typing import Dict, Optional, Literal
from pydantic import BaseModel, Field, SecretStr

class LLMProfile(BaseModel):
    provider: Literal["gemini", "openai", "deepseek", "ollama"]
    model_name: str
    api_key: Optional[SecretStr] = Field(default=None)
    api_key_env_var: Optional[str] = None
    base_url: Optional[str] = None
    context_window: int = Field(...)
    cost_per_million_tokens: float = Field(0.0)

class PromptConfig(BaseModel):
    template_path: str
    temperature: float = 0.7

class WorkflowStage(BaseModel):
    use_profile: str
    prompt: PromptConfig

class WorkflowConfig(BaseModel):
    transcribe: WorkflowStage
    repair: Optional[WorkflowStage] = None
    refine: Optional[WorkflowStage] = None

class ProjectSettings(BaseModel):
    llm_profiles: Dict[str, LLMProfile]
    workflow: WorkflowConfig
    input_dir: str = "workspace/input"
    output_dir: str = "workspace/output"
""",

    # loader.py
    "src/config/loader.py": """import os
import yaml
from typing import Dict, Any
from dotenv import load_dotenv
from pydantic import ValidationError
from src.utils.logger import logger
from .definitions import ProjectSettings

load_dotenv()

def _inject_env_vars(config_data: Dict[str, Any]):
    profiles = config_data.get("llm_profiles", {})
    for name, profile in profiles.items():
        env_var = profile.get("api_key_env_var")
        if env_var:
            key_value = os.getenv(env_var)
            if key_value:
                profile["api_key"] = key_value

def load_settings(yaml_path: str = "config.yaml") -> ProjectSettings:
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"Config missing: {yaml_path}")
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            raw_data = yaml.safe_load(f)
        _inject_env_vars(raw_data)
        return ProjectSettings(**raw_data)
    except Exception as e:
        logger.critical(f"Config Error: {e}")
        raise
""",

    # logger.py
    "src/utils/logger.py": """import logging
from rich.logging import RichHandler
from rich.console import Console
console = Console()
def setup_logger(level="INFO"):
    logging.basicConfig(level=level, format="%(message)s", datefmt="[%X]", handlers=[RichHandler(console=console)])
    return logging.getLogger("flowscribe")
logger = setup_logger()
""",

    # prompt_loader.py
    "src/utils/prompt_loader.py": """import os
import yaml
from src.utils.logger import logger

def load_prompt_template(template_path: str) -> str:
    base_path = os.path.join(os.getcwd(), "assets", "prompts")
    full_path = os.path.join(base_path, template_path)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Prompt missing: {full_path}")
    with open(full_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        if isinstance(data, dict):
            return data.get('content') or str(data)
        return str(data)
""",

    # interface.py
    "src/core/llm/interface.py": """from abc import ABC, abstractmethod
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
""",

    # providers.py (LATEST VERSION)
    "src/core/llm/providers.py": """import os
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
            content_parts = []
            if audio_path:
                logger.debug(f"📤 Uploading audio: {os.path.basename(audio_path)}")
                audio_file = await asyncio.to_thread(genai.upload_file, path=audio_path)
                while audio_file.state.name == "PROCESSING":
                    await asyncio.sleep(1)
                    audio_file = await asyncio.to_thread(genai.get_file, audio_file.name)
                if audio_file.state.name == "FAILED":
                    raise ValueError("Gemini audio processing failed")
                content_parts.append(audio_file)
            
            final_prompt = prompt
            if system_instruction:
                final_prompt = f"System: {system_instruction}\\n\\n{prompt}"
            content_parts.append(final_prompt)
            
            response = await self.model.generate_content_async(content_parts)
            return response.text
        except Exception as e:
            logger.error(f"Gemini Error: {e}")
            raise

    def get_token_usage(self) -> Dict[str, int]:
        return {"total": 0}

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, profile: LLMProfile):
        super().__init__(profile)
        api_key = profile.api_key.get_secret_value() if profile.api_key else "ollama"
        self.client = AsyncOpenAI(api_key=api_key, base_url=profile.base_url)

    async def generate(self, prompt: str, system_instruction: Optional[str] = None, audio_path: Optional[str] = None) -> str:
        if audio_path:
            logger.warning("⚠️ OpenAI/DeepSeek does not support audio input directly.")
        messages = [{"role": "user", "content": prompt}]
        if system_instruction:
            messages.insert(0, {"role": "system", "content": system_instruction})
        
        response = await self.client.chat.completions.create(model=self.model_name, messages=messages)
        return response.choices[0].message.content or ""

    def get_token_usage(self) -> Dict[str, int]:
        return {"total": 0}

class OllamaProvider(OpenAIProvider):
    pass
""",

    # registry.py
    "src/core/llm/registry.py": """from typing import Dict
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
""",

    # state.py
    "src/core/state.py": """import json
import os
import time
from typing import Dict, Literal, Optional
from pydantic import BaseModel, Field
from src.utils.logger import logger

class ChunkState(BaseModel):
    chunk_id: str
    status: Literal["pending", "transcribing", "repairing", "repaired", "completed", "failed"] = "pending"
    original_text: Optional[str] = None
    final_text: Optional[str] = None
    error_msg: Optional[str] = None
    last_updated: float = Field(default_factory=time.time)

class WorkflowState(BaseModel):
    chunks: Dict[str, ChunkState] = {}
    def get_chunk(self, chunk_id: str):
        if chunk_id not in self.chunks: self.chunks[chunk_id] = ChunkState(chunk_id=chunk_id)
        return self.chunks[chunk_id]

class StateManager:
    def __init__(self, workspace_dir: str):
        self.path = os.path.join(workspace_dir, "state.json")
        self.state = self._load()
    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, 'r', encoding='utf-8') as f: return WorkflowState(**json.load(f))
            except: pass
        return WorkflowState()
    def save(self):
        with open(self.path, 'w', encoding='utf-8') as f: f.write(self.state.model_dump_json(indent=2))
    def update_chunk(self, chunk_id, **kwargs):
        chunk = self.state.get_chunk(chunk_id)
        for k,v in kwargs.items(): setattr(chunk, k, v)
        self.save()
""",

    # validator.py
    "src/core/validator.py": """import re
class QualityGate:
    @staticmethod
    def needs_repair(text: str) -> bool:
        if not text or len(text) < 10: return True
        punc = len(re.findall(r'[.,;!?，。；！？]', text))
        if punc / len(text) < 0.01: return True
        return False
""",

    # audio.py (LATEST VERSION)
    "src/core/audio.py": """import os
from pydub import AudioSegment
from pydub.silence import split_on_silence
from typing import List, Tuple
from src.utils.logger import logger
from src.config.definitions import ProjectSettings

class AudioProcessor:
    def __init__(self, settings: ProjectSettings):
        self.settings = settings
        self.temp_dir = os.path.join(settings.input_dir, "temp_chunks")
        os.makedirs(self.temp_dir, exist_ok=True)

    def process_audio(self, file_path: str) -> List[Tuple[str, str]]:
        if not os.path.exists(file_path): raise FileNotFoundError(file_path)
        logger.info(f"🎧 Loading: {file_path}")
        try:
            audio = AudioSegment.from_file(file_path)
        except Exception as e:
            logger.error("FFmpeg error?")
            raise e
        
        chunks = split_on_silence(audio, min_silence_len=1000, silence_thresh=-40, keep_silence=500)
        if not chunks:
            chunks = [audio[i:i+600000] for i in range(0, len(audio), 600000)]
            
        prepared = []
        for i, chunk in enumerate(chunks):
            cid = f"part_{i+1:03d}"
            path = os.path.join(self.temp_dir, f"{cid}.mp3")
            chunk.export(path, format="mp3", bitrate="192k")
            prepared.append((cid, path))
        logger.info(f"✅ Split into {len(prepared)} chunks")
        return prepared
""",

    # engine.py (LATEST VERSION)
    "src/core/engine.py": """import asyncio
from typing import List
from src.core.llm.registry import LLMRegistry
from src.core.state import StateManager
from src.core.validator import QualityGate
from src.utils.logger import logger
from src.utils.prompt_loader import load_prompt_template

class WorkflowEngine:
    def __init__(self, settings):
        self.settings = settings
        self.llm_map = LLMRegistry.build_registry(settings.llm_profiles)
        self.state_manager = StateManager(settings.output_dir)
        self.semaphore = asyncio.Semaphore(5)

    async def process_chunk(self, chunk_id, input_data):
        if self.state_manager.state.get_chunk(chunk_id).status == "completed": return
        async with self.semaphore:
            logger.info(f"🚀 Processing {chunk_id}")
            try:
                self.state_manager.update_chunk(chunk_id, status="transcribing")
                transcriber = self.llm_map[self.settings.workflow.transcribe.use_profile]
                prompt = load_prompt_template(self.settings.workflow.transcribe.prompt.template_path)
                
                if input_data.endswith(('.mp3', '.m4a', '.wav')):
                    res = await transcriber.generate(prompt, audio_path=input_data)
                else:
                    res = await transcriber.generate(f"{prompt}\\n\\n{input_data}")
                
                if QualityGate.needs_repair(res) and self.settings.workflow.repair:
                    logger.warning(f"⚠️ Repairing {chunk_id}")
                    repairer = self.llm_map[self.settings.workflow.repair.use_profile]
                    r_prompt = load_prompt_template(self.settings.workflow.repair.prompt.template_path)
                    res = await repairer.generate(f"{r_prompt}\\n\\n{res}")
                
                self.state_manager.update_chunk(chunk_id, status="completed", final_text=res)
                logger.info(f"✅ {chunk_id} Done")
            except Exception as e:
                logger.error(f"❌ {chunk_id} Failed: {e}")
                self.state_manager.update_chunk(chunk_id, status="failed", error_msg=str(e))

    async def run_batch(self, inputs):
        await asyncio.gather(*[self.process_chunk(cid, d) for cid, d in inputs])
""",

    # Assets
    "assets/prompts/transcribe_default.yaml": "content: 'Transcribe the following audio accurately. Maintain original language.'",
    "assets/prompts/repair_strict.yaml": "content: 'Fix punctuation and formatting. Do not change meaning.'",
    "assets/prompts/refine_polish.yaml": "content: 'Polish the text for readability.'",
}

def create_project():
    print("🚀 Restoring FlowScribe V2...")
    for path, content in FILES.items():
        # Create dir if needed
        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        
        # Write file
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Created: {path}")
    
    # Create workspace dirs
    os.makedirs("workspace/input", exist_ok=True)
    os.makedirs("workspace/output", exist_ok=True)
    print("\\n✨ Project Restored Successfully!")
    print("👉 Next Step: Run 'pip install -r requirements.txt'")

if __name__ == "__main__":
    create_project()