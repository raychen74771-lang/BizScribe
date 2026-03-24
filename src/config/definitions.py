from typing import Dict, Optional, Literal
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
