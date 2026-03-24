import os
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
