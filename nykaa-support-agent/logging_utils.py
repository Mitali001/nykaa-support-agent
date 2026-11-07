import json, uuid, time
from pathlib import Path
from config import LOG_PATH
from guardrails.input_guardrails import inspect_and_mask

def log_request(query,status_code=200,elapsed_ms=0,trace_id=None,extra=None):
    trace_id=trace_id or str(uuid.uuid4()); safe=inspect_and_mask(query)['text']
    LOG_PATH.parent.mkdir(parents=True,exist_ok=True)
    row={"timestamp":time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),"trace_id":trace_id,"request_text":safe,"status_code":status_code,"elapsed_ms":round(elapsed_ms,3),**(extra or {})}
    with LOG_PATH.open('a',encoding='utf-8') as f: f.write(json.dumps(row,ensure_ascii=False)+'\n')
    return trace_id
