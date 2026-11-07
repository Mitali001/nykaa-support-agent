from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import importlib.util, json, re, sys, time, uuid
from service import SupportService
from logging_utils import log_request
from rag.retrieval import RAGService
app=FastAPI(title='Nykaa Domain Support Agent',version='2.0.0',description='Nykaa support console and MOCK_LLM capstone API')
service=SupportService()
ROOT=Path(__file__).resolve().parents[1]
WEB_DIR=ROOT/'web'
# Serve the dashboard from an absolute path anchored to this module, not the
# caller's working directory. Register page routes before the static mount.
INDEX_FILE = WEB_DIR / 'index.html'

@app.get('/', include_in_schema=False)
@app.get('/dashboard', include_in_schema=False)
@app.get('/index.html', include_in_schema=False)
def dashboard_ui():
    if not INDEX_FILE.is_file():
        raise HTTPException(status_code=500, detail=f'Dashboard file is missing: {INDEX_FILE}')
    return FileResponse(str(INDEX_FILE), media_type='text/html')

app.mount('/static', StaticFiles(directory=str(WEB_DIR)), name='static')

@app.middleware('http')
async def log_dashboard_requests(request, call_next):
    # Core /ask, /health and /add-document handlers log their own masked payloads.
    # This middleware adds one structured event for each dashboard JSON API request.
    if request.url.path.startswith('/api/'):
        started=time.perf_counter(); trace=str(uuid.uuid4())
        try:
            response=await call_next(request)
        except Exception as exc:
            log_request(f"{request.method} {request.url.path}",500,(time.perf_counter()-started)*1000,trace,{'endpoint':request.url.path,'error':type(exc).__name__})
            raise
        log_request(f"{request.method} {request.url.path}",response.status_code,(time.perf_counter()-started)*1000,trace,{'endpoint':request.url.path})
        response.headers['X-Trace-ID']=trace
        return response
    return await call_next(request)

class AskRequest(BaseModel): query:str=Field(min_length=1,max_length=10000); session_id:str='default'
class AddDocumentRequest(BaseModel): doc_id:str=Field(pattern=r'^[A-Za-z0-9_-]+$'); text:str=Field(min_length=20)
class AskResponse(BaseModel): answer:str; intent:str; grounded:bool; sources:list[str]=Field(default_factory=list); order:Optional[dict]=None; escalation_recommended:bool=False; trace_id:str|None=None
@app.get('/health')
def health():
    trace=str(uuid.uuid4())
    log_request('GET /health',200,0,trace,{"endpoint":"health"})
    return {"status":"ok","mock_llm":True}
@app.post('/ask',response_model=AskResponse)
def ask(req:AskRequest):
    start=time.perf_counter(); trace=str(uuid.uuid4())
    try:
        result=service.ask(req.query,req.session_id,trace_id=trace)
        log_request(req.query,200,(time.perf_counter()-start)*1000,trace,{"intent":result.intent})
        return result
    except ValueError as exc:
        log_request(req.query,400,(time.perf_counter()-start)*1000,trace,{"error":str(exc)})
        raise HTTPException(status_code=400,detail=str(exc))
@app.post('/add-document')
def add_document(req:AddDocumentRequest):
    start=time.perf_counter(); trace=str(uuid.uuid4())
    # Write only under KB; rebuild both collections on next service process start.
    from config import ROOT
    if not re.fullmatch(r'[A-Za-z0-9_-]+', req.doc_id): raise HTTPException(status_code=422,detail='Document ID may contain only letters, numbers, underscore and hyphen')
    path=ROOT/'knowledge_base'/f"{req.doc_id}.txt"
    if path.exists(): raise HTTPException(status_code=409,detail='Document ID already exists')
    path.write_text(req.text,encoding='utf-8')
    log_request(req.text,200,(time.perf_counter()-start)*1000,trace,{"endpoint":"add-document","doc_id":req.doc_id})
    return {"added":True,"doc_id":req.doc_id,"note":"Restart service to re-index both collections."}
@app.websocket('/ws/chat')
async def websocket_chat(ws:WebSocket):
    await ws.accept(); session_id='ws-'+str(uuid.uuid4())
    try:
        while True:
            payload=await ws.receive_json(); query=str(payload.get('query',''))
            session_id=str(payload.get('session_id') or session_id)
            result=service.ask(query,session_id)
            log_request(query,200,0,result.trace_id,{"channel":"websocket"})
            await ws.send_json(result.model_dump())
    except WebSocketDisconnect:
        # Disconnect is client-scoped; the FastAPI server and other sessions remain available.
        return


# Dashboard read models. These endpoints expose the capstone's existing evidence;
# they do not replace or bypass the core RAG / CrewAI / review pipeline.
@app.get('/api/dashboard')
def dashboard_summary():
    from dataset.dataset import generate_orders, report
    from rag.document_loader import load_documents
    from tools import escalation_design
    rows=generate_orders(); rep=report(rows); docs=load_documents()
    status_order=['Placed','Shipped','Delivered','Returned','Refunded']
    category_order=['Apparel','Electronics','Home','Footwear','Beauty']
    status_counts=[{'status':k,'count':rep['status_counts'].get(k,0)} for k in status_order]
    category_counts=[{'category':k,'count':rep['category_counts'].get(k,0),'percentage':round(100*rep['category_counts'].get(k,0)/len(rows),1)} for k in category_order]
    colors=['#e83e78','#8b78e6','#f2b34e','#31ad87','#8b91a4']; total=max(1,len(rows)); cursor=0; stops=[]
    for item,color in zip(status_counts,colors):
        nxt=cursor+100*item['count']/total; stops.append(f'{color} {cursor:.1f}% {nxt:.1f}%'); cursor=nxt
    rag_backend=getattr(service.rag.fixed,'backend','unknown')
    embedding_backend=getattr(service.rag.embedder,'backend','unknown')
    crew_ok=importlib.util.find_spec('crewai') is not None
    autogen_ok=importlib.util.find_spec('autogen_agentchat') is not None
    chroma_ok=rag_backend=='chromadb'
    st_ok=embedding_backend=='sentence-transformers'
    components=[
      {'name':'FastAPI application','detail':'HTTP endpoints and WebSocket chat','ok':True,'state':'READY'},
      {'name':'RAG retrieval','detail':f'{rag_backend} · {embedding_backend}','ok':True,'state':'READY' if chroma_ok and st_ok else 'FALLBACK'},
      {'name':'CrewAI orchestration','detail':'Package detected; kickoff path still requires runtime verification','ok':crew_ok,'state':'INSTALLED' if crew_ok else 'OPTIONAL'},
      {'name':'AutoGen review','detail':'Package detected; structured team path still requires runtime verification','ok':autogen_ok,'state':'INSTALLED' if autogen_ok else 'OPTIONAL'},
      {'name':'PII & injection guardrails','detail':'Input masking and prompt checks','ok':True,'state':'ACTIVE'},
      {'name':'Structured JSONL logging','detail':'Trace IDs and masked request text','ok':True,'state':'ACTIVE'},
    ]
    from config import MAX_REQUEST_TOKENS
    return {'dataset':rep,'status_counts':status_counts,'category_counts':category_counts,'status_gradient':'conic-gradient('+', '.join(stops)+')','knowledge_documents':len(docs),'cache':{'entries':len(service.cache),'hits':service.cache_hits,'rag_calls':service.rag_calls},'components':components,'overall_health':True,'runtime':{'python':sys.version.split()[0]},'governance':{'risk':'Medium','max_request_tokens':MAX_REQUEST_TOKENS,'escalation':escalation_design()}}

@app.get('/api/orders')
def list_orders(q:str='',status:str='',category:str='',limit:int=Query(100,ge=1,le=500)):
    from dataset.dataset import generate_orders
    rows=generate_orders()
    if q: rows=[r for r in rows if q.lower() in r['record_id'].lower()]
    if status: rows=[r for r in rows if r['status'].lower()==status.lower()]
    if category: rows=[r for r in rows if r['category'].lower()==category.lower()]
    total=len(rows)
    return {'total':total,'items':rows[:limit]}

@app.get('/api/orders/{record_id}')
def get_order(record_id:str):
    from agents.tools import execute_order_lookup
    from tools import escalation_design
    result=execute_order_lookup(record_id.upper())
    if not result.get('found'): raise HTTPException(status_code=404,detail=result.get('error','Order not found'))
    result['threshold']=escalation_design()['threshold']
    return result

@app.get('/api/knowledge')
def knowledge_documents():
    from rag.document_loader import load_documents
    import re
    docs=[]
    for d in load_documents():
        title=re.sub(r'^\d+_','',d['doc_id']).replace('_',' ').title()
        text=d['text']; docs.append({'doc_id':d['doc_id'],'title':title,'source':d['source'],'text':text,'words':len(text.split()),'sentences':len([x for x in re.split(r'(?<=[.!?])\s+',text.strip()) if x])})
    return {'count':len(docs),'documents':docs}

def _evaluation_payload():
    path=ROOT/'transcripts'/'scale_evaluation.txt'
    if not path.exists(): return {'queries':[],'averages':{},'source':'No saved evaluation transcript'}
    raw=path.read_text(encoding='utf-8')
    # Older demonstration captures may append shell stderr after the JSON payload.
    data, _end=json.JSONDecoder().raw_decode(raw.lstrip())
    from evaluation.test_set import TEST_QUERIES
    gold={qid:bool(topic) for qid,_,topic in TEST_QUERIES}
    for row in data.get('queries',[]): row['gold']=gold.get(row.get('id'),bool(row.get('sources')))
    return {'queries':data.get('queries',[]),'averages':data.get('averages',{}),'source':'Saved MOCK_LLM transcript','judge':data.get('judge','')}

@app.get('/api/evaluation')
def get_evaluation():
    return _evaluation_payload()

@app.post('/api/evaluation/run')
def run_evaluation():
    from evaluation.scale_evaluation import main as run_scale_evaluation
    import contextlib, io
    output=io.StringIO()
    with contextlib.redirect_stdout(output): data=run_scale_evaluation()
    path=ROOT/'transcripts'/'scale_evaluation.txt'; path.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
    return _evaluation_payload()

@app.get('/api/logs')
def recent_logs(limit:int=Query(30,ge=1,le=200)):
    from config import LOG_PATH
    if not LOG_PATH.exists(): return {'count':0,'items':[]}
    rows=[]
    for line in LOG_PATH.read_text(encoding='utf-8').splitlines()[-limit:]:
        try: rows.append(json.loads(line))
        except json.JSONDecodeError: continue
    return {'count':len(rows),'items':list(reversed(rows))}


@app.get('/api/rag-report')
def rag_report():
    def read_json_capture(name):
        path=ROOT/'transcripts'/name
        if not path.exists(): return {}
        raw=path.read_text(encoding='utf-8').lstrip()
        try: return json.JSONDecoder().raw_decode(raw)[0]
        except Exception: return {}
    calibration=read_json_capture('rag_threshold_calibration.txt')
    comparison=read_json_capture('rag_precision_recall.txt')
    return {'calibration':calibration,'comparison':comparison,'selected_collection':'nykaa_fixed_overlap','backend_note':'Values in the retained transcripts were measured with the deterministic fallback backend. Re-run calibration and retrieval evaluation after enabling/caching SentenceTransformers.'}

@app.get('/api/demos')
def demo_status():
    def read_json_capture(name):
        path=ROOT/'transcripts'/name
        if not path.exists(): return {}
        raw=path.read_text(encoding='utf-8').lstrip()
        try: return json.JSONDecoder().raw_decode(raw)[0]
        except Exception: return {}
    crew=read_json_capture('crew_demo.txt'); review=read_json_capture('autogen_review_demo.txt'); memory=read_json_capture('memory_demo.txt')
    return {'crew':crew,'review':review,'memory':memory}
