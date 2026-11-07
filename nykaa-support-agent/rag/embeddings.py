"""Local embeddings: SentenceTransformers when installed, deterministic fallback for offline smoke tests."""
import hashlib, math, re
class LocalEmbedder:
    def __init__(self, model_name='sentence-transformers/all-MiniLM-L6-v2', allow_fallback=True):
        self.model_name=model_name; self.model=None; self.backend='hashing-fallback'
        try:
            from sentence_transformers import SentenceTransformer
            self.model=SentenceTransformer(model_name, local_files_only=True)
            self.backend='sentence-transformers'
        except Exception:
            if not allow_fallback: raise RuntimeError('SentenceTransformer model is not locally cached. Install/download it before offline execution.')
    def encode(self, texts):
        if self.model is not None:
            return self.model.encode(list(texts),normalize_embeddings=True).tolist()
        # Fixed 384-dim signed hashing vector; deterministic and dependency-free, not a substitute for semantic ST embeddings.
        vectors=[]
        for text in texts:
            vec=[0.0]*384
            tokens=re.findall(r'[a-z0-9]+',text.lower())
            for token in tokens:
                h=int(hashlib.sha256(token.encode()).hexdigest()[:8],16); vec[h%384]+=1.0 if (h>>8)&1 else -1.0
            norm=math.sqrt(sum(x*x for x in vec)) or 1.0
            vectors.append([x/norm for x in vec])
        return vectors
