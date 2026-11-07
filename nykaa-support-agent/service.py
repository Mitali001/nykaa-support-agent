"""Application orchestration: input checks, budgets, retrieval, optional order lookup, CrewAI kickoff, review, cache."""
import re, uuid, time, asyncio
from functools import lru_cache
from schemas import SupportResponse
from rag.retrieval import RAGService
from guardrails.input_guardrails import inspect_and_mask
from guardrails.output_guardrails import groundedness_check
from governance.budget import enforce_budget
from governance.autonomy import guarded_lookup
from review.autogen_review import deterministic_review, run_autogen_review
from memory.session_memory import SessionMemory
from tools import PermissionErrorForTool
class SupportService:
    def __init__(self):
        self.rag=RAGService()
        self.memory=SessionMemory()
        from agents.tools import configure_rag_service
        configure_rag_service(self.rag)
        self.cache={}
        self.langchain_chain=None
        self.langchain_store={}
        try:
            from memory.session_memory import build_langchain_history_adapter
            self.langchain_chain,self.langchain_store=build_langchain_history_adapter()
        except Exception: pass
        self.rag_calls=0
        self.cache_hits=0
        self.crew_kickoffs=0
    def _intent(self,q):
        if re.search(r'NYK\d{4}',q,re.I): return 'order_lookup'
        return 'policy_question'
    def ask(self,query,session_id='default',trace_id=None,run_crew=True):
        trace_id=trace_id or str(uuid.uuid4()); started=time.perf_counter()
        safe=inspect_and_mask(query)
        if not safe['safe']: return SupportResponse(answer='I can help with Nykaa support questions, but I cannot follow instructions that attempt to override system safeguards.',intent='blocked',grounded=False,trace_id=trace_id)
        masked=safe['text']; budget=enforce_budget(masked)
        intent=self._intent(masked); order=None
        order_match=re.search(r'NYK\d{4}',masked,re.I)
        if order_match:
            from agents.tools import execute_order_lookup
            order=execute_order_lookup(order_match.group(0).upper())
        # RAG cache is normalized query keyed; order queries still retrieve relevant policies only if query is policy-related.
        normalized=' '.join(masked.lower().split())
        if normalized in self.cache:
            rag_result=self.cache[normalized]; cache_hit=True; self.cache_hits+=1
        else:
            self.rag_calls+=1
            from agents.tools import execute_rag_lookup
            rag_result=execute_rag_lookup(masked); self.cache[normalized]=rag_result; cache_hit=False
        if intent=='order_lookup' and order and order.get('found'):
            draft=f"Order {order['record_id']} is currently {order['status']}. Order value: INR {order['order_value_inr']}. Escalation score: {order['escalation_score']:.3f}."
            sources=[]; grounded=True
        else:
            draft=rag_result['answer']; sources=rag_result['sources']; grounded=rag_result['grounded']
        evidence=[h['text'] for h in rag_result.get('retrieved',[])]
        check=groundedness_check(draft,evidence,grounded_flag=grounded)
        if not check['allowed'] and intent!='order_lookup': draft=check['answer']; grounded=False
        try:
            asyncio.get_running_loop()
            review=deterministic_review(draft,evidence)  # WebSocket path stays non-blocking; dedicated review demo exercises AutoGen.
        except RuntimeError:
            review=asyncio.run(run_autogen_review(draft,evidence))
        final=review.final_answer
        # CrewAI kickoff is attempted when installed. All tools are separately executed above through guarded deterministic dispatch.
        crew_status='deterministic orchestration fallback'
        if run_crew:
            try:
                from agents.tools import make_crewai_tools
                from agents.crew import build_crew
                rt,lt=make_crewai_tools(); crew=build_crew(rt,lt)
                crew.kickoff(inputs={"query":masked,"context":"\n".join(evidence),"order_result":str(order or {})})
                self.crew_kickoffs+=1; crew_status='CrewAI kickoff completed'
            except Exception as exc: crew_status=f'CrewAI unavailable/fallback: {type(exc).__name__}'
        # When LangChain is installed, record the same turn through RunnableWithMessageHistory.
        if getattr(self,'langchain_chain',None) is not None and session_id:
            try: self.langchain_chain.invoke({'input':masked},config={'configurable':{'session_id':session_id}})
            except Exception: pass
        if session_id: self.memory.add(session_id,masked,final)
        return SupportResponse(answer=final,intent=intent,grounded=grounded,sources=sources,order=order,escalation_recommended=bool(order and order.get('escalate')),trace_id=trace_id)
