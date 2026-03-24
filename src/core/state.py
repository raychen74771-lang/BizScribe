import json
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
        if chunk_id not in self.chunks:
            self.chunks[chunk_id] = ChunkState(chunk_id=chunk_id)
        return self.chunks[chunk_id]

class StateManager:
    def __init__(self, workspace_dir: str):
        # 🔥 MAX CTO 修复补丁：如果目录被删了，自动建回来！
        os.makedirs(workspace_dir, exist_ok=True)
        
        self.path = os.path.join(workspace_dir, "state.json")
        self.state = self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, 'r', encoding='utf-8') as f:
                    return WorkflowState(**json.load(f))
            except Exception:
                pass # 如果文件坏了，就重来
        return WorkflowState()

    def save(self):
        # 双重保险：保存前再次确认目录存在
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        
        with open(self.path, 'w', encoding='utf-8') as f:
            f.write(self.state.model_dump_json(indent=2))
    
    def update_chunk(self, chunk_id, **kwargs):
        chunk = self.state.get_chunk(chunk_id)
        for k, v in kwargs.items():
            setattr(chunk, k, v)
        self.save()