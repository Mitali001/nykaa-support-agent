from pathlib import Path
from config import ROOT

def load_documents(folder=None):
    folder=Path(folder) if folder else ROOT/'knowledge_base'
    docs=[]
    for path in sorted(folder.glob('*.txt')):
        docs.append({"doc_id":path.stem,"text":path.read_text(encoding='utf-8'),"source":path.name})
    if len(docs)<12: raise ValueError(f"Expected at least 12 KB documents; found {len(docs)}")
    return docs
