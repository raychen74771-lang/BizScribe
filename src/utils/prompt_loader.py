import os
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
