"""Order lookup tool and least-autonomy enforcement."""
import json, statistics
from pathlib import Path
from dataset.dataset import generate_orders
ORDERS={r['record_id']:r for r in generate_orders()}
DAYS=[r['days_since_created'] for r in ORDERS.values()]
P80=sorted(DAYS)[int(0.80*(len(DAYS)-1))]
ESCALATION_THRESHOLD=round(0.60+0.40*(P80/30.0),3)
LOOKUP_CALLS=0
class PermissionErrorForTool(RuntimeError): pass

def check_order_status(record_id: str, caller: str='Lookup Agent') -> dict:
    global LOOKUP_CALLS
    if caller!='Lookup Agent': raise PermissionErrorForTool('Only Lookup Agent is authorized to call check_order_status')
    LOOKUP_CALLS+=1
    row=ORDERS.get(record_id)
    if row is None: return {"found":False,"record_id":record_id,"error":"Order ID not found in synthetic dataset"}
    recency=row['days_since_created']/30.0
    score=round(0.60*int(row['delayed_shipment'])+0.40*recency,3)
    return {"found":True,"record_id":record_id,"status":row['status'],"order_value_inr":row['order_value_inr'],"days_since_created":row['days_since_created'],"delayed_shipment":row['delayed_shipment'],"escalation_score":score,"escalate":score>ESCALATION_THRESHOLD}

def escalation_design():
    return {"formula":"0.60 * delayed_shipment(0/1) + 0.40 * (days_since_created / 30)","threshold":ESCALATION_THRESHOLD,"dataset_days_p80":P80,"interpretation":f"Threshold equals 0.60 + 0.40*(P80/30) = {ESCALATION_THRESHOLD}; it is the composite score for a delayed order whose age is at the dataset's 80th-percentile recency ({P80} days)."}
