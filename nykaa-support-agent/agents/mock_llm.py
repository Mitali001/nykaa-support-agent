"""CrewAI BaseLLM implementation: deterministic, offline, and schema-driven tool dispatch."""
import json, re, uuid, os
os.environ.setdefault('CREWAI_DISABLE_TELEMETRY','true')
os.environ.setdefault('OTEL_SDK_DISABLED','true')
os.environ.setdefault('CREWAI_TRACING_ENABLED','false')
try:
    from crewai.llms.base_llm import BaseLLM
except ImportError:
    class BaseLLM:
        def __init__(self,model='mock-llm',temperature=0): self.model=model; self.temperature=temperature

class DeterministicMockLLM(BaseLLM):
    def __init__(self):
        try: super().__init__(model='nykaa-mock-llm',temperature=0)
        except TypeError: super().__init__('nykaa-mock-llm',0)

    def supports_function_calling(self): return True
    def get_context_window_size(self): return 8192

    @staticmethod
    def _as_dict(value):
        if isinstance(value,dict): return value
        if hasattr(value,'model_dump'): return value.model_dump()
        if hasattr(value,'dict'): return value.dict()
        return {}

    @staticmethod
    def _content(messages):
        if isinstance(messages,str): return messages
        pieces=[]
        for item in messages:
            row=DeterministicMockLLM._as_dict(item)
            content=row.get('content')
            if content is not None: pieces.append(str(content))
        return '\\n'.join(pieces)

    def _schema_driven_tool_call(self,messages,tools,available_functions):
        """Choose by declared parameter schema (record_id/query), never by tool-name substring."""
        if not tools or not available_functions: return None
        prompt=self._content(messages)
        order_id=re.search(r'\bNYK\d{4}\b',prompt,re.I)
        for raw_tool in tools:
            tool=self._as_dict(raw_tool)
            fn=tool.get('function',tool)
            params=fn.get('parameters') or fn.get('args_schema') or {}
            properties=(params.get('properties') or {}) if isinstance(params,dict) else {}
            declared=set(properties)
            # Schema is the dispatch authority: the lookup tool declares record_id.
            if 'record_id' in declared and order_id:
                name=fn.get('name') or tool.get('name')
                if name in available_functions:
                    return name,{'record_id':order_id.group(0).upper()}
            # Retrieval tool declares query. Do not route an order lookup here.
            if 'query' in declared and not order_id:
                name=fn.get('name') or tool.get('name')
                if name in available_functions:
                    query_match=re.search(r'(?i)(?:query|question)\s*[:=]\s*(.+)',prompt)
                    query=query_match.group(1).splitlines()[0].strip() if query_match else prompt[-1000:]
                    return name,{'query':query}
        return None

    def call(self,messages,tools=None,callbacks=None,available_functions=None):
        """Return deterministic text and execute only schema-authorized tool calls."""
        text=self._content(messages)
        # Tool result messages are already present; do not dispatch the same tool repeatedly.
        has_tool_result=any(self._as_dict(m).get('role') in {'tool','function'} for m in messages) if isinstance(messages,list) else False
        if tools and available_functions and not has_tool_result:
            selected=self._schema_driven_tool_call(messages,tools,available_functions)
            if selected:
                function_name,args=selected
                result=available_functions[function_name](**args)
                return f"Deterministic tool result ({function_name}): {result}"
        lower=text.lower()
        if 'response composer' in lower or 'compose a response' in lower or 'final response' in lower:
            return 'The customer response is composed only from the retrieved policy evidence and the supplied order lookup result.'
        if 'lookup agent' in lower or 'order lookup' in lower:
            return 'Use only the supplied order lookup result; do not invent order status.'
        if 'retrieval agent' in lower or 'policy evidence' in lower:
            return 'Use the retrieved policy passages and include their source document identifiers.'
        return 'I can answer only from the provided Nykaa support knowledge base and synthetic order records.'
