"""Task 14: execute reviewer team for unchanged approval and injected-claim revision."""
import asyncio, json
import review.autogen_review as review_module
from review.autogen_review import run_autogen_review

async def main():
    context=['COD refunds are initiated after the return is approved and follow the supported refund method and payment-provider timeline.']
    approved=await run_autogen_review('COD refunds follow the supported refund method and provider processing timeline.',context)
    revised=await run_autogen_review('Nykaa guarantees a 24-hour refund. COD refunds follow the supported refund method.',context)
    print(json.dumps({"approved_case":approved.model_dump(),"revised_case":revised.model_dump(),"execution_status":review_module.LAST_AUTOGEN_STATUS},indent=2))
if __name__=='__main__': asyncio.run(main())
