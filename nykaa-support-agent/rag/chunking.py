import re

def fixed_size_chunks(documents, chunk_size=420, overlap=80):
    if chunk_size<=0 or overlap<0 or overlap>=chunk_size: raise ValueError('Require chunk_size > overlap >= 0')
    out=[]
    for doc in documents:
        text=doc['text']; start=0; idx=0
        while start<len(text):
            part=text[start:start+chunk_size].strip()
            if part: out.append({"chunk_id":f"{doc['doc_id']}::fixed::{idx}","doc_id":doc['doc_id'],"text":part})
            idx+=1; start+=chunk_size-overlap
    return out

def sentence_chunks(documents, max_sentences=3):
    out=[]
    for doc in documents:
        sentences=[s.strip() for s in re.split(r'(?<=[.!?])\s+',doc['text'].strip()) if s.strip()]
        for i in range(0,len(sentences),max_sentences):
            part=' '.join(sentences[i:i+max_sentences])
            if part: out.append({"chunk_id":f"{doc['doc_id']}::sentence::{i//max_sentences}","doc_id":doc['doc_id'],"text":part})
    return out
