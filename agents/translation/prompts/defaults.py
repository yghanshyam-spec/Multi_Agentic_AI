"""agents/translation/prompts/defaults.py — built-in prompt defaults."""

DETECT_LANGUAGE = (
    "You are a language identification expert. "
    "Detect the language of the following text and return JSON: "
    "{{detected_language: str, confidence: float, script: str}}\n"
    "Text: {text}"
)

LOAD_GLOSSARY = (
    "You are a terminology manager. Given the domain and language pair, "
    "list key domain-specific terms that must be preserved exactly during translation. "
    "Domain: {domain} | Source: {source_language} | Target: {target_language}\n"
    "Return JSON: {{glossary: {{source_term: target_term}}, protected_terms: [str]}}"
)

PREPROCESS_TEXT = (
    "Identify all non-translatable elements in the following text: "
    "proper nouns, code snippets, placeholders like {{{{var}}}}, currency symbols, URLs, email addresses. "
    "Return JSON: {{protected_spans: [{{text: str, type: str, placeholder: str}}], "
    "clean_text: str}}\nText: {text}"
)

TRANSLATE = (
    "You are an expert {target_language} translator specialising in {domain} content.\n"
    "Translate the following from {source_language} to {target_language}.\n"
    "Preserve formatting, paragraph structure, and tone.\n"
    "Do NOT translate: {protected_terms}\n"
    "Use these domain-specific terms: {glossary}\n"
    "Text to translate:\n{text}"
)

BACK_TRANSLATE = (
    "Translate this {target_language} text back to {source_language} for quality "
    "verification only. Do not optimise; translate literally.\nText: {translated_text}"
)

SCORE_QUALITY = (
    "Compare the original text and back-translation for semantic equivalence.\n"
    "Original: {original}\nBack-translation: {back_translated}\n"
    "Score semantic similarity (0-1) and identify any meaning distortions.\n"
    "Return JSON: {{score: float, distortions: [str], review_required: bool}}"
)

FORMAT_LOCALE = (
    "Apply locale-specific formatting to the translated text for the {target_locale} locale.\n"
    "Adjust: date formats, currency symbols, number separators, address formats.\n"
    "Text: {translated_text}\n"
    "Return JSON: {{formatted_text: str, changes_made: [str]}}"
)

_REGISTRY = {
    "translation_detect_language": DETECT_LANGUAGE,
    "translation_load_glossary": LOAD_GLOSSARY,
    "translation_preprocess": PREPROCESS_TEXT,
    "translation_translate": TRANSLATE,
    "translation_back_translate": BACK_TRANSLATE,
    "translation_score_quality": SCORE_QUALITY,
    "translation_format_locale": FORMAT_LOCALE,
}

def get_default_prompt(key: str) -> str:
    return _REGISTRY.get(key, "")
