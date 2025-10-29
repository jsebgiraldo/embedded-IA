"""
LLM Provider Abstraction Layer

Supports multiple LLM providers with automatic fallback:
- Local models via Ollama
- OpenAI (GPT-4, GPT-4o-mini)
- Anthropic (Claude 3.5 Sonnet)
- Azure OpenAI

Usage:
    from agent.llm_provider import get_llm, LLMConfig
    
    # Local model (preferred)
    llm = get_llm(LLMConfig(
        provider="ollama",
        model="qwen2.5-coder:14b"
    ))
    
    # Cloud with fallback
    llm = get_llm(LLMConfig(
        provider="openai",
        model="gpt-4o-mini",
        fallback_to_local=True
    ))
"""

import os
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass
from langchain_core.language_models import BaseLLM


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"


@dataclass
class LLMConfig:
    """Configuration for LLM provider"""
    provider: LLMProvider = LLMProvider.OLLAMA
    model: str = "qwen2.5-coder:14b"
    temperature: float = 0.0
    max_tokens: Optional[int] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    fallback_to_local: bool = True
    timeout: int = 300  # 5 minutes
    
    # Ollama specific
    num_ctx: int = 8192  # Context window
    
    # OpenAI specific
    organization: Optional[str] = None
    
    def __post_init__(self):
        """Load from environment if not specified"""
        if self.provider == LLMProvider.OPENAI and not self.api_key:
            self.api_key = os.getenv("OPENAI_API_KEY")
        elif self.provider == LLMProvider.ANTHROPIC and not self.api_key:
            self.api_key = os.getenv("ANTHROPIC_API_KEY")
        elif self.provider == LLMProvider.AZURE:
            self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
            self.base_url = os.getenv("AZURE_OPENAI_ENDPOINT")


# Recommended models for ESP32 development
RECOMMENDED_MODELS = {
    LLMProvider.OLLAMA: {
        "best": "deepseek-coder-v2:16b",
        "balanced": "qwen2.5-coder:14b",
        "fast": "codellama:13b",
        "lightweight": "codellama:7b"
    },
    LLMProvider.OPENAI: {
        "best": "gpt-4o",
        "balanced": "gpt-4o-mini",
        "fast": "gpt-3.5-turbo"
    },
    LLMProvider.ANTHROPIC: {
        "best": "claude-3-5-sonnet-20241022",
        "balanced": "claude-3-5-haiku-20241022"
    }
}


def get_ollama_llm(config: LLMConfig) -> BaseLLM:
    """
    Get Ollama LLM instance
    
    Requires:
        - Ollama installed: brew install ollama
        - Model pulled: ollama pull qwen2.5-coder:14b
        - Server running: ollama serve
    """
    try:
        from langchain_community.llms import Ollama
    except ImportError:
        raise ImportError(
            "langchain-community not installed. "
            "Install with: pip install langchain-community"
        )
    
    base_url = config.base_url or "http://localhost:11434"
    
    llm = Ollama(
        model=config.model,
        base_url=base_url,
        temperature=config.temperature,
        num_ctx=config.num_ctx,
        timeout=config.timeout,
    )
    
    # Test connection
    try:
        llm.invoke("test", max_tokens=1)
    except Exception as e:
        raise ConnectionError(
            f"Cannot connect to Ollama at {base_url}. "
            f"Make sure 'ollama serve' is running. Error: {e}"
        )
    
    return llm


def get_openai_llm(config: LLMConfig) -> BaseLLM:
    """
    Get OpenAI LLM instance
    
    Requires:
        - OPENAI_API_KEY environment variable
        - or api_key in config
    """
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        raise ImportError(
            "langchain-openai not installed. "
            "Install with: pip install langchain-openai"
        )
    
    if not config.api_key:
        raise ValueError(
            "OpenAI API key required. Set OPENAI_API_KEY env var "
            "or pass api_key in config"
        )
    
    llm = ChatOpenAI(
        model=config.model,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        api_key=config.api_key,
        organization=config.organization,
        timeout=config.timeout,
    )
    
    return llm


def get_anthropic_llm(config: LLMConfig) -> BaseLLM:
    """
    Get Anthropic Claude LLM instance
    
    Requires:
        - ANTHROPIC_API_KEY environment variable
        - or api_key in config
    """
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError:
        raise ImportError(
            "langchain-anthropic not installed. "
            "Install with: pip install langchain-anthropic"
        )
    
    if not config.api_key:
        raise ValueError(
            "Anthropic API key required. Set ANTHROPIC_API_KEY env var "
            "or pass api_key in config"
        )
    
    llm = ChatAnthropic(
        model=config.model,
        temperature=config.temperature,
        max_tokens=config.max_tokens or 4096,
        api_key=config.api_key,
        timeout=config.timeout,
    )
    
    return llm


def get_azure_llm(config: LLMConfig) -> BaseLLM:
    """
    Get Azure OpenAI LLM instance
    
    Requires:
        - AZURE_OPENAI_API_KEY environment variable
        - AZURE_OPENAI_ENDPOINT environment variable
        - or base_url and api_key in config
    """
    try:
        from langchain_openai import AzureChatOpenAI
    except ImportError:
        raise ImportError(
            "langchain-openai not installed. "
            "Install with: pip install langchain-openai"
        )
    
    if not config.api_key or not config.base_url:
        raise ValueError(
            "Azure OpenAI requires API key and endpoint. "
            "Set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT env vars"
        )
    
    llm = AzureChatOpenAI(
        deployment_name=config.model,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        azure_endpoint=config.base_url,
        api_key=config.api_key,
        timeout=config.timeout,
    )
    
    return llm


def get_llm(config: Optional[LLMConfig] = None) -> BaseLLM:
    """
    Get LLM instance with automatic fallback
    
    Args:
        config: LLM configuration. If None, uses default (Ollama qwen2.5-coder:14b)
    
    Returns:
        BaseLLM instance
    
    Raises:
        Exception: If all providers fail and no fallback available
    
    Examples:
        # Use local Ollama (default)
        llm = get_llm()
        
        # Specific local model
        llm = get_llm(LLMConfig(
            provider=LLMProvider.OLLAMA,
            model="deepseek-coder-v2:16b"
        ))
        
        # OpenAI with local fallback
        llm = get_llm(LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4o-mini",
            fallback_to_local=True
        ))
        
        # Claude without fallback
        llm = get_llm(LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3-5-sonnet-20241022",
            fallback_to_local=False
        ))
    """
    if config is None:
        config = LLMConfig()
    
    providers = {
        LLMProvider.OLLAMA: get_ollama_llm,
        LLMProvider.OPENAI: get_openai_llm,
        LLMProvider.ANTHROPIC: get_anthropic_llm,
        LLMProvider.AZURE: get_azure_llm,
    }
    
    # Try primary provider
    try:
        provider_func = providers[config.provider]
        llm = provider_func(config)
        print(f"✅ Using {config.provider.value} model: {config.model}")
        return llm
    except Exception as e:
        print(f"⚠️  Failed to initialize {config.provider.value}: {e}")
        
        # Try fallback to local if enabled
        if config.fallback_to_local and config.provider != LLMProvider.OLLAMA:
            print("🔄 Attempting fallback to local Ollama model...")
            try:
                fallback_config = LLMConfig(
                    provider=LLMProvider.OLLAMA,
                    model=RECOMMENDED_MODELS[LLMProvider.OLLAMA]["balanced"],
                    temperature=config.temperature,
                )
                llm = get_ollama_llm(fallback_config)
                print(f"✅ Fallback successful: {fallback_config.model}")
                return llm
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {fallback_error}")
        
        # No fallback or fallback failed
        raise Exception(
            f"Failed to initialize LLM provider {config.provider.value}. "
            f"Original error: {e}"
        )


def get_recommended_model(
    provider: LLMProvider,
    tier: str = "balanced"
) -> str:
    """
    Get recommended model for a provider
    
    Args:
        provider: LLM provider
        tier: "best", "balanced", "fast", or "lightweight"
    
    Returns:
        Model name
    
    Examples:
        >>> get_recommended_model(LLMProvider.OLLAMA, "best")
        'deepseek-coder-v2:16b'
        
        >>> get_recommended_model(LLMProvider.OPENAI, "balanced")
        'gpt-4o-mini'
    """
    models = RECOMMENDED_MODELS.get(provider, {})
    return models.get(tier, models.get("balanced", ""))


def test_llm_connection(config: Optional[LLMConfig] = None) -> Dict[str, Any]:
    """
    Test LLM connection and get model info
    
    Returns:
        Dict with connection status and model info
    """
    try:
        llm = get_llm(config)
        
        # Simple test prompt
        test_prompt = "What is 2+2? Reply with just the number."
        response = llm.invoke(test_prompt)
        
        return {
            "success": True,
            "provider": config.provider.value if config else "ollama",
            "model": config.model if config else "qwen2.5-coder:14b",
            "test_response": str(response),
            "message": "Connection successful"
        }
    except Exception as e:
        return {
            "success": False,
            "provider": config.provider.value if config else "ollama",
            "model": config.model if config else "qwen2.5-coder:14b",
            "error": str(e),
            "message": "Connection failed"
        }


if __name__ == "__main__":
    """Test LLM providers"""
    import sys
    
    print("🧪 Testing LLM Providers\n")
    
    # Test Ollama (default)
    print("1️⃣  Testing Ollama (local)...")
    result = test_llm_connection()
    print(f"   {'✅' if result['success'] else '❌'} {result['message']}")
    if result['success']:
        print(f"   Model: {result['model']}")
        print(f"   Response: {result['test_response']}")
    else:
        print(f"   Error: {result['error']}")
    print()
    
    # Test OpenAI if key available
    if os.getenv("OPENAI_API_KEY"):
        print("2️⃣  Testing OpenAI...")
        result = test_llm_connection(LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4o-mini"
        ))
        print(f"   {'✅' if result['success'] else '❌'} {result['message']}")
        if result['success']:
            print(f"   Model: {result['model']}")
        print()
    
    # Test Anthropic if key available
    if os.getenv("ANTHROPIC_API_KEY"):
        print("3️⃣  Testing Anthropic...")
        result = test_llm_connection(LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3-5-haiku-20241022"
        ))
        print(f"   {'✅' if result['success'] else '❌'} {result['message']}")
        if result['success']:
            print(f"   Model: {result['model']}")
        print()
    
    print("✨ Testing complete!")
    print("\nRecommended models:")
    for provider in [LLMProvider.OLLAMA, LLMProvider.OPENAI, LLMProvider.ANTHROPIC]:
        print(f"\n{provider.value.upper()}:")
        for tier in ["best", "balanced", "fast"]:
            model = get_recommended_model(provider, tier)
            if model:
                print(f"  {tier}: {model}")
