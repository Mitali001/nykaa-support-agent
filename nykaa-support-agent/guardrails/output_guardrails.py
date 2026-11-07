def groundedness_check(answer, retrieved_context, grounded_flag=True):
    if not grounded_flag or not retrieved_context or not answer.strip():
        return {"allowed":False,"answer":"I can't verify that from the available support policy documents. Please contact customer support.","reason":"No supporting retrieved context"}
    # The answer must contain at least one meaningful token found in the retrieved evidence.
    evidence=' '.join(retrieved_context).lower(); tokens=[t for t in answer.lower().split() if len(t)>4]
    if tokens and not any(t.strip('.,:;!?') in evidence for t in tokens):
        return {"allowed":False,"answer":"I can't verify that from the available support policy documents. Please contact customer support.","reason":"Answer has no lexical support in retrieved context"}
    return {"allowed":True,"answer":answer,"reason":"Retrieved context supports response"}
