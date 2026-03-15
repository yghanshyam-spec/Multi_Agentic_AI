"""agents/workflow/prompts/defaults.py"""
CONDITION = "Evaluate whether the workflow condition is met.\nCondition: {condition}\nState: {state}\nReturn JSON: {condition_met: bool, evaluation_reason: str}"
ERROR = "A workflow step failed.\nFailed step: {step_id} | Error: {error} | Remaining: {remaining}\nDecide: retry_step, skip_step, halt_workflow, or escalate_to_human.\nReturn JSON: {action: str, rationale: str}"
SUMMARISE = "Generate a workflow completion summary.\nWorkflow: {name} | Steps: {steps} | Outputs: {outputs}\nReturn JSON: {summary: str, status: str, step_summaries: [str]}"
_REGISTRY = {"workflow_condition": CONDITION, "workflow_error": ERROR, "workflow_summarise": SUMMARISE}
def get_default_prompt(key): return _REGISTRY.get(key, "")
