"""
orchestration/use_cases/invoice_to_pay.py
==========================================
Use-case: Invoice-to-Pay Workflow
Demonstrates 8 new agents working together in an enterprise workflow.

Pipeline steps:
  [Layer 1] email_handler     — Classify inbound invoice email + parse attachments
  [Layer 2] pdf_ingestor      — Extract and chunk the invoice PDF
  [Layer 3] sap_agent         — Match PO in SAP and validate three-way match
  [Layer 2] reasoning         — Evaluate if amounts match; flag discrepancies
  [Layer 3] hitl              — Human approval gate for exceptions
  [Layer 3] execution         — Post goods receipt / payment in ERP
  [Layer 2] notification_agent — Notify vendor of payment status
  [Layer 0] audit             — Compliance audit trail
"""
from __future__ import annotations
from orchestration.pipeline import UseCaseConfig, StepDef

USE_CASE_PROMPT = (
    "An invoice (INV-2024-0091, £4,200.00) has arrived from Vendor Corp via email with "
    "attached PDF. PO number referenced: PO-4500001234. Please:\n"
    "1. Parse the email and extract the invoice PDF\n"
    "2. Ingest the invoice into the document store\n"
    "3. Match against the SAP purchase order\n"
    "4. Validate the three-way match (PO → GR → Invoice)\n"
    "5. Get human approval for the payment if amounts differ\n"
    "6. Post the goods receipt and trigger payment in SAP\n"
    "7. Notify the vendor of payment status\n"
    "8. Log the full audit trail for compliance"
)


def _email_input(ctx, inp):
    return inp, {}


def _pdf_input(ctx, inp):
    email_state = ctx.get("email_handler", {})
    attachments = email_state.get("processed_attachments", [])
    pdf_path = attachments[0].get("name", "invoice.pdf") if attachments else "invoice.pdf"
    return "Ingest invoice PDF", {"pdf_path": pdf_path}


def _sap_input(ctx, inp):
    pdf_state = ctx.get("pdf_ingestor", {})
    chunk_text = " ".join(c.get("text", "") for c in pdf_state.get("chunks", [])[:3])
    return f"Match PO and validate goods receipt for: {chunk_text[:200]}", {}


def _reasoning_input(ctx, inp):
    sap = ctx.get("sap", {})
    email = ctx.get("email_handler", {})
    return (
        f"Validate three-way match: "
        f"Invoice amount from email: {email.get('email_entities', {}).get('amount', '£4,200.00')}. "
        f"SAP PO result: {sap.get('sap_summary', 'PO matched')}. "
        f"Are there discrepancies that require human approval?",
        {}
    )


def _hitl_input(ctx, inp):
    reasoning = ctx.get("reasoning", {})
    conclusion = (reasoning.get("conclusion") or {}).get("conclusion", "")
    return (
        "Approve payment posting for Invoice INV-2024-0091",
        {"working_memory": {
            "risk": "medium",
            "execution_plan": {
                "script": "BAPI_ACC_DOCUMENT_POST with reference INV-2024-0091",
                "target": "SAP FI module",
                "expected_outcome": "Payment document posted",
            },
            "reasoning_conclusion": conclusion,
        }}
    )


def _execution_input(ctx, inp):
    hitl = ctx.get("hitl", {})
    return (
        "Post payment document in SAP for INV-2024-0091",
        {
            "execution_plan": {
                "script": "BAPI_ACC_DOCUMENT_POST ref=INV-2024-0091 amount=4200.00 currency=GBP",
                "target": "SAP FI",
                "expected_outcome": "Payment document FI-DOC-9001 created",
                "requires_approval": True,
            },
            "approved_by": hitl.get("approver_id", "finance_controller"),
        }
    )


def _notification_input(ctx, inp):
    execution = ctx.get("execution", {})
    return (
        "Notify vendor that invoice INV-2024-0091 has been approved and payment is processing",
        {"event_payload": {
            "type": "PAYMENT_PROCESSED",
            "source": "accounts_payable_workflow",
            "details": f"Invoice INV-2024-0091 payment posted. {execution.get('execution_report', '')}",
            "severity": "low",
            "vendor": "Vendor Corp",
            "invoice": "INV-2024-0091",
        }}
    )


def _audit_input(ctx, inp):
    all_events = []
    for s in ctx.values():
        if isinstance(s, dict):
            all_events.extend(s.get("audit_events", []))
    return all_events, {}


INVOICE_TO_PAY_CONFIG = UseCaseConfig(
    name="Invoice-to-Pay Workflow",
    description=(
        "End-to-end invoice processing: email parsing → PDF ingestion → SAP PO matching → "
        "three-way validation → HITL approval → ERP payment posting → vendor notification → audit."
    ),
    langfuse_tags=["invoice-to-pay", "finance", "enterprise", "v4"],
    global_config={
        "environment": "production",
        "org_name": "Acme Enterprise Ltd",
    },
    steps=[
        StepDef(id="email_handler",     agent="email_handler",      label="Email Parsing & Classification",     layer=1, input_fn=_email_input),
        StepDef(id="pdf_ingestor",      agent="pdf_ingestor",       label="Invoice PDF Ingestion",              layer=2, input_fn=_pdf_input,          ),
        StepDef(id="sap",         agent="sap",          label="SAP PO Match & Validation",          layer=3, input_fn=_sap_input,          ),
        StepDef(id="reasoning",         agent="reasoning",          label="Three-Way Match Analysis",           layer=2, input_fn=_reasoning_input,     ),
        StepDef(id="hitl",              agent="hitl",               label="Finance Controller Approval",         layer=3, input_fn=_hitl_input,         ),
        StepDef(id="execution",         agent="execution",          label="ERP Payment Posting",                layer=3, input_fn=_execution_input,     ),
        StepDef(id="notification",agent="notification", label="Vendor Payment Notification",        layer=2, input_fn=_notification_input,  ),
        StepDef(id="audit",             agent="audit",              label="AP Compliance Audit",                layer=3, input_fn=_audit_input,         optional=True),
    ],
)
