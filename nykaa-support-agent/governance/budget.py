from config import MAX_REQUEST_TOKENS
class BudgetExceeded(ValueError): pass
def estimate_tokens(text): return max(1,len(text.split()))
def enforce_budget(text,limit=MAX_REQUEST_TOKENS):
    used=estimate_tokens(text)
    if used>limit: raise BudgetExceeded(f'Request budget exceeded: estimated {used} tokens > cap {limit}')
    return {"estimated_tokens":used,"limit":limit,"accepted":True}
