"""agents/audit/prompts/defaults.py"""
POLICY = "Evaluate this action against compliance policy.\nAction: {action}\nPolicies: [no_pii_in_logs, no_delete_without_approval, rate_limit_llm_calls, require_hitl_for_high_risk]\nReturn JSON: {compliant: bool, violations: [{rule_id: str, severity: str, description: str}]}"
ANOMALY = "Analyse this action sequence for behavioural anomalies.\nActions: {actions}\nReturn JSON: {anomalies_found: bool, anomalies: [str], baseline_match: bool}"
REPORT = "Generate a compliance audit report.\nLogs: {logs}\nInclude: total_events, llm_calls, policy_violations, anomalies_detected, compliance_score, agents_involved, hitl_checkpoints.\nReturn JSON."
_REGISTRY = {"audit_policy": POLICY, "audit_anomaly": ANOMALY, "audit_report": REPORT}
def get_default_prompt(key): return _REGISTRY.get(key, "")
