"""
communication/utils/config_loader.py
YAML loader with ${ENV_VAR:default} interpolation.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict

import yaml

from communication.utils.logger import get_logger

logger = get_logger(__name__)

_ENV_PATTERN = re.compile(r"\$\{([^}:]+)(?::([^}]*))?\}")


def _interpolate(value: Any) -> Any:
    if isinstance(value, str):
        def replacer(m: re.Match) -> str:
            return os.environ.get(m.group(1), m.group(2) or "")
        return _ENV_PATTERN.sub(replacer, value)
    if isinstance(value, dict):
        return {k: _interpolate(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_interpolate(i) for i in value]
    return value


class ConfigLoader:
    def load(self, path: str) -> Dict[str, Any]:
        p = Path(path)
        if not p.exists():
            logger.warning(f"Config not found: {path}")
            return {}
        raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        return _interpolate(raw)

    def load_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return _interpolate(data)
