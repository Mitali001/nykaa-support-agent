"""CrewAI-compatible tools and deterministic preflight dispatch."""
from tools import check_order_status as _lookup
from rag.retrieval import RAGService
_RAG=None
RAG_TOOL_CALLS=0
LOOKUP_TOOL_CALLS=0
def configure_rag_service(service):
    global _RAG
    _RAG=service
def execute_rag_lookup(query: str) -> dict:
    global _RAG,RAG_TOOL_CALLS
    if _RAG is None: _RAG=RAGService()
    RAG_TOOL_CALLS+=1
    return _RAG.answer(query)
def rag_lookup(query: str) -> str:
    result=execute_rag_lookup(query)
    return result['answer']+' | sources: '+','.join(result['sources'])
def execute_order_lookup(record_id: str) -> dict:
    global LOOKUP_TOOL_CALLS
    LOOKUP_TOOL_CALLS+=1
    return _lookup(record_id,caller='Lookup Agent')
def order_lookup(record_id: str) -> str:
    return str(execute_order_lookup(record_id))
def make_crewai_tools():
    try:
        from crewai.tools import tool
        return tool('rag_lookup')(rag_lookup),tool('check_order_status')(order_lookup)
    except Exception: return None,None
