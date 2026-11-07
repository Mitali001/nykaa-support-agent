import re
PHONE=re.compile(r'(?<!\d)(?:\+?91[- ]?)?[6-9]\d{9}(?!\d)')
CARD=re.compile(r'(?i)(?:card(?:\s*last\s*4)?|payment\s*card)\s*[:#-]?\s*(\d{4})')
INJECTION_PATTERNS=[r'ignore (all )?(previous|prior) instructions',r'reveal (the )?(system prompt|hidden prompt)',r'bypass (the )?guardrails',r'you are now .*admin']
def inspect_and_mask(text):
    original=text
    masked=PHONE.sub('[PHONE_MASKED]',text)
    masked=CARD.sub(lambda m:'[CARD_LAST4_MASKED]',masked)
    injection=any(re.search(p,masked,re.I) for p in INJECTION_PATTERNS)
    return {"safe":not injection,"text":masked,"pii_masked":masked!=original,"injection_detected":injection,"reason":"Prompt injection detected" if injection else None}
