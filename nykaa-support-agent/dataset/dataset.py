"""Seeded, deterministic fabricated Nykaa-like order data. Run: python -m dataset.dataset"""
from __future__ import annotations
import json, random
from collections import Counter
from pathlib import Path
SEED=42; RECORD_COUNT=50
CATEGORIES=["Apparel","Electronics","Home","Footwear","Beauty"]
STATUSES=["Placed","Shipped","Delivered","Returned","Refunded"]
CATEGORY_WEIGHTS=[20,15,15,15,35]
STATUS_WEIGHTS=[15,25,35,15,10]
DELAY_PROBABILITY=0.20
MIN_ORDER_VALUE_INR=199; MAX_ORDER_VALUE_INR=14999

def generate_orders():
    rng=random.Random(SEED); rows=[]
    for i in range(1,RECORD_COUNT+1):
        rows.append({"record_id":f"NYK{i:04d}","category":rng.choices(CATEGORIES,weights=CATEGORY_WEIGHTS,k=1)[0],"status":rng.choices(STATUSES,weights=STATUS_WEIGHTS,k=1)[0],"order_value_inr":rng.randint(MIN_ORDER_VALUE_INR,MAX_ORDER_VALUE_INR),"days_since_created":rng.randint(0,30),"delayed_shipment":rng.random()<DELAY_PROBABILITY})
    return rows

def validate_orders(rows):
    assert len(rows)>=40
    required={"record_id","category","status","order_value_inr","days_since_created","delayed_shipment"}
    assert all(set(r)==required for r in rows)
    cc=Counter(r['category'] for r in rows); sc=Counter(r['status'] for r in rows)
    assert all(cc[x]>=3 for x in CATEGORIES), cc
    assert all(sc[x]>=1 for x in STATUSES), sc
    assert all(type(r['days_since_created']) is int and 0<=r['days_since_created']<=30 for r in rows)
    assert all(type(r['delayed_shipment']) is bool for r in rows)
    assert all(MIN_ORDER_VALUE_INR<=r['order_value_inr']<=MAX_ORDER_VALUE_INR for r in rows)
    pct=100*sum(r['delayed_shipment'] for r in rows)/len(rows)
    assert 10<=pct<=30, f"Delayed shipment rate {pct:.2f}% outside required band"
    return True

def report(rows):
    return {"record_count":len(rows),"seed":SEED,"category_weights":CATEGORY_WEIGHTS,"status_weights":STATUS_WEIGHTS,"amount_range_inr":[MIN_ORDER_VALUE_INR,MAX_ORDER_VALUE_INR],"category_counts":dict(sorted(Counter(r['category'] for r in rows).items())),"status_counts":dict(sorted(Counter(r['status'] for r in rows).items())),"delayed_count":sum(r['delayed_shipment'] for r in rows),"delayed_percentage":round(100*sum(r['delayed_shipment'] for r in rows)/len(rows),2)}

def main():
    rows=generate_orders(); validate_orders(rows)
    out=Path(__file__).with_name('orders.json'); out.write_text(json.dumps(rows,indent=2),encoding='utf-8')
    print(json.dumps(report(rows),indent=2)); print(f"Saved {len(rows)} orders to {out}")
if __name__=='__main__': main()
