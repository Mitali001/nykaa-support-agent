"""Grounded retrieval with measured threshold and deterministic context-only answer generation."""
import json, re
from config import ROOT, RAG_TOP_K, SIMILARITY_THRESHOLD_FILE
from rag.document_loader import load_documents
from rag.chunking import fixed_size_chunks, sentence_chunks
from rag.embeddings import LocalEmbedder
from rag.vector_store import VectorIndex
class RAGService:
    def __init__(self, preferred='fixed'):
        self.docs=load_documents(); self.embedder=LocalEmbedder(); self.fixed=VectorIndex('nykaa_fixed_overlap',self.embedder); self.sentence=VectorIndex('nykaa_sentence_chunks',self.embedder)
        self.fixed_chunks=fixed_size_chunks(self.docs); self.sentence_chunks=sentence_chunks(self.docs)
        self.fixed.upsert(self.fixed_chunks); self.sentence.upsert(self.sentence_chunks)
        self.index=self.sentence if preferred=='sentence' else self.fixed
        self.threshold=self._threshold()
    def _threshold(self):
        if SIMILARITY_THRESHOLD_FILE.exists():
            try:return float(json.loads(SIMILARITY_THRESHOLD_FILE.read_text())['threshold'])
            except Exception: pass
        return 0.0
    def retrieve(self,query,top_k=RAG_TOP_K):
        hits=self.index.query(query,top_k)
        return hits
    def answer(self,query,top_k=RAG_TOP_K):
        hits=self.retrieve(query,top_k)
        if not hits or hits[0]['similarity']<self.threshold:
            return {"answer":"I don't know based on the available Nykaa support knowledge base.","grounded":False,"sources":[],"top_similarity":hits[0]['similarity'] if hits else 0.0,"retrieved":hits}
        # MOCK_LLM: return retrieved evidence excerpt; never fabricate unsupported policy facts.
        evidence=' '.join(dict.fromkeys(h['text'] for h in hits))
        sentences=[s.strip() for s in re.split(r'(?<=[.!?])\s+',evidence) if s.strip()]
        query_terms=set(re.findall(r'[a-z0-9]+',query.lower()))
        ranked=sorted(sentences,key=lambda s:len(query_terms & set(re.findall(r'[a-z0-9]+',s.lower()))),reverse=True)
        answer=' '.join(ranked[:3])
        return {"answer":answer,"grounded":bool(answer),"sources":sorted(set(h['doc_id'] for h in hits)),"top_similarity":hits[0]['similarity'],"retrieved":hits}
