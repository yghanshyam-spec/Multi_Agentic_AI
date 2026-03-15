"""
tests/test_pipeline.py
======================
Unit + integration tests for all 10 agent accelerators.
Run with: python -m pytest tests/ -v
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from shared.state import (
    make_base_state, build_agent_response, make_audit_event,
    AgentType, ExecutionStatus, new_id,
)
from shared.llm_factory import MockLLM, call_llm


# ─────────────────────────────────────────────────────────────────────────────
# SHARED / STATE TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestBaseState:
    def test_make_base_state(self):
        state = make_base_state("test input", AgentType.SCHEDULER)
        assert state["raw_input"] == "test input"
        assert state["agent_type"] == AgentType.SCHEDULER
        assert state["status"] == ExecutionStatus.PENDING
        assert state["retry_count"] == 0
        assert isinstance(state["audit_events"], list)
        assert isinstance(state["execution_trace"], list)

    def test_build_agent_response(self):
        state = make_base_state("test", AgentType.REASONING)
        resp = build_agent_response(state, payload={"result": "ok"}, confidence_score=0.9)
        assert resp["status"] == ExecutionStatus.PENDING
        assert resp["payload"]["result"] == "ok"
        assert resp["confidence"]["score"] == 0.9
        assert resp["confidence"]["level"] == "high"
        assert "response_id" in resp

    def test_audit_event(self):
        state = make_base_state("test", AgentType.AUDIT)
        evt = make_audit_event(state, "test_node", "TEST_ACTION")
        assert evt["node_name"] == "test_node"
        assert evt["action"] == "TEST_ACTION"
        assert evt["policy_ok"] is True


class TestMockLLM:
    def test_mock_llm_returns_dict(self):
        llm = MockLLM()
        result = call_llm(llm, "System prompt", "User prompt: analyse request", node_hint="analyse_request")
        assert isinstance(result, dict)

    def test_mock_llm_intent(self):
        llm = MockLLM()
        result = call_llm(llm, "Classify intent", "User: diagnose incident", node_hint="classify_intent")
        assert isinstance(result, dict)

    def test_mock_llm_plan(self):
        llm = MockLLM()
        result = call_llm(llm, "Decompose tasks", "Objective: fix incident", node_hint="decompose_tasks")
        assert isinstance(result, (dict, list))


# ─────────────────────────────────────────────────────────────────────────────
# AGENT UNIT TESTS
# ─────────────────────────────────────────────────────────────────────────────

INCIDENT = "Critical: Order Processing API latency 4200ms. DB CPU 94%. Orders table grew 4x."


class TestSchedulerAgent:
    def test_run(self):
        from agents.scheduler.graph import run_scheduler
        state = run_scheduler(INCIDENT)
        assert state["status"] == ExecutionStatus.COMPLETED
        assert state["agent_response"] is not None
        assert len(state.get("activated_agents", [])) > 0
        assert len(state.get("execution_trace", [])) > 0

    def test_audit_events_populated(self):
        from agents.scheduler.graph import run_scheduler
        state = run_scheduler(INCIDENT)
        assert len(state.get("audit_events", [])) >= 2


class TestIntentAgent:
    def test_run(self):
        from agents.intent.graph import run_intent_agent
        state = run_intent_agent(INCIDENT)
        assert state["status"] == ExecutionStatus.COMPLETED
        assert state.get("primary_intent") is not None
        assert len(state.get("detected_intents", [])) > 0
        assert len(state.get("sub_tasks", [])) > 0

    def test_entities_extracted(self):
        from agents.intent.graph import run_intent_agent
        state = run_intent_agent(INCIDENT)
        assert isinstance(state.get("extracted_entities"), dict)


class TestPlannerAgent:
    def test_run(self):
        from agents.planner.graph import run_planner_agent
        state = run_planner_agent(INCIDENT)
        assert state["status"] == ExecutionStatus.COMPLETED
        assert state.get("plan_id") is not None
        assert len(state.get("task_graph", [])) >= 3

    def test_execution_order(self):
        from agents.planner.graph import run_planner_agent
        state = run_planner_agent(INCIDENT)
        assert len(state.get("execution_order", [])) > 0

    def test_workflow_plan_serialised(self):
        from agents.planner.graph import run_planner_agent
        state = run_planner_agent(INCIDENT)
        wp = state.get("workflow_plan", {})
        assert "plan_id" in wp
        assert "tasks" in wp


class TestWorkflowAgent:
    def test_run_with_plan(self):
        from agents.planner.graph import run_planner_agent
        from agents.workflow.graph import run_workflow_agent
        planner_state = run_planner_agent(INCIDENT)
        wp = planner_state.get("workflow_plan", {})
        state = run_workflow_agent(INCIDENT, workflow_plan=wp)
        assert state["status"] == ExecutionStatus.COMPLETED
        assert state.get("workflow_summary") is not None

    def test_steps_completed(self):
        from agents.workflow.graph import run_workflow_agent
        state = run_workflow_agent(INCIDENT, workflow_plan={"tasks": [
            {"task_id": "T1", "title": "Diagnose", "agent": "REASONING_AGENT", "deps": []},
        ]})
        assert len(state.get("completed_steps", [])) >= 1


class TestReasoningAgent:
    def test_run(self):
        from agents.reasoning.graph import run_reasoning_agent
        state = run_reasoning_agent(INCIDENT)
        assert state["status"] == ExecutionStatus.COMPLETED
        assert state.get("conclusion") is not None
        assert len(state.get("reasoning_chain", [])) > 0

    def test_hypotheses_generated(self):
        from agents.reasoning.graph import run_reasoning_agent
        state = run_reasoning_agent(INCIDENT)
        assert len(state.get("hypotheses", [])) >= 1

    def test_reasoning_valid(self):
        from agents.reasoning.graph import run_reasoning_agent
        state = run_reasoning_agent(INCIDENT)
        assert state.get("reasoning_valid") is True


class TestGeneratorAgent:
    def test_run(self):
        from agents.generator.graph import run_generator_agent
        state = run_generator_agent("Generate incident report", working_memory={
            "incident_summary": INCIDENT,
            "root_cause": "Missing index",
            "resolution": "Index created",
        })
        assert state["status"] == ExecutionStatus.COMPLETED
        assert state.get("final_document") is not None
        assert len(state.get("generated_sections", [])) > 0

    def test_document_has_content(self):
        from agents.generator.graph import run_generator_agent
        state = run_generator_agent("Generate report")
        doc = state.get("final_document", "")
        assert len(doc) > 100


class TestCommunicationAgent:
    def test_run(self):
        from agents.communication.graph import run_communication_agent
        state = run_communication_agent("Notify stakeholders: incident resolved", channel="email")
        assert state["status"] == ExecutionStatus.COMPLETED
        assert state.get("draft_response") is not None
        assert state.get("dispatch_result") is not None

    def test_channel_detected(self):
        from agents.communication.graph import run_communication_agent
        state = run_communication_agent("test", channel="slack")
        assert state.get("detected_channel") == "slack"


class TestHITLAgent:
    def test_run(self):
        from agents.execution.graph import run_hitl_agent
        from shared.state import HITLDecision
        state = run_hitl_agent(
            "Approve execution of database fix",
            working_memory={"risk": "high", "execution_plan": {"script": "CREATE INDEX CONCURRENTLY..."}},
        )
        assert state["status"] in (ExecutionStatus.COMPLETED, ExecutionStatus.CANCELLED)
        assert state.get("decision_value") == HITLDecision.APPROVED

    def test_checkpoint_triggered(self):
        from agents.execution.graph import run_hitl_agent
        state = run_hitl_agent("Approve fix", working_memory={"risk": "high"})
        assert state.get("checkpoint_triggered") is True


class TestExecutionAgent:
    def test_run(self):
        from agents.execution.graph import run_execution_agent
        state = run_execution_agent(
            "Execute approved index creation",
            execution_plan={
                "script": "CREATE INDEX CONCURRENTLY idx_test ON orders(id)",
                "expected_outcome": "success",
                "rollback": "DROP INDEX idx_test",
            },
            approved_by="eng_lead",
        )
        assert state["status"] == ExecutionStatus.COMPLETED
        assert state.get("execution_output") is not None
        assert state.get("execution_output", {}).get("exit_code") == 0

    def test_preconditions_checked(self):
        from agents.execution.graph import run_execution_agent
        state = run_execution_agent("Execute", execution_plan={"script": "test"})
        assert "preconditions_ok" in state


class TestAuditAgent:
    def test_run(self):
        from agents.execution.graph import run_audit_agent
        from shared.state import make_audit_event, make_base_state, AgentType
        base = make_base_state("test", AgentType.AUDIT)
        events = [
            make_audit_event(base, "node_1", "ACTION_1"),
            make_audit_event(base, "node_2", "ACTION_2"),
        ]
        state = run_audit_agent(events)
        assert state["status"] == ExecutionStatus.COMPLETED
        assert state.get("compliance_score") == 1.0

    def test_events_normalised(self):
        from agents.execution.graph import run_audit_agent
        from shared.state import make_audit_event, make_base_state, AgentType
        base = make_base_state("test", AgentType.AUDIT)
        events = [make_audit_event(base, "n1", "A1")]
        state = run_audit_agent(events)
        assert len(state.get("normalised_events", [])) == len(events)


# ─────────────────────────────────────────────────────────────────────────────
# INTEGRATION TEST — FULL PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

class TestFullPipeline:
    def test_pipeline_completes(self):
        from orchestration.pipeline import run_full_pipeline
        result = run_full_pipeline(INCIDENT)
        assert result is not None
        assert result.run_id.startswith("run_")
        assert len(result.steps) == 11  # All 11 step records

    def test_all_agents_executed(self):
        from orchestration.pipeline import run_full_pipeline
        result = run_full_pipeline(INCIDENT)
        agent_names = [s.agent_name for s in result.steps]
        assert "Reasoning Agent" in agent_names
        assert "HITL Agent" in agent_names
        assert "Execution Agent" in agent_names
        assert "Audit Agent" in agent_names

    def test_hitl_decision_present(self):
        from orchestration.pipeline import run_full_pipeline
        result = run_full_pipeline(INCIDENT)
        assert result.hitl_decision in ("APPROVED", "REJECTED", "MODIFIED")

    def test_incident_report_generated(self):
        from orchestration.pipeline import run_full_pipeline
        result = run_full_pipeline(INCIDENT)
        assert len(result.incident_report) > 100

    def test_compliance_score(self):
        from orchestration.pipeline import run_full_pipeline
        result = run_full_pipeline(INCIDENT)
        assert 0.0 <= result.compliance_score <= 1.0

    def test_audit_trail_non_empty(self):
        from orchestration.pipeline import run_full_pipeline
        result = run_full_pipeline(INCIDENT)
        assert len(result.all_audit_events) > 0

    def test_no_failed_steps(self):
        from orchestration.pipeline import run_full_pipeline
        result = run_full_pipeline(INCIDENT)
        failed = [s for s in result.steps if s.status == "FAILED"]
        assert len(failed) == 0, f"Failed steps: {[s.agent_name for s in failed]}"


if __name__ == "__main__":
    # Quick smoke test without pytest
    print("Running smoke tests...")
    t = TestFullPipeline()
    t.test_pipeline_completes()
    print("✓ Full pipeline completed")
    t.test_all_agents_executed()
    print("✓ All agents executed")
    t.test_hitl_decision_present()
    print("✓ HITL decision present")
    t.test_incident_report_generated()
    print("✓ Incident report generated")
    t.test_compliance_score()
    print("✓ Compliance score valid")
    t.test_no_failed_steps()
    print("✓ No failed steps")
    print("\n✅ All smoke tests passed!")
