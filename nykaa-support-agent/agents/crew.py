"""CrewAI crew definition. Tool execution is deterministic and permission-gated in service.py."""
import os
os.environ['CREWAI_DISABLE_TELEMETRY']='true'; os.environ['OTEL_SDK_DISABLED']='true'; os.environ['CREWAI_TRACING_ENABLED']='false'
from agents.mock_llm import DeterministicMockLLM
from schemas import SupportResponse

def build_crew(rag_tool=None,lookup_tool=None):
    try:
        from crewai import Agent, Task, Crew, Process
    except ImportError as exc: raise RuntimeError('CrewAI not installed. Install requirements.txt to run the real CrewAI crew.') from exc
    llm=DeterministicMockLLM()
    retrieval=Agent(role='Retrieval Agent',goal='Retrieve only relevant policy passages from the Nykaa knowledge base',backstory='Ground every policy answer in retrieved documents.',tools=[rag_tool] if rag_tool else [],llm=llm,verbose=False,allow_delegation=False)
    lookup=Agent(role='Lookup Agent',goal='Look up synthetic order records and calculate escalation scores',backstory='You are the only agent authorized to access order lookup.',tools=[lookup_tool] if lookup_tool else [],llm=llm,verbose=False,allow_delegation=False)
    composer=Agent(role='Response Composer',goal='Compose a concise grounded customer support response',backstory='Never invent policy facts; disclose uncertainty.',llm=llm,verbose=False,allow_delegation=False)
    t1=Task(description='Use the provided retrieved policy context for this customer query: {query}. Return source identifiers and evidence.',expected_output='Policy evidence and source IDs.',agent=retrieval)
    t2=Task(description='Use the provided order lookup result if present. Do not invent order data. Query: {query}. Lookup result: {order_result}',expected_output='Order status and escalation summary, or no order lookup needed.',agent=lookup)
    t3=Task(description='Compose a response from only the preceding task outputs. Query: {query}. Retrieved context: {context}. Order result: {order_result}',expected_output='A concise grounded customer support draft conforming to SupportResponse.',agent=composer,output_pydantic=SupportResponse)
    return Crew(agents=[retrieval,lookup,composer],tasks=[t1,t2,t3],process=Process.sequential,verbose=False)
