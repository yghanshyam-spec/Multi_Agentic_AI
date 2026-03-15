"""
communication/core/provider.py
LLM client factory: OpenAI, Anthropic, Azure OpenAI.
"""
from __future__ import annotations

import os
from typing import Any, Dict

from shared.common import get_logger

logger = get_logger(__name__)


class LLMProvider:
    def __init__(self, llm_config: Dict[str, Any]):
        self._cfg = llm_config
        self._provider = os.environ.get(
            "LLM_PROVIDER", llm_config.get("provider", "openai")
        ).lower()

    def get_client(self) -> Any:
        provider_cfg = self._cfg.get("providers", {}).get(self._provider, {})
        temperature  = provider_cfg.get("temperature", self._cfg.get("temperature", 0.2))
        max_tokens   = provider_cfg.get("max_tokens",  self._cfg.get("max_tokens", 2048))

        try:
            if self._provider == "openai":
                from langchain_openai import ChatOpenAI
                model = provider_cfg.get("model", "gpt-4o")
                logger.info(f"LLM: OpenAI {model}")
                return ChatOpenAI(model=model, temperature=temperature,
                                  max_tokens=max_tokens,
                                  api_key=os.environ.get("OPENAI_API_KEY", ""))

            elif self._provider == "anthropic":
                from langchain_anthropic import ChatAnthropic
                model = provider_cfg.get("model", "claude-sonnet-4-20250514")
                logger.info(f"LLM: Anthropic {model}")
                return ChatAnthropic(model=model, temperature=temperature,
                                     max_tokens=max_tokens,
                                     api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

            elif self._provider == "azure_openai":
                from langchain_openai import AzureChatOpenAI
                logger.info("LLM: Azure OpenAI")
                return AzureChatOpenAI(
                    azure_deployment=provider_cfg.get("model", os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")),
                    azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
                    api_key=os.environ.get("AZURE_OPENAI_API_KEY", ""),
                    api_version=provider_cfg.get("api_version", "2024-02-01"),
                    temperature=temperature, max_tokens=max_tokens,
                )
            else:
                raise ValueError(f"Unknown LLM provider: {self._provider}")
        except ImportError as exc:
            logger.error(f"LLM import failed: {exc}")
            raise
