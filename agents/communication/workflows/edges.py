"""
communication/workflows/edges.py
Conditional routing logic for LangGraph edges.
Handles YAML bool keys (True/False) correctly.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from shared.common import get_logger

logger = get_logger(__name__)


def build_conditional_router(
    condition_field: str,
    routes: Dict[Any, str],
    default: Optional[str] = None,
) -> Callable[[Dict[str, Any]], str]:
    """
    Build a config-driven router. Two-stage lookup:
    1. Direct value match (handles Python bool True/False from YAML)
    2. Normalised lowercase string match
    """
    _raw = dict(routes)
    _str = {str(k).lower(): v for k, v in routes.items()}

    def router(state: Dict[str, Any]) -> str:
        value = _resolve_nested(state, condition_field)
        if value in _raw:
            target = _raw[value]
        elif str(value).lower() in _str:
            target = _str[str(value).lower()]
        elif default:
            target = default
        else:
            raise ValueError(
                f"No route for '{condition_field}'={value!r}. Available: {list(routes.keys())}"
            )
        logger.info(f"[EDGE] '{condition_field}'={value!r} -> '{target}'")
        return target

    return router


def _resolve_nested(state: Dict[str, Any], path: str) -> Any:
    parts = path.split(".")
    current = state
    for p in parts:
        if current is None:
            return None
        current = current.get(p) if isinstance(current, dict) else getattr(current, p, None)
    return current


# ---- Named routing helpers --------------------------------------------------

def route_on_error(state: Dict[str, Any]) -> str:
    return "error_handler" if state.get("error") else "load_context_node"


def route_on_classification(state: Dict[str, Any]) -> str:
    cls = (state.get("classification") or {}).get("classification", "automated_response")
    if cls == "human_escalation":
        return "dispatch_response_node"   # skip drafting; use pre-built escalation msg
    if cls == "acknowledgement_only":
        return "dispatch_response_node"
    return "draft_response_node"


def route_on_consistency(state: Dict[str, Any]) -> str:
    report = state.get("consistency_report") or {}
    is_consistent = report.get("is_consistent", True)
    return "dispatch_response_node" if is_consistent else "dispatch_response_node"


def route_on_requires_human(state: Dict[str, Any]) -> str:
    cls = state.get("classification") or {}
    return "update_context_node" if cls.get("requires_human") else "check_consistency_node"
