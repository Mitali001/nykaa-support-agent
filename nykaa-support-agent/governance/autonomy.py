from tools import PermissionErrorForTool, check_order_status
ALLOWED_LOOKUP_CALLER='Lookup Agent'
def guarded_lookup(record_id,caller):
    if caller!=ALLOWED_LOOKUP_CALLER: raise PermissionErrorForTool('Least-autonomy policy: lookup tool is restricted to Lookup Agent')
    return check_order_status(record_id,caller=caller)

def governance_summary():
    return {"application_layer":"Only Lookup Agent is wired to the order lookup tool; API and other agents cannot call it directly.","risk_level":"Medium","risk_justification":"The system provides customer-support policy information and order-status summaries. Incorrect answers can inconvenience customers or mishandle support expectations, but the system does not make credit, employment, medical, or other high-impact decisions. Human escalation remains available.","runtime_layer":"Each request is capped by MAX_REQUEST_TOKENS; oversized input is rejected before orchestration.","data_layer":"Fixed-format phone and card-last-four patterns are masked before model processing and JSONL logging; all identity/address examples are synthetic.","model_layer":"MOCK_LLM is deterministic, no external LLM provider is called, and output grounding checks enforce evidence-only responses."}
