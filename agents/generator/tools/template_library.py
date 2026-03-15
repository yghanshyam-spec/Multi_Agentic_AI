"""agents/generator/tools/template_library.py — Document template registry."""
TEMPLATES = {
    "incident_report_v2": {"name":"Production Incident Report","sections":["executive_summary","timeline","root_cause","resolution"],"audience":"executive + engineering","format":"docx"},
    "rca_brief": {"name":"Root Cause Analysis Brief","sections":["problem_statement","analysis","findings","recommendations"],"audience":"engineering","format":"markdown"},
    "stakeholder_update": {"name":"Stakeholder Status Update","sections":["summary","current_status","next_steps","timeline"],"audience":"executive","format":"email"},
}
def get_template(tid: str): return TEMPLATES.get(tid, TEMPLATES["incident_report_v2"])
def list_templates(): return list(TEMPLATES.keys())
