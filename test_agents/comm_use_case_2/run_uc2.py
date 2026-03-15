#!/usr/bin/env python3
"""
test_agents/use_case_2/run_uc2.py
===============================================================================
Console Test Application -- Use Case 2: Internal Broadcast Drafting
===============================================================================
WORKFLOW
  Communications manager provides bullet-point talking points ->
  Agent drafts channel-specific versions (email, Slack, memo) adapting
  tone and length per channel while preserving factual consistency and
  flagging any contradictions across the multi-channel outputs.

MODES
  --interactive     Enter talking points interactively (default)
  --scenarios       Run all test_scenarios.yaml
  --scenario-id ID  Run one scenario
  --demo            Policy change broadcast demo

QUICK START (from communication/ root)
  python test_agents/use_case_2/run_uc2.py
  python test_agents/use_case_2/run_uc2.py --scenarios
  python test_agents/use_case_2/run_uc2.py --demo
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

_SCRIPT_DIR = Path(__file__).resolve().parent
_AGENT_ROOT  = _SCRIPT_DIR.parents[1]
if str(_AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(_AGENT_ROOT))

from dotenv import load_dotenv
_ENV_FILE = _SCRIPT_DIR / ".env"
if _ENV_FILE.exists():
    load_dotenv(_ENV_FILE, override=True)

from agents.communication.core.engine import CommunicationAgentEngine
from agents.communication.schemas.output_models import AgentResponse, BroadcastResponse
from agents.communication.utils.logger import get_logger

logger = get_logger("uc2_runner")

_CONFIG_PATH    = str(_SCRIPT_DIR / "agent_config.yaml")
_SCENARIOS_PATH = _SCRIPT_DIR / "test_scenarios.yaml"
WORKFLOW        = "broadcast_drafting"

BANNER = """
+==============================================================================+
|     COMMUNICATION AGENT  .  USE CASE 2  .  INTERNAL BROADCAST DRAFTING     |
|                                                                              |
|  Turns bullet-point talking points into multi-channel communications.       |
|  For each broadcast the agent will:                                          |
|    (1) Parse and normalise the talking points input                          |
|    (2) Load any prior broadcast context                                      |
|    (3) Draft a version for EACH target channel (email / Slack / memo)        |
|           - Email: professional paragraphs with greeting and signature       |
|           - Slack: concise bullets, emoji-friendly, conversational           |
|           - Memo: formal TO/FROM/DATE/RE sections, numbered paragraphs       |
|    (4) Check all drafts are factually consistent with each other             |
|    (5) Flag any contradictions introduced during adaptation                  |
|    (6) Dispatch each version to its channel adapter                          |
|    (7) Persist all drafts and delivery metadata                              |
+==============================================================================+
"""

CHANNEL_ICONS = {
    "email": "[EMAIL]", "slack": "[SLACK]", "memo": "[MEMO]",
    "teams": "[TEAMS]", "api": "[API]",
}
CONSISTENCY_OK   = "\033[32m[CONSISTENT]\033[0m"
CONSISTENCY_WARN = "\033[31m[INCONSISTENCY DETECTED]\033[0m"


# def _ensure_cwd():
#     if not (Path.cwd() / "config" / "workflows" / "broadcast_drafting.yaml").exists():
#         if (_AGENT_ROOT / "config" / "workflows" / "broadcast_drafting.yaml").exists():
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
    print(f"  BROADCAST DRAFTING RESULT {label}")
    print("=" * w)
    status = "[OK]  SUCCESS" if result.success else "[FAIL] FAILED"
    print(f"  Status          : {status}")

    if isinstance(result, BroadcastResponse):
        cons_str = CONSISTENCY_OK if result.is_consistent else CONSISTENCY_WARN
        print(f"  Channels        : {', '.join(result.target_channels)}")
        print(f"  Drafts Created  : {len(result.channel_drafts)}")
        print(f"  Consistency     : {cons_str}")
        if not result.is_consistent and result.contradictions:
            print(f"\n  CONTRADICTIONS DETECTED:")
            for c in result.contradictions:
                print(f"    ! {c}")
        if result.dispatch_results:
            print(f"\n  Dispatch Summary:")
            for dr in result.dispatch_results:
                ch = dr.get("channel", "?")
                icon = CHANNEL_ICONS.get(ch, "[?]")
                print(f"    {icon} {ch:<8} -- status: {dr.get('status')} | "
                      f"id: {dr.get('delivery_id', 'N/A')}")
        print(f"  Audit ID        : {(result.audit_id or 'N/A')[:16]}")
        print(f"  Trace ID        : {(result.trace_id or 'N/A')[:16]}")

        # Print each channel draft
        for draft in result.channel_drafts:
            ch     = draft.get("channel", "?")
            icon   = CHANNEL_ICONS.get(ch, "[?]")
            words  = draft.get("word_count", 0)
            tone   = draft.get("tone", "")
            is_con = draft.get("is_consistent", True)
            con_tag = "" if is_con else " [INCONSISTENT]"
            content = draft.get("content", "")

            print(f"\n  {'-'*74}")
            print(f"  {icon} {ch.upper()} DRAFT  ({words} words | tone: {tone}){con_tag}")
            print(f"  {'-'*74}")
            for line in content.split("\n")[:25]:
                print(f"  {line}")
            if len(content.split("\n")) > 25:
                print(f"  ... [{len(content.split(chr(10)))-25} more lines]")
    else:
        print(f"\n  {result.message}")

    print("=" * w)


def run_interactive(engine: CommunicationAgentEngine):
    print(BANNER)
    print("  Enter talking points (multi-line OK -- finish with a blank line).")
    print("  Commands: 'demo' | 'channels' (change target) | 'quit'\n")

    target_channels = ["email", "slack", "memo"]
    session_id = str(uuid.uuid4())
    count = 0

    while True:
        print(f"  Target channels: {' | '.join(target_channels)}")
        print(f"  Session: {session_id[:16]}...")

        lines = []
        try:
            first = input("  Talking points > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye!\n"); break

        if not first:
            continue
        if first.lower() in ("quit", "exit", "q"):
            print("\n  Goodbye!\n"); break
        if first.lower() == "demo":
            run_demo(engine); break
        if first.lower() == "channels":
            print("  Available: email | slack | memo | teams | api")
            raw = input("  Enter channels (comma-separated) > ").strip()
            if raw:
                target_channels = [c.strip() for c in raw.split(",")]
                print(f"  Channels updated: {target_channels}\n")
            continue

        lines.append(first)
        try:
            while True:
                line = input("  ... > ").strip()
                if not line:
                    break
                lines.append(line)
        except (EOFError, KeyboardInterrupt):
            pass

        talking_points = "\n".join(lines)
        count += 1
        print(f"\n  Drafting for {len(target_channels)} channel(s)...\n")
        t0 = time.perf_counter()
        result = engine.run(
            workflow=WORKFLOW,
            user_message=talking_points,
            session_id=session_id,
            talking_points=talking_points,
            target_channels=target_channels,
            metadata={"runner": "interactive"},
        )
        _print_result(result, f"[Broadcast #{count}]")
        print(f"\n  Completed in {time.perf_counter()-t0:.2f}s\n")
        try:
            cont = input("  Draft another broadcast? (yes/no) > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            cont = "no"
        if cont not in ("yes", "y"):
            print("\n  Goodbye!\n"); break


def _evaluate(result: AgentResponse, s: Dict[str, Any]) -> tuple:
    exp = s.get("expected", {})
    fails = []
    if not result.success:
        fails.append("expected success=True")
    if isinstance(result, BroadcastResponse):
        exp_count = exp.get("draft_count")
        if exp_count and len(result.channel_drafts) != exp_count:
            fails.append(f"draft_count: expected {exp_count}, got {len(result.channel_drafts)}")
        if exp.get("is_consistent") and not result.is_consistent:
            fails.append("expected is_consistent=True")
    return len(fails) == 0, fails


def run_scenarios(engine: CommunicationAgentEngine, target_id=None) -> int:
    scenarios = yaml.safe_load(_SCENARIOS_PATH.read_text(encoding="utf-8")).get("scenarios", [])
    if target_id:
        scenarios = [s for s in scenarios if s["id"] == target_id]
    if not scenarios:
        print("  No scenarios found."); return 0

    print(BANNER)
    print(f"  Running {len(scenarios)} scenario(s)\n")
    rows = []
    for idx, s in enumerate(scenarios, 1):
        print(f"\n{'-'*78}")
        print(f"  SCENARIO {idx}/{len(scenarios)}: {s['id']} -- {s['description']}")
        channels = s.get("target_channels", ["email", "slack", "memo"])
        print(f"  Channels: {', '.join(channels)}")
        tp = s.get("talking_points", "")
        print(f"  Talking points: {tp[:60]}...")
        print("-"*78)
        session_id = f"UC2-{s['id']}-{uuid.uuid4().hex[:6].upper()}"
        t0 = time.perf_counter()
        result = engine.run(
            workflow=WORKFLOW,
            user_message=tp,
            session_id=session_id,
            talking_points=tp,
            target_channels=channels,
            metadata={"runner": "scenario", "id": s["id"]},
        )
        elapsed = time.perf_counter() - t0
        _print_result(result, f"[{s['id']}]")
        passed, fails = _evaluate(result, s)
        rows.append({
            "id": s["id"], "passed": passed, "fails": fails, "elapsed": elapsed,
            "channels": channels,
            "draft_count": len(getattr(result, "channel_drafts", [])),
            "is_consistent": getattr(result, "is_consistent", True),
            "contradictions": len(getattr(result, "contradictions", [])),
        })
        print(f"\n  {'[OK]' if passed else '[WARN]'} {s['id']} -- "
              f"{'PASSED' if passed else 'ASSERTIONS FAILED'} ({elapsed:.2f}s)")
        for f in fails:
            print(f"     * {f}")

    print(f"\n\n{'='*78}")
    print("  SUMMARY -- Use Case 2: Internal Broadcast Drafting")
    print("="*78)
    print(f"  {'ID':<14} {'Channels':<20} {'Drafts':<7} {'Consist.':<12} {'Status':<8} {'Time':>6}")
    print(f"  {'-'*13} {'-'*19} {'-'*6} {'-'*11} {'-'*7} {'-'*6}")
    for r in rows:
        st   = "PASS" if r["passed"] else "FAIL"
        cons = "OK" if r["is_consistent"] else f"WARN({r['contradictions']})"
        chs  = ",".join(r["channels"])[:18]
        print(f"  {r['id']:<14} {chs:<20} {r['draft_count']:<7} {cons:<12} {st:<8} {r['elapsed']:>5.2f}s")
    total, passed_n = len(rows), sum(1 for r in rows if r["passed"])
    print(f"\n  Total: {total}  |  Passed: {passed_n}  |  Failed: {total-passed_n}")
    print("="*78)
    return 0 if total == passed_n else 1


def run_demo(engine: CommunicationAgentEngine):
    print(BANNER)
    print("  DEMO: Work-from-home policy change broadcast\n")
    talking_points = """\
- Effective March 1, 2025, all employees may work from home up to 3 days per week
- Office anchor days are Tuesday and Thursday (mandatory in-office for all staff)
- Employees must notify their manager by Friday of each week with the WFH schedule
- Home office equipment allowance: $500 per employee (one-time, claim by June 30, 2025)
- Exceptions for manufacturing and facilities roles -- HR to communicate separately
- Questions: contact HR at hr@company.com or use the HR portal under My Benefits"""

    target_channels = ["email", "slack", "memo"]
    session_id = f"UC2-DEMO-{uuid.uuid4().hex[:8].upper()}"

    print(f"  Talking points:\n")
    for line in talking_points.split("\n"):
        print(f"  {line}")
    print(f"\n  Target channels: {', '.join(target_channels)}")
    print(f"  Session: {session_id}\n")
    print("  Drafting...\n")

    t0 = time.perf_counter()
    result = engine.run(
        workflow=WORKFLOW,
        user_message=talking_points,
        session_id=session_id,
        talking_points=talking_points,
        target_channels=target_channels,
        metadata={"runner": "demo"},
    )
    _print_result(result, "[WFH Policy Demo]")
    print(f"\n  Completed in {time.perf_counter()-t0:.2f}s")
    print("  Demo complete.\n")


def main():
    ap = argparse.ArgumentParser(description="Communication Agent -- UC2: Broadcast Drafting")
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
    print("\n  Initialising Communication Agent Engine (UC2)...")
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
