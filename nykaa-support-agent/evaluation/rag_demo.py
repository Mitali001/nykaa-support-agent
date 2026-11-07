"""Task 4 demonstration: five in-scope questions and one out-of-scope fallback."""
import json
from rag.retrieval import RAGService
QUERIES=[
    "What is the return window for Beauty products?",
    "How long does a COD refund take?",
    "What is the delivery SLA?",
    "Can an order be cancelled after shipment?",
    "How do I claim a damaged item?",
    "Explain quantum entanglement in particle physics.",
]
def main():
    rag=RAGService(); rows=[]
    for q in QUERIES:
        r=rag.answer(q)
        rows.append({"query":q,"answer":r['answer'],"grounded":r['grounded'],"top1_similarity":r['top_similarity'],"sources":r['sources']})
    print(json.dumps({"threshold":rag.threshold,"embedding_backend":rag.embedder.backend,"demonstrations":rows},indent=2))
if __name__=='__main__': main()
