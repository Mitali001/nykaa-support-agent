"""Empirically measure in-scope/out-of-scope similarities and save midpoint threshold."""
import json
from pathlib import Path
from config import ROOT, SIMILARITY_THRESHOLD_FILE
from rag.document_loader import load_documents
from rag.chunking import fixed_size_chunks
from rag.embeddings import LocalEmbedder
from rag.vector_store import VectorIndex
IN_SCOPE=["What is the return window for beauty products?","How long does a COD refund take?","What is the standard delivery SLA?","Can an order be cancelled after it is shipped?","How do I claim a damaged item?"]
OUT_SCOPE=["Explain quantum entanglement in particle physics.","Who won the 1998 FIFA World Cup?"]
def main():
    docs=load_documents(); emb=LocalEmbedder(); idx=VectorIndex('calibration_temp',emb); idx.upsert(fixed_size_chunks(docs))
    ins=[idx.query(q,1)[0]['similarity'] for q in IN_SCOPE]; outs=[idx.query(q,1)[0]['similarity'] for q in OUT_SCOPE]
    # Select midpoint only if observed clusters separate; otherwise set conservative threshold and report overlap.
    threshold=(min(ins)+max(outs))/2 if min(ins)>max(outs) else max(outs)+0.01
    payload={"embedding_backend":emb.backend,"in_scope_top1":dict(zip(IN_SCOPE,ins)),"out_of_scope_top1":dict(zip(OUT_SCOPE,outs)),"threshold":round(threshold,6),"clusters_separated":min(ins)>max(outs)}
    SIMILARITY_THRESHOLD_FILE.write_text(json.dumps(payload,indent=2),encoding='utf-8'); print(json.dumps(payload,indent=2))
if __name__=='__main__': main()
