"""Task 7 demonstration: tool dispatch for separate policy/order questions and CrewAI kickoff."""
import json
from rag.retrieval import RAGService
from agents import tools as agent_tools
from agents.tools import configure_rag_service, execute_rag_lookup, execute_order_lookup, make_crewai_tools
from tools import escalation_design

def main():
    rag=RAGService(); configure_rag_service(rag)
    policy=execute_rag_lookup('What is the return window for Beauty products?')
    order=execute_order_lookup('NYK0001')
    out={"retrieval_tool_invocation":{"calls":agent_tools.RAG_TOOL_CALLS,"sources":policy['sources']},"lookup_tool_invocation":{"calls":agent_tools.LOOKUP_TOOL_CALLS,"result":order},"escalation_design":escalation_design()}
    try:
        from agents.crew import build_crew
        rt,lt=make_crewai_tools(); crew=build_crew(rt,lt)
        result=crew.kickoff(inputs={"query":"What is the return window for Beauty products? Check order NYK0001 only if requested.","context":"\\n".join(h['text'] for h in policy['retrieved']),"order_result":str(order)})
        out['crewai_kickoff']={"executed":True,"output":str(result)}
    except Exception as exc:
        out['crewai_kickoff']={"executed":False,"reason":type(exc).__name__+': '+str(exc)}
    print(json.dumps(out,indent=2))
if __name__=='__main__': main()
