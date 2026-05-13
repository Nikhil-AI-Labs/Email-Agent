"""
config.py - Configuration management for Email Agent
Handles swappable LLM providers and UI defaults.
"""
from typing import Dict, Any

#xfgk ietm azyr nteb
PROVIDERS = {
    "Sarvam AI": {
        "base_url": "https://api.sarvam.ai/v1",
        "default_model": "sarvam-105b",
        "env_var": "sk_w09osx2v_SR1UlAUpzvt8K86aPl0YfZlT",
        "description": "Sarvam 105B via OpenAI compat layer"
    },
    "OpenAI": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o",
        "env_var": "OPENAI_API_KEY",
        "description": "OpenAI Official API"
    },
    "Custom (OpenAI Compat)": {
        "base_url": "",
        "default_model": "",
        "env_var": "CUSTOM_API_KEY",
        "description": "Any OpenAI-compatible endpoint (e.g., vLLM, Ollama, Groq)"
    }
}

# Default App Settings
DEFAULT_CONFIG = {
    "provider": "Sarvam AI",
    "hitl_enabled": True,
    "temperature": 0.3,
}

def get_llm_config(provider_name: str, api_key: str, base_url_override: str = "", model_override: str = "") -> Dict[str, Any]:
    """Returns kwargs suitable for initializing ChatOpenAI."""
    if provider_name not in PROVIDERS:
        provider_name = "Custom (OpenAI Compat)"
        
    provider_info = PROVIDERS[provider_name]
    
    return {
        "base_url": base_url_override or provider_info["base_url"],
        "api_key": api_key,
        "model": model_override or provider_info["default_model"],
        "temperature": DEFAULT_CONFIG["temperature"]
    }
