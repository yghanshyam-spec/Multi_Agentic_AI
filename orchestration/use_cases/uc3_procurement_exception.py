"""
orchestration/use_cases/uc3_procurement_exception.py
======================================================
Use Case 3 — Procurement Exception & Vendor Dispute Resolution

Business Context:
  A vendor emails to dispute a goods receipt quantity discrepancy on PO-4500009876.
  They received payment for 80 units but claim they delivered 100. The workflow:
  parses the dispute email, pulls PO/GR data from SAP, uses reasoning to evaluate
  evidence, routes to a procurement manager for approval of any credit note,
  executes the correction in SAP, notifies the vendor, and leaves a full audit trail.

Agents Used (9/21):
  router           → entry dispatch + final synthesis
  email_handler    → parse vendor dispute email + extract structured claim
  sap_agent        → query PO + GR status from SAP MM module
  reasoning        → evaluate discrepancy evidence: PO vs GR vs invoice
  hitl             → procurement manager approval for credit note issuance
  execution        → post corrective BAPI in SAP (BAPI_GOODSMVT_CANCEL / credit note)
  communication    → draft and send resolution reply to vendor
  notification_agent → alert category manager + AP team of resolution
  audit            → regulatory + SOX compliance trail of all financial transactions

Pipeline Layers:
  Layer 0: router
  Layer 1: email_handler
  Layer 2: sap_agent → reasoning
  Layer 3: hitl → execution → communication, notification_agent, audit
"""
from __future__ import annotations
from orchestration.pipeline import UseCaseConfig, StepDef

USE_CASE_PROMPT = (
    "Vendor dispute received: Vendor Corp (vendor ID: 0000100045) has emailed to dispute "
    "PO-4500009876. They claim 100 units of Item 10 (SKU: COMP-GPU-4090) were delivered "
    "on 2025-02-28 but only 80 units are shown in the goods receipt (GR-5000012345) "
    "posted in SAP. The invoice INV-2025-0042 was paid for 80 units at £850/unit = £68,000. "
    "Vendor requests credit for the missing 20 units (£17,000) or correction of the GR.\n"
    "Please:\n"
    "  1. Parse the dispute email and extract the structured claim\n"
    "  2. Pull PO, GR, and invoice data from SAP MM to verify both sides\n"
    "  3. Reason over the evidence to determine if the claim is valid\n"
    "  4. Get procurement manager approval before posting any correction\n"
    "  5. Post the corrective transaction in SAP (credit note or GR amendment)\n"
    "  6. Reply to the vendor with the resolution outcome\n"
    "  7. Notify the category manager and AP team of the resolution\n"
    "  8. Log the full audit trail for SOX compliance"
)


# ── Input functions ──────────────────────────────────────────────────────────

def _router_input(ctx, inp):
    return inp, {}


def _email_input(ctx, inp):
    return (
        "Parse vendor dispute email from ap@vendorcorp.com regarding PO-4500009876. "
        "Extract: vendor_id, po_number, gr_number, invoice_number, claimed_quantity, "
        "paid_quantity, unit_price, disputed_amount, dispute_reason.",
        {
            "agent_config": {
                "mailbox": {"protocol": "mock"},
                "reply_tone": "professional",
                "org_name": "Acme Procurement",
            }
        },
    )


def _sap_input(ctx, inp):
    email = ctx.get("email_handler", {})
    entities = email.get("email_entities", {})
    return (
        "Query SAP MM for PO-4500009876: retrieve line items, confirmed quantities, "
        "goods receipt GR-5000012345 quantities, and invoice verification status. "
        "Also check if any open quantity discrepancy exists on the PO.",
        {
            "agent_config": {
                "sap": {"module": "MM"},
            }
        },
    )


def _reasoning_input(ctx, inp):
    sap   = ctx.get("sap", {})
    email = ctx.get("email_handler", {})
    return (
        "Evaluate vendor quantity discrepancy claim:\n"
        f"Vendor claims: 100 units delivered, but GR shows 80 units posted.\n"
        f"SAP PO data: {sap.get('sap_summary', 'PO-4500009876 retrieved: 100 units ordered')}\n"
        f"Email entities: {email.get('email_entities', {})}\n"
        "Questions to reason through:\n"
        "  1. Is the vendor's claimed delivery quantity supported by PO quantity?\n"
        "  2. Could the GR undercount be a system entry error or a genuine short delivery?\n"
        "  3. What is the financial exposure of accepting the claim (£17,000)?\n"
        "  4. What corrective action is most appropriate: credit note or GR amendment?\n"
        "  5. Does this require human approval given the amount threshold (>£5,000)?",
        {},
    )


def _hitl_input(ctx, inp):
    reasoning = ctx.get("reasoning", {})
    sap       = ctx.get("sap", {})
    conclusion = (reasoning.get("conclusion") or {}).get("conclusion", "Claim appears valid")
    return (
        "Approve corrective transaction for vendor dispute PO-4500009876",
        {
            "working_memory": {
                "risk": "medium",
                "execution_plan": {
                    "script": (
                        "BAPI_GOODSMVT_CREATE: post quantity correction +20 units on "
                        "GR-5000012345, then trigger credit note for £17,000 to vendor 0000100045"
                    ),
                    "target": "SAP MM + FI modules",
                    "expected_outcome": "GR corrected to 100 units; credit note £17,000 posted",
                    "rollback": "BAPI_GOODSMVT_CANCEL correction document",
                },
                "reasoning_conclusion": conclusion,
                "financial_impact": "£17,000 credit note to Vendor Corp",
                "sap_po_status": sap.get("sap_summary", ""),
            }
        },
    )


def _execution_input(ctx, inp):
    hitl = ctx.get("hitl", {})
    return (
        "Post GR quantity correction and vendor credit note in SAP",
        {
            "execution_plan": {
                "script": (
                    "sap_correction.py --bapi=BAPI_GOODSMVT_CREATE "
                    "--gr=GR-5000012345 --qty-delta=+20 "
                    "--credit-note-amount=17000 --vendor=0000100045 --currency=GBP"
                ),
                "target": "SAP MM + FI",
                "expected_outcome": "GR corrected; credit note FI-CN-2025-001 posted",
                "requires_approval": True,
                "rollback": "reverse_correction.py --gr=GR-5000012345",
            },
            "approved_by": hitl.get("approver_id", "procurement_manager"),
        },
    )


def _communication_input(ctx, inp):
    execution = ctx.get("execution", {})
    hitl      = ctx.get("hitl", {})
    return (
        "Draft resolution reply to vendor ap@vendorcorp.com for dispute PO-4500009876",
        {
            "channel": "email",
            "working_memory": {
                "recipient": "ap@vendorcorp.com",
                "subject": "RE: Quantity Discrepancy — PO-4500009876 — Resolution",
                "resolution_outcome": (
                    "Discrepancy validated. GR amended to 100 units. "
                    f"Credit note for £17,000 posted. "
                    f"Execution status: {execution.get('status', 'COMPLETED')}."
                ),
                "approval_by": hitl.get("approver_id", "procurement_manager"),
                "incident_summary": inp,
            },
        },
    )


def _notification_input(ctx, inp):
    execution = ctx.get("execution", {})
    return (
        "Alert category manager and AP team of vendor dispute resolution",
        {
            "event_payload": {
                "type": "VENDOR_DISPUTE_RESOLVED",
                "source": "procurement_exception_workflow",
                "severity": "medium",
                "details": (
                    "Vendor Dispute PO-4500009876 resolved. "
                    "GR-5000012345 corrected +20 units. Credit note £17,000 issued. "
                    f"Execution: {execution.get('status', 'COMPLETED')}"
                ),
                "recipients": ["category_manager@company.com", "ap_team@company.com"],
                "po_number": "PO-4500009876",
                "financial_impact": "£17,000",
            }
        },
    )


def _audit_input(ctx, inp):
    events = []
    for s in ctx.values():
        if isinstance(s, dict):
            events.extend(s.get("audit_events", []))
    return events, {}


def _router_final_input(ctx, inp):
    partial = []
    for sid, sstate in ctx.items():
        if isinstance(sstate, dict) and sstate.get("agent_response"):
            partial.append({"agent": sid.upper(), "result": str(sstate.get("agent_response", {}))[:200]})
    return inp, {"partial_results": partial}


# ── Config ───────────────────────────────────────────────────────────────────

UC3_PROCUREMENT_EXCEPTION_CONFIG = UseCaseConfig(
    name="Procurement Exception & Vendor Dispute Resolution",
    description=(
        "End-to-end vendor dispute pipeline: email parsing → SAP PO/GR data pull → "
        "reasoning-based claim evaluation → manager HITL approval → SAP correction posting → "
        "vendor resolution reply → AP team notification → SOX-compliant audit trail."
    ),
    langfuse_tags=["procurement", "sap", "vendor-dispute", "finance", "sox", "uc3"],
    global_config={
        "environment": "production",
        "org_name": "Acme Procurement Ltd",
        "sox_reporting": True,
    },
    steps=[
        StepDef(id="router",             agent="router",            label="Entry Router — Dispute Dispatch",          layer=0, input_fn=_router_input),
        StepDef(id="email_handler",      agent="email_handler",     label="Vendor Dispute Email Parsing",             layer=1, input_fn=_email_input,         ),
        StepDef(id="sap",          agent="sap",         label="SAP PO/GR Data Retrieval",                 layer=2, input_fn=_sap_input,           ),
        StepDef(id="reasoning",          agent="reasoning",         label="Discrepancy Evidence Evaluation",          layer=2, input_fn=_reasoning_input,      ),
        StepDef(id="hitl",               agent="hitl",              label="Procurement Manager Approval",             layer=3, input_fn=_hitl_input,           ),
        StepDef(id="execution",          agent="execution",         label="SAP Corrective Transaction Posting",       layer=3, input_fn=_execution_input,      ),
        StepDef(id="communication",      agent="communication",     label="Vendor Resolution Reply",                  layer=3, input_fn=_communication_input,  ),
        StepDef(id="notification", agent="notification", label="AP Team & Manager Alert",                layer=3, input_fn=_notification_input,   ),
        StepDef(id="audit",              agent="audit",             label="SOX Compliance Audit Trail",               layer=3, input_fn=_audit_input,          optional=True),
        StepDef(id="router_final",       agent="router",            label="Router — Final Resolution Synthesis",      layer=0, input_fn=_router_final_input,   ),
    ],
)
