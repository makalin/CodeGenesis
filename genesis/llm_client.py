"""LLM client for code generation."""

import os
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from genesis.config import Config


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Generate text from prompt."""
        pass


class OpenAIClient(LLMClient):
    """OpenAI API client."""

    def __init__(self, config: Config):
        """Initialize OpenAI client."""
        if openai is None:
            raise ImportError("openai package is required. Install with: pip install openai")
        
        api_key = config.get_llm_api_key()
        if not api_key:
            raise ValueError("GENESIS_LLM_API_KEY or OPENAI_API_KEY environment variable not set")
        
        self.client = openai.OpenAI(api_key=api_key)
        self.model = config.get("llm.model", "gpt-4-turbo-preview")
        self.temperature = config.get("llm.temperature", 0.7)
        self.max_tokens = config.get("llm.max_tokens", 4000)

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Generate text using OpenAI API."""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=kwargs.get("model", self.model),
            messages=messages,
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
        )
        
        return response.choices[0].message.content


class AnthropicClient(LLMClient):
    """Anthropic Claude API client."""

    def __init__(self, config: Config):
        """Initialize Anthropic client."""
        if anthropic is None:
            raise ImportError("anthropic package is required. Install with: pip install anthropic")
        
        api_key = config.get_llm_api_key()
        if not api_key:
            raise ValueError("GENESIS_LLM_API_KEY or ANTHROPIC_API_KEY environment variable not set")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = config.get("llm.model", "claude-3-opus-20240229")
        self.temperature = config.get("llm.temperature", 0.7)
        self.max_tokens = config.get("llm.max_tokens", 4000)

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Generate text using Anthropic API."""
        messages = [{"role": "user", "content": prompt}]
        
        response = self.client.messages.create(
            model=kwargs.get("model", self.model),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            temperature=kwargs.get("temperature", self.temperature),
            system=system_prompt or "",
            messages=messages,
        )
        
        return response.content[0].text


class GoogleClient(LLMClient):
    """Google Gemini API client."""

    def __init__(self, config: Config):
        """Initialize Google client."""
        if genai is None:
            raise ImportError("google-generativeai package is required. Install with: pip install google-generativeai")
        
        api_key = config.get_llm_api_key()
        if not api_key:
            raise ValueError("GENESIS_LLM_API_KEY or GOOGLE_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        self.model_name = config.get("llm.model", "gemini-pro")
        self.model = genai.GenerativeModel(self.model_name)
        self.temperature = config.get("llm.temperature", 0.7)

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Generate text using Google Gemini API."""
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        generation_config = {
            "temperature": kwargs.get("temperature", self.temperature),
            "max_output_tokens": kwargs.get("max_tokens", 4000),
        }
        
        response = self.model.generate_content(
            full_prompt,
            generation_config=generation_config,
        )
        
        return response.text


def create_llm_client(config: Config) -> LLMClient:
    """Factory function to create appropriate LLM client."""
    provider = config.get("llm.provider", "openai").lower()
    
    if provider == "openai":
        return OpenAIClient(config)
    elif provider == "anthropic":
        return AnthropicClient(config)
    elif provider == "google":
        return GoogleClient(config)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

