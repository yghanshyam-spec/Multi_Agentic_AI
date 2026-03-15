"""agents/translation/tools/glossary_store.py — in-memory glossary store."""
from __future__ import annotations

_GLOSSARIES: dict[str, dict] = {
    ("hr", "en", "de"): {"Annual Leave": "Jahresurlaub", "Probation": "Probezeit"},
    ("legal", "en", "fr"): {"indemnity": "indemnité", "covenant": "covenant"},
}

def get_glossary(domain: str, source: str, target: str) -> dict:
    key = (domain.lower(), source.lower()[:2], target.lower()[:2])
    return _GLOSSARIES.get(key, {})

def list_domains() -> list[str]:
    return list({k[0] for k in _GLOSSARIES})
