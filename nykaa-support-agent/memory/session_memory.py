"""Per-session in-process history; LangChain RunnableWithMessageHistory adapter when installed."""
from collections import defaultdict
class SessionMemory:
    def __init__(self): self._history=defaultdict(list)
    def add(self,session_id,user,assistant): self._history[session_id].extend([{"role":"user","content":user},{"role":"assistant","content":assistant}])
    def get(self,session_id): return list(self._history.get(session_id,[]))
    def clear(self,session_id): self._history.pop(session_id,None)
    def previous_context(self,session_id): return self.get(session_id)[-6:]

# The capstone's LangChain integration is available when dependencies are installed.
def build_langchain_history_adapter():
    try:
        from langchain_core.chat_history import InMemoryChatMessageHistory
        from langchain_core.runnables.history import RunnableWithMessageHistory
        from langchain_core.runnables import RunnableLambda
    except ImportError as exc: raise RuntimeError('Install langchain-core to use RunnableWithMessageHistory') from exc
    store={}
    def get_history(session_id):
        if session_id not in store: store[session_id]=InMemoryChatMessageHistory()
        return store[session_id]
    runnable=RunnableLambda(lambda x: {'reply': f"Received: {x['input']} (prior messages in this session: {len(x.get('history', []))})"})
    chain=RunnableWithMessageHistory(runnable,get_history,input_messages_key='input',history_messages_key='history',output_messages_key='reply')
    return chain,store
