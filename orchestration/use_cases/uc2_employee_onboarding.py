"""
orchestration/use_cases/uc2_employee_onboarding.py
====================================================
Use Case 2 — End-to-End Employee Onboarding Workflow

Business Context:
  HR triggers onboarding for a new software engineer joining the APAC office.
  The workflow: creates the SAP HR employee record, answers policy Q&A for the
  new joiner, provisions system accounts, books orientation meetings, and sends
  personalised status updates at every stage — with manager approval gating the
  account provisioning step.

Agents Used (10/21):
  planner          → decompose 8-week onboarding goal into sequenced tasks
  workflow         → orchestrate the full multi-step sequence
  pdf_ingestor     → ingest HR policy handbook into vector store
  vector_query     → answer new joiner policy Q&A (RAG)
  sap_agent        → create employee master record in SAP HR module
  email_handler    → parse manager's confirmation/welcome email
  scheduling_agent → book orientation session + buddy 1:1 meetings
  hitl             → manager approval before account provisioning
  execution        → provision AD/SSO/GitHub accounts via scripts
  notification_agent → send personalised status updates at each stage

Pipeline Layers:
  Layer 0: planner
  Layer 1: workflow, pdf_ingestor
  Layer 2: vector_query, sap_agent, email_handler
  Layer 3: scheduling_agent, hitl → execution, notification_agent, audit (optional)
"""
from __future__ import annotations
from orchestration.pipeline import UseCaseConfig, StepDef

USE_CASE_PROMPT = (
    "Onboard new employee: Priya Sharma, Software Engineer II, APAC (Singapore). "
    "Start date: 2025-03-17. Manager: David Chen (david.chen@company.com). "
    "Tasks required:\n"
    "  1. Decompose 8-week onboarding plan with dependencies\n"
    "  2. Ingest and index the HR Policy Handbook (PDF) for self-service Q&A\n"
    "  3. Answer Priya's first-day policy questions from the indexed handbook\n"
    "  4. Create SAP HR employee record (personnel number, cost centre SG-TECH-01)\n"
    "  5. Parse David's confirmation email and extract any special instructions\n"
    "  6. Get David's approval before provisioning system accounts\n"
    "  7. Provision AD account, GitHub org membership, SSO role\n"
    "  8. Book 60-min orientation session and buddy 1:1 in first week\n"
    "  9. Send Priya personalised updates at every stage\n"
    " 10. Orchestrate all steps in dependency order"
)


# ── Input functions ──────────────────────────────────────────────────────────

def _planner_input(ctx, inp):
    return (
        "Plan 8-week employee onboarding for Priya Sharma (Software Engineer II, Singapore). "
        "Decompose into: HR record creation, policy Q&A setup, system account provisioning, "
        "orientation scheduling, training assignment, buddy programme, 30/60/90 day checkpoints. "
        "Tag each task with responsible agent type and dependencies.",
        {},
    )


def _pdf_input(ctx, inp):
    return (
        "Ingest HR Policy Handbook into document store for new joiner self-service Q&A",
        {
            "pdf_path": "hr_policy_handbook_v2025.pdf",
            "agent_config": {
                "chunk_size": 600,
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                "vector_store": {"table": "hr_policies", "type": "pgvector"},
            },
        },
    )


def _vector_query_input(ctx, inp):
    pdf = ctx.get("pdf_ingestor", {})
    chunks_created = pdf.get("chunk_count", 0)
    return (
        "What is the annual leave entitlement for a Singapore-based Software Engineer? "
        "What are the equipment request procedures? What is the probation period policy?",
        {
            "agent_config": {
                "vector_store": {"table": "hr_policies", "type": "pgvector"},
                "top_k": 5,
                "filters": {"min_score": 0.6},
            }
        },
    )


def _sap_input(ctx, inp):
    return (
        "Create new employee record in SAP HR for Priya Sharma: "
        "Employee ID TBD, Job Title Software Engineer II, "
        "Cost Centre SG-TECH-01, Company Code SGAP, "
        "Start Date 20250317, Location Singapore, "
        "Employment Type Permanent, Pay Grade L4",
        {
            "agent_config": {
                "sap": {
                    "module": "HR",
                    "bapi": "BAPI_EMPLOYEE_CREATE",
                },
            }
        },
    )


def _email_input(ctx, inp):
    return (
        "Process manager confirmation email from david.chen@company.com "
        "regarding new joiner Priya Sharma — extract any special equipment requests, "
        "access level overrides, or onboarding notes.",
        {
            "agent_config": {
                "mailbox": {"protocol": "mock"},
                "reply_tone": "professional",
                "org_name": "Acme APAC",
            }
        },
    )


def _hitl_input(ctx, inp):
    sap    = ctx.get("sap", {})
    email  = ctx.get("email_handler", {})
    doc_no = sap.get("sap_raw_result", {}).get("DOCUMENT_NUMBER", "HR-EMP-001")
    notes  = email.get("email_entities", {})
    return (
        "Approve system account provisioning for new employee Priya Sharma",
        {
            "working_memory": {
                "risk": "low",
                "execution_plan": {
                    "script": (
                        "provision_accounts.py --user=priya.sharma "
                        "--ad-group=SG-ENGINEERING --github-org=acme-apac --sso-role=engineer-l4"
                    ),
                    "target": "identity_management_system",
                    "expected_outcome": "AD/SSO/GitHub accounts active within 10 min",
                },
                "sap_employee_number": doc_no,
                "manager_notes": str(notes),
            }
        },
    )


def _execution_input(ctx, inp):
    hitl = ctx.get("hitl", {})
    return (
        "Provision AD account, GitHub org membership, and SSO role for Priya Sharma",
        {
            "execution_plan": {
                "script": (
                    "provision_accounts.py --user=priya.sharma "
                    "--ad-group=SG-ENGINEERING --github-org=acme-apac --sso-role=engineer-l4"
                ),
                "target": "identity_management_system",
                "expected_outcome": "All three accounts provisioned and accessible",
                "requires_approval": True,
            },
            "approved_by": hitl.get("approver_id", "david_chen"),
        },
    )


def _scheduling_input(ctx, inp):
    exec_ = ctx.get("execution", {})
    return (
        "Schedule a 60-minute orientation session for Priya Sharma with the Singapore HR team "
        "on 2025-03-17 at 10:00 AM SGT. Also schedule a 30-minute buddy 1:1 with buddy "
        "Raj Kumar on 2025-03-18 at 2:00 PM SGT. Platform: Microsoft Teams.",
        {
            "agent_config": {
                "calendar": {"platform": "teams"},
            }
        },
    )


def _notification_input(ctx, inp):
    exec_  = ctx.get("execution", {})
    sched  = ctx.get("scheduling", {})
    return (
        "Send Priya Sharma personalised onboarding status update",
        {
            "event_payload": {
                "type": "ONBOARDING_UPDATE",
                "source": "hr_onboarding_workflow",
                "severity": "low",
                "details": (
                    "Welcome Priya! Your onboarding is underway. "
                    f"Accounts provisioned: {exec_.get('status','COMPLETED')}. "
                    f"Orientation meeting: {sched.get('scheduling_summary','booked for Mon 10AM')}. "
                    "Please check your email for credentials and calendar invites."
                ),
                "recipient": "priya.sharma@company.com",
            }
        },
    )


def _workflow_input(ctx, inp):
    planner = ctx.get("planner", {})
    return (
        "Orchestrate and verify completion of all onboarding tasks for Priya Sharma",
        {"workflow_plan": planner.get("workflow_plan")},
    )


# ── Config ───────────────────────────────────────────────────────────────────

UC2_EMPLOYEE_ONBOARDING_CONFIG = UseCaseConfig(
    name="End-to-End Employee Onboarding",
    description=(
        "Fully automated onboarding pipeline: HR record creation in SAP, policy handbook "
        "ingestion + RAG Q&A, system account provisioning (with manager HITL approval), "
        "orientation scheduling via Teams, and personalised status notifications."
    ),
    langfuse_tags=["hr", "onboarding", "sap", "scheduling", "uc2"],
    global_config={
        "environment": "production",
        "org_name": "Acme APAC Pte Ltd",
        "country": "Singapore",
    },
    steps=[
        StepDef(id="planner",          agent="planner",          label="Onboarding Plan Decomposition",     layer=0, input_fn=_planner_input),
        StepDef(id="pdf_ingestor",     agent="pdf_ingestor",     label="HR Policy Handbook Ingestion",      layer=1, input_fn=_pdf_input,         ),
        StepDef(id="vector_query",     agent="vector_query",     label="Policy Q&A for New Joiner",         layer=2, input_fn=_vector_query_input),
        StepDef(id="sap",        agent="sap",        label="SAP HR Employee Record Creation",   layer=2, input_fn=_sap_input,          ),
        StepDef(id="email_handler",    agent="email_handler",    label="Manager Confirmation Email Parse",  layer=2, input_fn=_email_input,        ),
        StepDef(id="hitl",             agent="hitl",             label="Manager Approval for Provisioning", layer=3, input_fn=_hitl_input,         ),
        StepDef(id="execution",        agent="execution",        label="System Account Provisioning",       layer=3, input_fn=_execution_input,    ),
        StepDef(id="scheduling", agent="scheduling", label="Orientation & Buddy Meeting Booking", layer=3, input_fn=_scheduling_input),
        StepDef(id="notification", agent="notification", label="New Joiner Status Notification", layer=3, input_fn=_notification_input),
        StepDef(id="workflow",         agent="workflow",         label="Onboarding Workflow Orchestration", layer=1, input_fn=_workflow_input,     ),
    ],
)
