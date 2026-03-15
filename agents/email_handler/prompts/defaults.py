"""agents/email_handler/prompts/defaults.py"""

FETCH_EMAIL = (
    "You are an email processing assistant. Summarise the email metadata for routing.\n"
    "Headers: {headers}\nPreview: {body_preview}\n"
    "Return JSON: {{subject: str, sender: str, has_attachments: bool, urgency_hint: str}}"
)

PARSE_EMAIL = (
    "Extract structured information from this email.\n"
    "Email headers: {headers}\nEmail body: {body}\n"
    "Extract: sender, intent, key_entities (names, dates, amounts, order_ids), "
    "action_required, urgency.\nReturn JSON."
)

CLASSIFY_EMAIL = (
    "Classify this email into a handling category.\n"
    "Email summary: {parsed_email}\n"
    "Categories: [INVOICE, COMPLAINT, INQUIRY, APPROVAL_REQUEST, SPAM, "
    "INTERNAL_NOTIFICATION, CONTRACT, OTHER]\n"
    "Return JSON: {{category: str, confidence: float, sub_category: str, requires_human: bool}}"
)

DRAFT_REPLY = (
    "Draft a professional email reply.\n"
    "Original email: {original_email}\n"
    "Context / resolved information: {context}\n"
    "Tone: {tone} | Organisation name: {org_name}\n"
    "Draft a reply that directly addresses the sender's request. "
    "Do not hallucinate facts not in the context."
)

ROUTE_ACTION = (
    "Based on this email classification, determine the downstream action.\n"
    "Classification: {classification}\nEntities: {entities}\n"
    "Available routes: [INVOICE_PROCESSOR, CRM_UPDATE, SQL_QUERY, HUMAN_ESCALATION, AUTO_REPLY]\n"
    "Return JSON: {{route: str, rationale: str, priority: low|medium|high}}"
)

_REGISTRY = {
    "email_handler_fetch": FETCH_EMAIL,
    "email_handler_parse": PARSE_EMAIL,
    "email_handler_classify": CLASSIFY_EMAIL,
    "email_handler_draft_reply": DRAFT_REPLY,
    "email_handler_route": ROUTE_ACTION,
}

def get_default_prompt(key: str) -> str:
    return _REGISTRY.get(key, "")
