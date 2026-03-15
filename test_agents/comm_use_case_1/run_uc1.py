#!/usr/bin/env python3
"""
test_agents/use_case_1/run_uc1.py
===============================================================================
Console Test Application -- Use Case 1: Omnichannel Customer Response
===============================================================================
WORKFLOW
  Inbound message arrives on any channel (email, chat, voice, Slack, API) ->
  Agent detects channel, loads conversation history, classifies intent,
  drafts a channel-appropriate response, checks consistency with prior
  communications, dispatches the reply, and logs the full thread to CRM.

MODES
  --interactive     Type messages simulating any channel (default)
  --scenarios       Run all test_scenarios.yaml
  --scenario-id ID  Run one scenario
  --demo            3-message omnichannel demo (email -> chat -> voice)
  --thread-replay   Show stored thread history for a session

QUICK START (from communication/ root)
  python test_agents/use_case_1/run_uc1.py
  python test_agents/use_case_1/run_uc1.py --scenarios
  python test_agents/use_case_1/run_uc1.py --demo
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# -- Path setup --------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_AGENT_ROOT  = _SCRIPT_DIR.parents[1]
if str(_AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(_AGENT_ROOT))

from dotenv import load_dotenv
_ENV_FILE = _SCRIPT_DIR / ".env"
if _ENV_FILE.exists():
    load_dotenv(_ENV_FILE, override=True)

from communication.core.engine import CommunicationAgentEngine
from communication.schemas.output_models import AgentResponse, OmnichannelResponse
from communication.tools.communication_tools import ContextMemoryTool, AuditLogTool
from communication.utils.logger import get_logger

logger = get_logger("uc1_runner")

_CONFIG_PATH    = str(_SCRIPT_DIR / "agent_config.yaml")
_SCENARIOS_PATH = _SCRIPT_DIR / "test_scenarios.yaml"
WORKFLOW        = "omnichannel_response"

BANNER = """
+==============================================================================+
|     COMMUNICATION AGENT  .  USE CASE 1  .  OMNICHANNEL CUSTOMER RESPONSE   |
|                                                                              |
|  Handles customer messages across email, chat, Slack, voice & API.          |
|  For each message the agent will:                                            |
|    (1) Detect and normalise the inbound channel                              |
|    (2) Load conversation history (unified across all channels)               |
|    (3) Classify: automated response | human escalation | acknowledgement     |
|    (4) Draft a channel-appropriate response (tone + length adapted)          |
|    (5) Check consistency with prior thread communications                   |
|    (6) Dispatch the reply to the correct channel adapter                     |
|    (7) Persist history and log interaction to CRM                            |
+==============================================================================+
"""

CHANNELS_INFO = """
  SUPPORTED CHANNELS (all mocked by default):
    email   -- SMTP / SendGrid  |  chat  -- WebSocket / REST
    slack   -- Slack API        |  teams -- Microsoft Teams webhook
    api     -- REST callback    |  voice -- Phone transcript processing
"""

CHANNEL_ICONS = {
    "email": "[EMAIL]", "chat": "[CHAT]", "slack": "[SLACK]",
    "teams": "[TEAMS]", "api": "[API]", "voice": "[VOICE]", "memo": "[MEMO]",
}
PRIORITY_COLOURS = {
    "urgent": "\033[31m", "high": "\033[33m",
    "medium": "\033[32m", "low": "\033[36m",
}
RESET = "\033[0m"


# def _ensure_cwd():
#     if not (Path.cwd() / "config" / "workflows" / "omnichannel_response.yaml").exists():
#         if (_AGENT_ROOT / "config" / "workflows" / "omnichannel_response.yaml").exists():
#             os.chdir(_AGENT_ROOT)

def _ensure_cwd():
    if not (Path.cwd() / "config" / "workflows" / "omnichannel_response.yaml").exists():
        if (_SCRIPT_DIR / "config" / "workflows" / "omnichannel_response.yaml").exists():
            os.chdir(_SCRIPT_DIR)


def build_engine() -> CommunicationAgentEngine:
    _ensure_cwd()
    return CommunicationAgentEngine(config_path=_CONFIG_PATH, env_file=str(_ENV_FILE))


def _print_result(result: AgentResponse, label: str = ""):
    w = 78
    print(f"\n{'=' * w}")
    print(f"  OMNICHANNEL RESPONSE RESULT {label}")
    print("=" * w)
    status = "[OK]  SUCCESS" if result.success else "[FAIL] FAILED"
    print(f"  Status          : {status}")
    if isinstance(result, OmnichannelResponse):
        ch_icon = CHANNEL_ICONS.get(result.detected_channel or "", "[?]")
        print(f"  Detected Channel: {ch_icon} {result.detected_channel or 'unknown'}")
        print(f"  Reply Channel   : {CHANNEL_ICONS.get(result.reply_channel or '', '[?]')} {result.reply_channel or 'N/A'}")
        print(f"  Thread ID       : {result.thread_id or 'N/A'}")
        print(f"  Classification  : {result.classification or 'N/A'}")
        pri = result.priority or "medium"
        colour = PRIORITY_COLOURS.get(pri, "")
        print(f"  Priority        : {colour}{pri.upper()}{RESET}")
        print(f"  Sentiment       : {result.sentiment or 'N/A'}")
        print(f"  Requires Human  : {'YES -- ESCALATED' if result.requires_human else 'No -- Automated'}")
        print(f"  CRM Logged      : {'Yes' if result.crm_logged else 'No'}")
        if result.dispatch_results:
            dr = result.dispatch_results[0]
            print(f"  Dispatch Status : {dr.get('status')} | id: {dr.get('delivery_id', 'N/A')}")
        print(f"  Audit ID        : {(result.audit_id or 'N/A')[:16]}")
    print(f"  Trace ID        : {(result.trace_id or 'N/A')[:16]}")
    print(f"\n  DRAFTED RESPONSE:")
    print("  " + "-" * (w - 4))
    for line in result.message.split("\n")[:20]:
        print(f"  {line}")
    print("=" * w)


def run_interactive(engine: CommunicationAgentEngine):
    print(BANNER)
    print(CHANNELS_INFO)
    session_id = str(uuid.uuid4())
    count = 0
    print(f"  Session ID: {session_id}")
    print(f"  (Messages in the same session share conversation history)\n")
    print("  Commands: 'channel' (change channel) | 'history' (show thread) | 'quit'\n")

    current_channel = "email"
    current_sender  = "customer@example.com"

    while True:
        try:
            user_input = input(f"  [{current_channel.upper()}] Message > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye!\n"); break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("\n  Goodbye!\n"); break
        if user_input.lower() == "history":
            _show_history(session_id); continue
        if user_input.lower() == "channel":
            print("  Channels: email | chat | slack | teams | api | voice")
            ch = input("  New channel > ").strip().lower()
            if ch:
                current_channel = ch
                print(f"  Channel changed to: {current_channel}\n")
            continue

        count += 1
        payload = {
            "channel":      current_channel,
            "sender":       current_sender,
            "sender_email": current_sender,
            "subject":      f"Customer enquiry #{count}",
            "body":         user_input,
            "thread_id":    session_id,
        }
        print(f"\n  Processing via {current_channel.upper()}...\n")
        t0 = time.perf_counter()
        result = engine.run(
            workflow=WORKFLOW,
            user_message=user_input,
            session_id=session_id,
            inbound_payload=payload,
            metadata={"runner": "interactive"},
        )
        _print_result(result)
        print(f"\n  Completed in {time.perf_counter()-t0:.2f}s\n")

        try:
            cont = input("  Continue conversation? (yes/no) > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            cont = "no"
        if cont not in ("yes", "y"):
            print("\n  Goodbye!\n"); break


def _show_history(session_id: str):
    memory = ContextMemoryTool()
    history = memory.load(session_id)
    if not history:
        print("  No history found for this session.\n")
        return
    print(f"\n  Thread History ({len(history)} entries):")
    print("  " + "-" * 60)
    for i, entry in enumerate(history, 1):
        role    = entry.get("role", "?")
        channel = entry.get("channel", "?")
        content = entry.get("content", "")[:80]
        print(f"  {i:2}. [{channel}/{role}]: {content}")
    print()


def _evaluate(result: AgentResponse, s: Dict[str, Any]):
    exp = s.get("expected", {})
    fails = []
    if not result.success:
        fails.append("expected success=True")
    if isinstance(result, OmnichannelResponse):
        if exp.get("requires_human") and not result.requires_human:
            fails.append(f"expected requires_human=True")
        if exp.get("classification") and result.classification != exp["classification"]:
            fails.append(f"classification: expected {exp['classification']}, got {result.classification}")
        if exp.get("priority") and result.priority != exp.get("priority"):
            fails.append(f"priority: expected {exp['priority']}, got {result.priority}")
    return len(fails) == 0, fails


def run_scenarios(engine: CommunicationAgentEngine, target_id=None) -> int:
    scenarios = yaml.safe_load(_SCENARIOS_PATH.read_text(encoding="utf-8")).get("scenarios", [])
    if target_id:
        scenarios = [s for s in scenarios if s["id"] == target_id]
    if not scenarios:
        print("  No scenarios found."); return 0
    print(BANNER)
    print(f"  Running {len(scenarios)} scenario(s) -- shared thread for multi-channel continuity\n")
    # Group by session (use first scenario's sender as thread anchor)
    session_id = str(uuid.uuid4())
    rows = []
    for idx, s in enumerate(scenarios, 1):
        print(f"\n{'-'*78}")
        print(f"  SCENARIO {idx}/{len(scenarios)}: {s['id']} -- {s['description']}")
        ch = s.get("channel", "email")
        print(f"  Channel: {CHANNEL_ICONS.get(ch, '[?]')} {ch}")
        print(f"  Message: \"{(s.get('body',''))[:70]}\"")
        print("-"*78)

        payload = {
            "channel":      s.get("channel", "email"),
            "sender":       s.get("sender", "test@example.com"),
            "sender_email": s.get("sender_email", s.get("sender", "test@example.com")),
            "subject":      s.get("subject", "Test scenario"),
            "body":         s.get("body", ""),
            "thread_id":    session_id,
        }
        t0 = time.perf_counter()
        result = engine.run(
            workflow=WORKFLOW,
            user_message=s.get("body", ""),
            session_id=session_id,
            inbound_payload=payload,
            metadata={"runner": "scenario", "id": s["id"]},
        )
        elapsed = time.perf_counter() - t0
        _print_result(result, f"[{s['id']}]")
        passed, fails = _evaluate(result, s)
        rows.append({
            "id": s["id"], "passed": passed, "fails": fails,
            "elapsed": elapsed, "channel": ch,
            "classification": getattr(result, "classification", "?"),
            "priority": getattr(result, "priority", "?"),
            "requires_human": getattr(result, "requires_human", False),
        })
        print(f"\n  {'[OK]' if passed else '[WARN]'} {s['id']} -- "
              f"{'PASSED' if passed else 'ASSERTIONS FAILED'} ({elapsed:.2f}s)")
        for f in fails:
            print(f"     * {f}")

    # Summary
    print(f"\n\n{'='*78}")
    print("  SUMMARY -- Use Case 1: Omnichannel Customer Response")
    print("="*78)
    print(f"  {'ID':<14} {'Channel':<8} {'Class.':<22} {'Pri.':<8} {'Esc.':<6} {'Status':<8} {'Time':>6}")
    print(f"  {'-'*13} {'-'*7} {'-'*21} {'-'*7} {'-'*5} {'-'*7} {'-'*6}")
    for r in rows:
        st = "PASS" if r["passed"] else "FAIL"
        esc = "YES" if r["requires_human"] else "No"
        print(f"  {r['id']:<14} {r['channel']:<8} {(r['classification'] or '?'):<22} "
              f"{(r['priority'] or '?'):<8} {esc:<6} {st:<8} {r['elapsed']:>5.2f}s")
    total, passed_n = len(rows), sum(1 for r in rows if r["passed"])
    print(f"\n  Total: {total}  |  Passed: {passed_n}  |  Failed: {total-passed_n}")
    print(f"  CRM Entries: {len(rows)}  |  Thread: {session_id[:16]}...")
    print("="*78)
    return 0 if total == passed_n else 1


def run_demo(engine: CommunicationAgentEngine):
    """3-message omnichannel demo simulating a real customer journey."""
    print(BANNER)
    print(CHANNELS_INFO)
    print("  DEMO: 3-message omnichannel journey -- Email -> Chat -> Voice escalation\n")
    session_id = str(uuid.uuid4())

    demo_messages = [
        {
            "step": "1/3 -- Initial email complaint",
            "payload": {
                "channel": "email",
                "sender": "sarah.jones@example.com",
                "sender_email": "sarah.jones@example.com",
                "subject": "Billing error on my account",
                "body": (
                    "Hi, I've been charged twice for my subscription this month. "
                    "My account shows two charges of $49.99 on the 15th and 16th. "
                    "Please refund the duplicate charge immediately. "
                    "Order reference: SUB-2024-8812.\n\nRegards, Sarah Jones"
                ),
                "thread_id": session_id,
            },
        },
        {
            "step": "2/3 -- Follow-up chat (unresolved)",
            "payload": {
                "channel": "chat",
                "sender": "sarah.jones@example.com",
                "body": "I still haven't received the refund from my email earlier. It's been 3 hours.",
                "thread_id": session_id,
            },
        },
        {
            "step": "3/3 -- Voice transcript escalation",
            "payload": {
                "channel": "voice",
                "sender": "sarah.jones@example.com",
                "body": (
                    "Customer called stating duplicate billing issue from earlier today "
                    "is still unresolved. She has contacted her bank and is requesting "
                    "an immediate full refund or she will file a chargeback. "
                    "She mentioned consulting a lawyer if not resolved by end of day."
                ),
                "thread_id": session_id,
            },
        },
    ]

    for msg in demo_messages:
        print(f"\n  --- DEMO STEP {msg['step']} ---")
        ch = msg["payload"]["channel"]
        print(f"  Channel : {CHANNEL_ICONS.get(ch,'[?]')} {ch.upper()}")
        print(f"  Message : \"{msg['payload']['body'][:75]}...\"")
        print()
        t0 = time.perf_counter()
        result = engine.run(
            workflow=WORKFLOW,
            user_message=msg["payload"]["body"],
            session_id=session_id,
            inbound_payload=msg["payload"],
            metadata={"runner": "demo"},
        )
        _print_result(result, f"[Step {msg['step'][:3]}]")
        print(f"\n  Completed in {time.perf_counter()-t0:.2f}s")
        try:
            input("\n  Press ENTER for next step...\n")
        except (EOFError, KeyboardInterrupt):
            break

    # Show full thread
    print("\n  --- FULL THREAD HISTORY ---")
    _show_history(session_id)

    audit_entries = AuditLogTool.get_log()
    print(f"  Audit entries logged: {len(audit_entries)}")
    print("  Demo complete.\n")


def main():
    ap = argparse.ArgumentParser(description="Communication Agent -- UC1: Omnichannel Response")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--interactive", action="store_true")
    mode.add_argument("--scenarios", action="store_true")
    mode.add_argument("--scenario-id", metavar="ID")
    mode.add_argument("--demo", action="store_true")
    ap.add_argument("--log-level", choices=["DEBUG","INFO","WARNING","ERROR"])
    args = ap.parse_args()
    if args.log_level:
        os.environ["LOG_LEVEL"] = args.log_level

    _ensure_cwd()
    print("\n  Initialising Communication Agent Engine (UC1)...")
    t = time.perf_counter()
    engine = build_engine()
    print(f"  Engine ready ({time.perf_counter()-t:.2f}s)\n")

    code = 0
    if args.demo:
        run_demo(engine)
    elif args.scenarios or args.scenario_id:
        code = run_scenarios(engine, target_id=args.scenario_id)
    else:
        run_interactive(engine)
    sys.exit(code)


if __name__ == "__main__":
    main()
