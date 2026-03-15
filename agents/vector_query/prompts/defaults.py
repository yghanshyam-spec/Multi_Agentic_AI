"""agents/vector_query/prompts/defaults.py"""
PREPROCESS_QUERY=("You are a query optimisation assistant.\nExpand this user query into 2-3 semantically related sub-queries for better retrieval coverage:\nQuery: {user_query}\nReturn JSON: {{original: str, expansions: [str]}}")
GENERATE_RESPONSE=("You are a precise, citation-aware assistant. Answer ONLY using the provided context. If the answer is not in the context, say so explicitly.\nContext:\n{retrieved_chunks}\nQuestion: {user_query}\nProvide answer with source references (section name, page number).")
CHECK_FAITHFULNESS=("Given the context and the generated answer, identify any claims in the answer NOT supported by the context.\nContext: {context}\nAnswer: {answer}\nReturn JSON: {{faithful: bool, unsupported_claims: [str]}}")
_REG={"rag_preprocess":PREPROCESS_QUERY,"rag_generate":GENERATE_RESPONSE,"rag_faithfulness":CHECK_FAITHFULNESS}
def get_default_prompt(k): return _REG.get(k,"")
