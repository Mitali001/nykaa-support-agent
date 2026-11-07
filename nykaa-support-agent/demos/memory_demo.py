"""Task 8: LangChain history demonstration when installed; in-process fallback always shown."""
import json
from memory.session_memory import SessionMemory, build_langchain_history_adapter

def main():
    out={"fallback_session_memory":{}}
    mem=SessionMemory(); out['fallback_session_memory']['fresh_before']=mem.get('alpha')
    mem.add('alpha','My order is NYK0001','Order NYK0001 is shipped.')
    out['fallback_session_memory']['after_turn_1']=mem.get('alpha')
    mem.add('alpha','What is its status?','It is shipped.')
    out['fallback_session_memory']['after_turn_2']=mem.get('alpha')
    out['fallback_session_memory']['separate_session']=mem.get('beta')
    try:
        chain,store=build_langchain_history_adapter()
        first=chain.invoke({'input':'My order is NYK0001'},config={'configurable':{'session_id':'lc-demo'}})
        second=chain.invoke({'input':'What is its status?'},config={'configurable':{'session_id':'lc-demo'}})
        out['langchain_runnable_with_message_history']={"available":True,"first_output":first,"second_output":second,"history_messages":len(store['lc-demo'].messages)}
    except Exception as exc:
        out['langchain_runnable_with_message_history']={"available":False,"reason":type(exc).__name__+': '+str(exc)}
    print(json.dumps(out,indent=2))
if __name__=='__main__': main()
