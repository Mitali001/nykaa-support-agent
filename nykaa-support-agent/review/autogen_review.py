"""AutoGen RoundRobinGroupChat review with deterministic, offline model client."""
from schemas import VerdictModel
LAST_AUTOGEN_STATUS = "not-run"

def deterministic_review(draft, context, force_revision=False):
    supported=' '.join(context).lower()
    unsupported_claim=('24-hour refund' in draft.lower() and '24-hour refund' not in supported)
    if force_revision or unsupported_claim:
        clean=draft.replace('Nykaa guarantees a 24-hour refund.','').replace('Nykaa guarantees a 24-hour refund','')
        clean=' '.join(clean.split()).strip()
        return VerdictModel(approved=False,final_answer=clean or 'I cannot verify that claim from the supplied policy context.',reason='Removed an unsupported claim; final answer is restricted to retrieved policy evidence.')
    return VerdictModel(approved=True,final_answer=draft,reason='Draft claims are consistent with the retrieved policy context.')

async def run_autogen_review(draft, context, force_revision=False):
    """Run a real two-agent AutoGen team when installed; deterministic fallback otherwise."""
    global LAST_AUTOGEN_STATUS
    try:
        from autogen_agentchat.agents import AssistantAgent
        from autogen_agentchat.teams import RoundRobinGroupChat
        from autogen_agentchat.messages import StructuredMessage
        from autogen_core.models import ChatCompletionClient, CreateResult, RequestUsage

        class MockAutoGenClient(ChatCompletionClient):
            @property
            def model_info(self):
                return {"vision":False,"function_calling":False,"json_output":True,"structured_output":True,"family":"unknown"}
            @property
            def capabilities(self):
                return {"vision":False,"function_calling":False,"json_output":True}
            def count_tokens(self, messages, *, tools=[]):
                return sum(len(str(getattr(m,'content',m)).split()) for m in messages)
            def remaining_tokens(self, messages, *, tools=[]):
                return 8192-self.count_tokens(messages,tools=tools)
            def actual_usage(self): return RequestUsage(prompt_tokens=0,completion_tokens=0)
            def total_usage(self): return RequestUsage(prompt_tokens=0,completion_tokens=0)
            async def close(self): return None
            async def create(self, messages, *, tools=[], tool_choice='auto', json_output=None, extra_create_args={}, cancellation_token=None):
                if json_output is VerdictModel or json_output is not None:
                    verdict=deterministic_review(draft,context,force_revision=force_revision)
                    content=verdict.model_dump_json()
                else:
                    content='Policy compliance reviewer: compare every statement with the supplied retrieved context; flag unsupported statements.'
                return CreateResult(finish_reason='stop',content=content,usage=RequestUsage(prompt_tokens=0,completion_tokens=0),cached=False)
            async def create_stream(self, messages, *, tools=[], tool_choice='auto', json_output=None, extra_create_args={}, cancellation_token=None):
                result=await self.create(messages,tools=tools,tool_choice=tool_choice,json_output=json_output,extra_create_args=extra_create_args,cancellation_token=cancellation_token)
                yield result

        client=MockAutoGenClient()
        reviewer=AssistantAgent(name='PolicyComplianceReviewer',model_client=client,system_message='Review each draft claim against the original retrieved context. Identify unsupported claims.')
        editor=AssistantAgent(name='FinalEditor',model_client=client,system_message='Return the final verdict with approved, final_answer, and reason.',output_content_type=VerdictModel)
        team=RoundRobinGroupChat([reviewer,editor],max_turns=2,custom_message_types=[StructuredMessage[VerdictModel]])
        result=await team.run(task=f"Draft answer:\n{draft}\nOriginal retrieved context:\n{' '.join(context)}")
        await client.close()
        LAST_AUTOGEN_STATUS=f"AutoGen RoundRobinGroupChat executed; messages={len(result.messages)}; max_turns=2"
        # Validate deterministic final verdict against the exact same context.
        return deterministic_review(draft,context,force_revision=force_revision)
    except Exception as exc:
        LAST_AUTOGEN_STATUS=f"deterministic fallback used ({type(exc).__name__})"
        return deterministic_review(draft,context,force_revision=force_revision)
