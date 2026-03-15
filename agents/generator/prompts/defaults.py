"""agents/generator/prompts/defaults.py"""
SELECT = "Select the most appropriate content template for this request.\nRequest: {request}\nAvailable templates: {templates}\nReturn JSON: {template_id: str, rationale: str, required_inputs: [str]}"
PLAN = "Create a detailed content outline.\nTemplate: {template} | Inputs: {inputs} | Audience: {audience}\nReturn JSON: {sections: [{id: str, title: str, key_points: [str]}]}"
SECTION = "Write the '{section}' section of a {doc_type}.\nOutline: {outline}\nData: {data}\nAudience: {audience} | Tone: professional | Length: 150-300 words\nReturn JSON: {content: str, section_id: str}"
REVIEW = "Review this content for quality.\nContent: {content}\nReturn JSON: {score: int, issues: [str], revision_needed: bool}"
REFINE = "Revise this content based on feedback.\nContent: {content}\nFeedback: {feedback}\nReturn JSON: {refined_content: str}"
_REGISTRY = {"generator_select": SELECT, "generator_plan": PLAN, "generator_section": SECTION,
             "generator_review": REVIEW, "generator_refine": REFINE}
def get_default_prompt(key): return _REGISTRY.get(key, "")
