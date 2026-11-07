from pydantic import BaseModel, Field
from typing import List, Optional
class SupportResponse(BaseModel):
    answer: str
    intent: str
    grounded: bool
    sources: List[str]=Field(default_factory=list)
    order: Optional[dict]=None
    escalation_recommended: bool=False
    trace_id: Optional[str]=None
class VerdictModel(BaseModel):
    approved: bool
    final_answer: str
    reason: str
