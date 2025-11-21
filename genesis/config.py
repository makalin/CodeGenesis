"""Configuration management for Code Genesis."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Manages configuration for Code Genesis."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration from YAML file."""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.yaml"
        
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from YAML file."""
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                self.config = yaml.safe_load(f) or {}
        else:
            self.config = self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "repository": {
                "path": "./",
                "ignore_patterns": [
                    "**/.git/**",
                    "**/node_modules/**",
                    "**/__pycache__/**",
                    "**/*.pyc",
                ],
            },
            "llm": {
                "provider": "openai",
                "model": "gpt-4-turbo-preview",
                "temperature": 0.7,
                "max_tokens": 4000,
            },
            "vector_db": {
                "persist_directory": "./.genesis_index",
                "collection_name": "codebase_embeddings",
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated key."""
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def get_llm_api_key(self) -> Optional[str]:
        """Get LLM API key from environment."""
        return os.getenv("GENESIS_LLM_API_KEY") or os.getenv("OPENAI_API_KEY")

    def get_repo_path(self) -> Path:
        """Get repository path."""
        repo_path = self.get("repository.path", "./")
        return Path(repo_path).resolve()

