"""agents/vector_query/tools/vector_store.py — mock vector store."""
class VectorStore:
    def __init__(self,config=None): self.config=config or {}
    def search(self,query_embedding,top_k=5,filters=None):
        return [{"chunk_id":f"chk-{i}","text":f"Relevant content chunk {i} for the query.",
                 "score":0.92-i*0.05,"page":i+1,"section":f"Section {i+1}","source":"handbook.pdf"}
                for i in range(min(top_k,3))]
    def embed_query(self,text,model=None): return [0.1]*384
