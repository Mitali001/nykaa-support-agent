"""Two independent persistent Chroma collections; JSON fallback keeps smoke tests offline."""
import json, math
from pathlib import Path
from config import ROOT, CHROMA_PATH
from rag.embeddings import LocalEmbedder
class VectorIndex:
    def __init__(self, name, embedder=None):
        self.name=name; self.embedder=embedder or LocalEmbedder(); self.path=ROOT/'storage'/'fallback'/f'{name}.json'; self.collection=None; self.backend='json-fallback'
        try:
            import chromadb
            CHROMA_PATH.mkdir(parents=True,exist_ok=True)
            client=chromadb.PersistentClient(path=str(CHROMA_PATH))
            self.collection=client.get_or_create_collection(name=name,metadata={"hnsw:space":"cosine"})
            self.backend='chromadb'
        except Exception: self.collection=None
    def upsert(self,chunks):
        if self.collection is not None:
            embeddings=self.embedder.encode([c['text'] for c in chunks])
            self.collection.upsert(ids=[c['chunk_id'] for c in chunks],documents=[c['text'] for c in chunks],metadatas=[{"doc_id":c['doc_id']} for c in chunks],embeddings=embeddings)
        else:
            self.path.parent.mkdir(parents=True,exist_ok=True)
            rows=[]
            for c in chunks: rows.append({**c,"embedding":self.embedder.encode([c['text']])[0]})
            self.path.write_text(json.dumps(rows),encoding='utf-8')
    def query(self,text,top_k=4):
        q=self.embedder.encode([text])[0]
        if self.collection is not None:
            result=self.collection.query(query_embeddings=[q],n_results=top_k,include=['documents','metadatas','distances'])
            return [{"text":d,"doc_id":m['doc_id'],"distance":float(dist),"similarity":1-float(dist)} for d,m,dist in zip(result['documents'][0],result['metadatas'][0],result['distances'][0])]
        if not self.path.exists(): return []
        rows=json.loads(self.path.read_text(encoding='utf-8'))
        # Lexical cosine fallback is deliberately transparent and separates unrelated
        # out-of-domain queries more reliably than pseudo-random feature hashing.
        import re
        stop={'what','is','the','a','an','for','to','of','and','in','on','how','do','i','can','does','are','my','me','it','if','be','by','with','from','after','when','who','won','explain','tell'}
        qterms={t for t in re.findall(r'[a-z0-9]+',text.lower()) if len(t)>2 and t not in stop}
        def lexical(r):
            terms={t for t in re.findall(r'[a-z0-9]+',r['text'].lower()) if len(t)>2 and t not in stop}
            return len(qterms & terms)/((len(qterms)*len(terms))**0.5) if qterms and terms else 0.0
        scored=sorted(rows,key=lexical,reverse=True)[:top_k]
        return [{"text":r['text'],"doc_id":r['doc_id'],"distance":1-lexical(r),"similarity":lexical(r)} for r in scored]
