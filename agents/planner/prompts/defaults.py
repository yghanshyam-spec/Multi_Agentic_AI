"""agents/planner/prompts/defaults.py"""
GOAL = """You are a strategic planning assistant.
Analyse this goal and extract: objective, success_criteria, constraints, stakeholders.
Return structured JSON: {objective: str, success_criteria: [str], constraints: dict, stakeholders: [str]}"""
DECOMPOSE = """Break down the following objective into discrete, executable tasks.
Objective: {objective}
Constraints: {constraints}
For each task return: task_id, title, description, agent, deps, parallel_safe, risk, estimated_duration.
Return as JSON array."""
ASSIGN = """For each task, identify the most suitable agent type.
Available: REASONING_AGENT, GENERATOR_AGENT, COMMUNICATION_AGENT, EXECUTION_AGENT, HITL_AGENT, WORKFLOW_AGENT, AUDIT_AGENT.
Tasks: {tasks}
Return JSON: {task_id: {agent_type: str, rationale: str}}"""
ESTIMATE = """Estimate resource requirements and risk for each task.
Task plan: {plan}
Return JSON: {task_id: {risk_level: low|medium|high, requires_human_approval: bool, parallel_safe: bool, estimated_tokens: int}}"""
VALIDATE = """Review this execution plan for completeness and feasibility.
Plan: {plan}
Return JSON: {valid: bool, gaps: [str], recommendations: [str]}"""
_REGISTRY = {
    "planner_goal": GOAL, "planner_decompose": DECOMPOSE,
    "planner_assign": ASSIGN, "planner_estimate": ESTIMATE, "planner_validate": VALIDATE,
}
def get_default_prompt(key): return _REGISTRY.get(key, "")
