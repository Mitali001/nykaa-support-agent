import json
from collections import defaultdict
from rag.document_loader import load_documents
from rag.chunking import fixed_size_chunks,sentence_chunks
from rag.embeddings import LocalEmbedder
from rag.vector_store import VectorIndex
from evaluation.test_set import TEST_QUERIES

def score_strategy(name,chunks,embedder):
    idx=VectorIndex('eval_'+name,embedder); idx.upsert(chunks); rows=[]
    for qid,q,gold in TEST_QUERIES[:12]:
        hits=idx.query(q,4); predicted=list(dict.fromkeys(h['doc_id'] for h in hits)); tp=len(set(predicted)&set(gold)); precision=tp/len(predicted) if predicted else 0; recall=tp/len(gold) if gold else 1
        rows.append({"query_id":qid,"query":q,"gold_docs":gold,"retrieved_unique_docs":predicted,"arithmetic":f"precision={tp}/{len(predicted)}; recall={tp}/{len(gold)}","precision":round(precision,3),"recall":round(recall,3)})
    return rows

def main():
    docs=load_documents(); emb=LocalEmbedder(); fixed=score_strategy('fixed',fixed_size_chunks(docs),emb); sent=score_strategy('sentence',sentence_chunks(docs),emb)
    result={"embedding_backend":emb.backend,"fixed_size_overlap":fixed,"sentence_based":sent}
    for k,rows in [('fixed_size_overlap',fixed),('sentence_based',sent)]: result[k+'_mean']={m:round(sum(r[m] for r in rows)/len(rows),3) for m in ['precision','recall']}
    fm=result['fixed_size_overlap_mean']; sm=result['sentence_based_mean']
    winner='sentence-based' if (sm['precision']+sm['recall']) >= (fm['precision']+fm['recall']) else 'fixed-size-with-overlap'
    result['recommendation']=(f"Deploy {winner}: fixed-size precision/recall={fm['precision']:.3f}/{fm['recall']:.3f}; sentence-based precision/recall={sm['precision']:.3f}/{sm['recall']:.3f}. The selected strategy has the higher combined mean precision-plus-recall on this 12-query, document-deduplicated evaluation; rerun after changing the KB or embedding model.")
    print(json.dumps(result,indent=2)); return result
if __name__=='__main__': main()
