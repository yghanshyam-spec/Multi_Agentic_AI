"""agents/reasoning/prompts/defaults.py"""
FRAME = "You are a structured analytical thinker.\nRestate this problem precisely.\nIdentify: core_question, known_facts, unknowns, constraints.\nProblem: {input}\nReturn structured JSON."
HYPOTHESES = "Based on this problem, generate 2-4 plausible hypotheses.\nProblem: {problem}\nFor each: id, statement, supporting_evidence, contradicting_evidence.\nReturn JSON array."
EVIDENCE = "Evaluate the hypothesis against evidence.\nHypothesis: {hypothesis}\nEvidence: {evidence}\nRate: support_score (0-1), confidence, key_gaps.\nReturn JSON."
COT = "You are a rigorous analytical reasoner. Think step by step.\nGiven: {problem}\nEvidence: {evidence}\nReturn JSON: {steps: [str], primary_cause: str, confidence: float}"
CONCLUDE = "State the final conclusion clearly.\nReasoning: {reasoning}\nInclude: conclusion, confidence, key_assumptions, alternative_interpretations.\nReturn JSON."
VALIDATE_R = "Review this reasoning chain for logical fallacies.\nChain: {chain}\nReturn JSON: {valid: bool, issues: [str], severity: low|medium|high}"
_REGISTRY = {"reasoning_frame": FRAME, "reasoning_hypotheses": HYPOTHESES, "reasoning_evidence": EVIDENCE,
             "reasoning_cot": COT, "reasoning_conclude": CONCLUDE, "reasoning_validate": VALIDATE_R}
def get_default_prompt(key): return _REGISTRY.get(key, "")
