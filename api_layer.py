"""
═══════════════════════════════════════════════════════════════════════════════
  IntelliTrace 2026 — Enhanced API Layer
  File: api_layer.py
  Team: Cyber Dynamos
═══════════════════════════════════════════════════════════════════════════════
  NEW ENDPOINTS vs v1:
    GET  /graph/fan-in        → Mule Collection (Fan-In) alerts
    GET  /graph/loops         → Circular Loop detections
    GET  /graph/churn         → High-churn-rate accounts
    GET  /analytics/velocity  → velocity_l6h escalation patterns
    GET  /analytics/new-accounts → New accounts (age < 30 days)
    GET  /analytics/ip-density   → High ip_account_density clusters

  HOW TO RUN:
    pip install fastapi uvicorn
    python transaction_simulator.py   ← generate data first
    python api_layer.py
    → http://127.0.0.1:8000/docs
═══════════════════════════════════════════════════════════════════════════════
"""

import os, csv, json, uuid, datetime
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
import asyncio

try:
    from transaction_simulator import TransactionSimulator
    from graph_intelligence import GraphIntelligence
    MODULES = True
except ImportError:
    MODULES = False

app = FastAPI(
    title      = "IntelliTrace 2026 — Enhanced Mule Detection API",
    description= "Real-Time Cross-Channel Mule Account Detection\nTeam: Cyber Dynamos",
    version    = "2.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"], allow_credentials=True)

# ─── STATE ────────────────────────────────────────────────────────────────────

_txns:    List[Dict] = []
_report:  Dict       = {}
_alerts:  List[Dict] = []
_clients: List       = []
CSV_PATH = "transactions.csv"

# ─── MODELS ───────────────────────────────────────────────────────────────────

class TxnIn(BaseModel):
    name:             str   = Field(..., example="Arjun Sharma")
    account_number:   str   = Field(..., example="SB95822412")
    account_type:     str   = Field("Savings")
    mobile_number:    str   = Field(..., example="9914763202")
    pincode:          str   = Field(..., example="600001")
    narration:        str   = Field(..., example="Transfer")
    trans_type:       str   = Field(..., example="UPI Payment")
    amount:           float = Field(..., gt=0, example=5000.0)
    ip_address:       str   = Field(..., example="103.161.159.227")
    device:           str   = Field(..., example="iPhone 14")
    receiver_account: str   = Field("SELF")
    receiver_name:    str   = Field("Unknown")
    receiver_pincode: str   = Field("000000")
    account_age_days: float = Field(365.0)

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _risk_level(s: float) -> str:
    return "CRITICAL" if s>=90 else "HIGH" if s>=70 else "MEDIUM" if s>=40 else "LOW"

def calculate_risk_summary_matrix() -> List[Dict]:
    """
    Calculates the 4x4 Risk Summary Matrix data for the Dashboard.
    Buckets high-risk/mule accounts by Transaction Volume and Value.
    """
    if not _txns:
        return []

    mule_txns = [t for t in _txns if int(t.get("is_fraud", 0)) == 1]
    if not mule_txns: return []
    
    mule_aggregates = {}
    for txn in mule_txns:
        acc = txn['account_number']
        if acc not in mule_aggregates: mule_aggregates[acc] = {'vol': 0, 'val': 0}
        mule_aggregates[acc]['vol'] += 1
        mule_aggregates[acc]['val'] += float(txn['amount'])

    volume_bins = [1, 3, 6] 
    value_bins = [20000, 50000, 80000] 
    matrix = [[0 for _ in range(4)] for _ in range(4)]
    cat_labels = ["Low", "Medium", "High", "Critical"]

    for acc_data in mule_aggregates.values():
        vol = acc_data['vol']
        val = acc_data['val']
        vol_idx = 3 if vol > volume_bins[2] else 2 if vol > volume_bins[1] else 1 if vol > volume_bins[0] else 0
        val_idx = 3 if val > value_bins[2] else 2 if val > value_bins[1] else 1 if val > value_bins[0] else 0
        matrix[val_idx][vol_idx] += 1

    formatted_data = []
    for y in range(3, -1, -1):
        for x in range(4):
            formatted_data.append({"vol_cat": cat_labels[x], "val_cat": cat_labels[y],
                                   "vol_idx": x, "val_idx": y, "mule_count": matrix[y][x]})
    return formatted_data

def _load():
    global _txns, _report, _alerts
    if not os.path.exists(CSV_PATH):
        if MODULES:
            sim = TransactionSimulator(n_normal=200)
            sim.run(); sim.to_csv(CSV_PATH)
        else:
            return

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        raw = list(csv.DictReader(f))
    _txns = []
    for r in raw:
        r["amount"]             = float(r["amount"])
        r["risk_score"]         = float(r["risk_score"])
        r["is_fraud"]           = int(r["is_fraud"])
        r["account_age_days"]   = float(r.get("account_age_days", 365))
        r["velocity_l6h"]       = float(r.get("velocity_l6h", 1))
        r["churn_rate"]         = float(r.get("churn_rate", 0.1))
        r["ip_account_density"] = int(r.get("ip_account_density", 5))
        _txns.append(r)
    print(f"[API] {len(_txns)} transactions loaded.")

    if MODULES and os.path.exists(CSV_PATH):
        try:
            eng = GraphIntelligence(csv_path=CSV_PATH)
            _report = eng.analyze()
            eng._last_report = _report
            _build_alerts()
        except Exception as e:
            print(f"[API] Graph error: {e}")
    elif os.path.exists("graph_report.json"):
        with open("graph_report.json") as f:
            _report = json.load(f)
        _build_alerts()

def _build_alerts():
    global _alerts
    _alerts = []
    for v in _report.get("velocity_alerts", []):
        _alerts.append({"alert_id": f"A-VEL-{v['account'][-4:]}",
            "severity": "critical", "fraud_type": "High Velocity",
            "title": f"High Velocity: {v['txn_count']} txns/5min", # FIXED window_seconds BUG
            "account": v["account"], "risk_score": v["risk_score"],
            "timestamp": v.get("start_time","")})
    for c in _report.get("cross_channel", []):
        _alerts.append({"alert_id": f"A-CC-{c['account'][-4:]}",
            "severity": "critical", "fraud_type": "Cross Channel",
            "title": f"Cross-Channel: {c['description']}",
            "account": c["account"], "risk_score": c["risk_score"],
            "timestamp": c.get("time_1","")})
    for f in _report.get("fan_in_alerts", []):
        _alerts.append({"alert_id": f"A-FAN-{f['collector'][-4:]}",
            "severity": "critical", "fraud_type": "Mule Collection",
            "title": f"Fan-In: {f['sender_count']} mules → {f['collector']}",
            "account": f["collector"], "risk_score": f["risk_score"],
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    for l in _report.get("circular_loops", []):
        _alerts.append({"alert_id": f"A-LOOP-{str(uuid.uuid4())[:4].upper()}",
            "severity": "critical", "fraud_type": "Circular Loop",
            "title": f"Circular Loop: {l['description']}",
            "account": l["path"][0] if l["path"] else "",
            "risk_score": l["risk_score"],
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

# ─── STARTUP ──────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    _load()
    print(f"[API] ✅ Ready — {len(_txns)} txns, {len(_alerts)} alerts")

# ─── HEALTH ───────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    return {"status": "online", "version": "2.0", "transactions": len(_txns),
            "alerts": len(_alerts), "timestamp": datetime.datetime.now().isoformat()}

# ─── TRANSACTIONS ─────────────────────────────────────────────────────────────

@app.get("/transactions", tags=["Transactions"])
async def get_txns(
    fraud_only: bool = Query(False),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    fraud_type: Optional[str] = Query(None),
    min_churn: Optional[float] = Query(None, description="Filter by min churn_rate"),
    min_risk:  Optional[float] = Query(None, description="Filter by min risk_score"),
):
    data = _txns
    if fraud_only:       data = [t for t in data if t["is_fraud"]==1]
    if fraud_type:       data = [t for t in data if t["fraud_type"].lower()==fraud_type.lower()]
    if min_churn is not None: data = [t for t in data if t["churn_rate"] >= min_churn]
    if min_risk  is not None: data = [t for t in data if t["risk_score"] >= min_risk]
    return {"total": len(data), "offset": offset, "limit": limit,
            "transactions": data[offset: offset+limit]}

@app.get("/transactions/fraud", tags=["Transactions"])
async def get_fraud():
    fraud = [t for t in _txns if t["is_fraud"]==1]
    by_type = {}
    for t in fraud:
        by_type[t["fraud_type"]] = by_type.get(t["fraud_type"],0)+1
    return {"total": len(fraud), "transactions": fraud, "by_type": by_type}

@app.get("/transactions/{txn_id}", tags=["Transactions"])
async def get_txn(txn_id: str):
    t = next((x for x in _txns if x["txn_id"]==txn_id), None)
    if not t: raise HTTPException(404, f"Transaction {txn_id} not found")
    return t

@app.post("/transactions", tags=["Transactions"])
async def add_txn(inp: TxnIn):
    txn_id = str(uuid.uuid4())[:8].upper()
    ts     = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    risk = 5.0; flags = []; ftype = "Normal"

    # Checks
    same_ip = [t for t in _txns[-100:] if t["ip_address"]==inp.ip_address]
    if len(set(t["account_number"] for t in same_ip)) >= 3:
        risk += 30; flags.append("Shared IP cluster"); ftype = "Shared IP"

    recent = [t for t in _txns[-200:] if t["account_number"]==inp.account_number]
    if len(recent) >= 5:
        risk += 20; flags.append(f"High velocity: {len(recent)} recent"); ftype = "High Velocity"

    if inp.account_age_days < 30:
        risk += 15; flags.append(f"New account: {inp.account_age_days} days")

    if 9000 <= inp.amount < 10000:
        risk += 10; flags.append("Amount just under ₹10K — evasion pattern")

    # Fan-in check
    recv_count = sum(1 for t in _txns[-50:] if t["receiver_account"]==inp.receiver_account)
    if recv_count >= 5:
        risk += 35; flags.append(f"Fan-in: {recv_count} senders → same receiver"); ftype = "Mule Collection"

    # Churn estimate from historical
    acc_txns = [t for t in _txns if t["account_number"]==inp.account_number]
    avg_churn = (sum(t["churn_rate"] for t in acc_txns)/len(acc_txns)) if acc_txns else 0.1
    if avg_churn >= 0.85:
        risk += 15; flags.append(f"High churn rate: {avg_churn:.2f}")

    is_fraud = 1 if risk >= 40 else 0
    new_t = {
        "timestamp": ts, "txn_id": txn_id, "name": inp.name,
        "account_number": inp.account_number, "account_type": inp.account_type,
        "mobile_number": inp.mobile_number, "pincode": inp.pincode,
        "narration": inp.narration, "trans_type": inp.trans_type, "amount": inp.amount,
        "ip_address": inp.ip_address, "device": inp.device,
        "receiver_account": inp.receiver_account, "is_fraud": is_fraud,
        "fraud_type": ftype, "risk_score": round(min(risk,100),1),
        "account_age_days": inp.account_age_days,
        "receiver_name": inp.receiver_name, "receiver_pincode": inp.receiver_pincode,
        "velocity_l6h": float(len(recent)+1), "churn_rate": round(avg_churn,3),
        "ip_account_density": len(same_ip),
    }
    _txns.append(new_t)

    if is_fraud:
        alert = {"alert_id": f"A-NEW-{txn_id}", "severity": "critical",
                 "fraud_type": ftype, "title": f"New Fraud: {ftype}",
                 "account": inp.account_number, "risk_score": round(min(risk,100),1),
                 "timestamp": ts}
        _alerts.insert(0, alert)
        for q in _clients:
            await q.put(json.dumps(alert))

    return {"txn_id": txn_id, "risk_score": round(min(risk,100),1),
            "risk_level": _risk_level(risk), "is_fraud": is_fraud,
            "fraud_type": ftype, "flags": flags, "transaction": new_t}

# ─── ALERTS ───────────────────────────────────────────────────────────────────

@app.get("/alerts", tags=["Alerts"])
async def get_alerts(severity: Optional[str]=None):
    data = _alerts if not severity else [a for a in _alerts if a["severity"]==severity]
    return {"total": len(data), "alerts": data}

@app.get("/alerts/live", tags=["Alerts"])
async def live_alerts(request: Request):
    q: asyncio.Queue = asyncio.Queue()
    _clients.append(q)
    async def gen():
        try:
            for a in _alerts[:5]:
                yield f"data: {json.dumps(a)}\n\n"
                await asyncio.sleep(0.1)
            while True:
                if await request.is_disconnected(): break
                try:
                    a = await asyncio.wait_for(q.get(), timeout=30)
                    yield f"data: {a}\n\n"
                except asyncio.TimeoutError:
                    yield "data: {\"heartbeat\":true}\n\n"
        finally:
            _clients.remove(q)
    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})

# ─── GRAPH ────────────────────────────────────────────────────────────────────

@app.get("/graph/report",  tags=["Graph"]) 
async def graph_report():
    if not _report: raise HTTPException(503,"Run graph_intelligence.py first")
    return _report

@app.get("/graph/fan-in",  tags=["Graph"])
async def graph_fan_in():
    return {"fan_in_alerts": _report.get("fan_in_alerts",[]),
            "total": len(_report.get("fan_in_alerts",[]))}

@app.get("/graph/loops",   tags=["Graph"])
async def graph_loops():
    return {"circular_loops": _report.get("circular_loops",[]),
            "total": len(_report.get("circular_loops",[]))}

@app.get("/graph/churn",   tags=["Graph"])
async def graph_churn():
    return {"high_churn": _report.get("high_churn",[]),
            "total": len(_report.get("high_churn",[]))}

# ─── ANALYTICS ────────────────────────────────────────────────────────────────

@app.get("/analytics/velocity", tags=["Analytics"])
async def analytics_velocity():
    """Accounts with escalating velocity_l6h (rising pattern = fraud signal)."""
    from collections import defaultdict
    acc_vel: Dict[str, list] = defaultdict(list)
    for t in _txns:
        acc_vel[t["account_number"]].append(float(t.get("velocity_l6h",1)))
    escalating = []
    for acc, vels in acc_vel.items():
        if len(vels)>2 and vels[-1] > vels[0] and max(vels)>=3:
            escalating.append({"account":acc,
                "name": next((t["name"] for t in _txns if t["account_number"]==acc), "?"),
                "velocity_pattern": vels, "max_velocity": max(vels)})
    return {"escalating_accounts": escalating, "total": len(escalating)}

@app.get("/analytics/new-accounts", tags=["Analytics"])
async def analytics_new_accounts():
    """Accounts younger than 30 days involved in transactions."""
    new_accs = {}
    for t in _txns:
        age = float(t.get("account_age_days",365))
        if age < 30:
            acc = t["account_number"]
            if acc not in new_accs:
                new_accs[acc] = {"account": acc, "name": t["name"],
                    "account_age_days": age, "is_fraud": t["is_fraud"],
                    "churn_rate": t.get("churn_rate", 0), "txn_count": 0}
            new_accs[acc]["txn_count"] += 1
    return {"new_accounts": list(new_accs.values()), "total": len(new_accs)}

@app.get("/analytics/ip-density", tags=["Analytics"])
async def analytics_ip_density():
    """IPs with high account density (many accounts using same IP)."""
    from collections import defaultdict
    ip_data: Dict[str, dict] = {}
    for t in _txns:
        ip = t["ip_address"]
        if ip not in ip_data:
            ip_data[ip] = {"ip": ip, "density": int(t.get("ip_account_density",1)),
                "accounts": set(), "fraud_count": 0}
        ip_data[ip]["accounts"].add(t["account_number"])
        if t["is_fraud"]: ip_data[ip]["fraud_count"] += 1

    dense = [{"ip":d["ip"],"density":d["density"],"unique_accounts":len(d["accounts"]),
              "fraud_count":d["fraud_count"],"accounts":list(d["accounts"])}
             for d in ip_data.values() if d["density"] >= 15]
    dense.sort(key=lambda x:x["density"],reverse=True)
    return {"dense_ips": dense, "total": len(dense)}

# ─── RISK ─────────────────────────────────────────────────────────────────────

@app.get("/risk/{account_number}", tags=["Risk"])
async def get_risk(account_number: str):
    acc_txns = [t for t in _txns if t["account_number"]==account_number]
    if not acc_txns: raise HTTPException(404, f"Account {account_number} not found")
    max_risk  = max(t["risk_score"] for t in acc_txns)
    avg_churn = sum(t["churn_rate"] for t in acc_txns) / len(acc_txns)
    min_age   = min(float(t["account_age_days"]) for t in acc_txns)
    max_vel   = max(float(t.get("velocity_l6h",1)) for t in acc_txns)
    fraud_txns = [t for t in acc_txns if t["is_fraud"]]
    flags = []
    if avg_churn >= 0.85: flags.append(f"High churn: {avg_churn:.3f}")
    if min_age < 30:      flags.append(f"New account: {min_age:.0f} days")
    if max_vel >= 3:      flags.append(f"High velocity: {max_vel:.0f} in 6h")
    if fraud_txns:        flags.extend([f"Fraud type: {ft}" for ft in set(t["fraud_type"] for t in fraud_txns)])
    if not flags:         flags = ["No specific flags — monitor"]

    recs = {"LOW":"Normal activity.","MEDIUM":"Monitor account.",
            "HIGH":"Block transfers, KYC review.","CRITICAL":"Freeze immediately, file SAR."}
    level = _risk_level(max_risk)
    return {"account_number": account_number, "risk_score": max_risk,
            "risk_level": level, "avg_churn_rate": round(avg_churn,3),
            "min_account_age_days": min_age, "max_velocity_l6h": max_vel,
            "fraud_flags": flags, "recommendation": recs[level],
            "transaction_count": len(acc_txns), "fraud_count": len(fraud_txns)}

# ─── DASHBOARD / MATRIX ───────────────────────────────────────────────────────

@app.get("/api/dashboard/stats", tags=["Dashboard"])
async def get_matrix_dashboard_stats():
    """Specific KPI stats for the Matrix Dashboard HTML view."""
    fraud = [t for t in _txns if t["is_fraud"] == 1]
    critical_alerts = [a for a in _alerts if a["severity"] == "critical"]
    total_fraud_amt = sum(t["amount"] for t in fraud)
    
    mule_nodes = 0
    if _report and "mule_chains" in _report:
        mule_nodes = sum(m.get("length", 0) for m in _report["mule_chains"])
    else:
        mule_nodes = len(set(t["account_number"] for t in fraud))

    return {
        "total_transactions": len(_txns),
        "critical_alerts": len(critical_alerts),
        "flagged_amount": total_fraud_amt,
        "mule_nodes_detected": mule_nodes
    }

@app.get("/api/risk_matrix", tags=["Dashboard"])
async def get_risk_matrix():
    """Retrieves binned data for the 4x4 Risk Summary Matrix."""
    matrix_data = calculate_risk_summary_matrix()
    return matrix_data

# ─── STATS ────────────────────────────────────────────────────────────────────

@app.get("/stats", tags=["Dashboard"])
async def get_stats():
    fraud = [t for t in _txns if t["is_fraud"]]
    by_type = {}
    for t in fraud: by_type[t["fraud_type"]] = by_type.get(t["fraud_type"],0)+1
    return {
        "total_transactions":  len(_txns),
        "fraud_transactions":  len(fraud),
        "normal_transactions": len(_txns)-len(fraud),
        "fraud_rate_pct":      round(len(fraud)/max(len(_txns),1)*100,2),
        "total_fraud_amount":  round(sum(t["amount"] for t in fraud),2),
        "max_risk_score":      max((t["risk_score"] for t in fraud),default=0),
        "avg_churn_fraud":     round(sum(t["churn_rate"] for t in fraud)/max(len(fraud),1),3) if fraud else 0,
        "alerts_count":        len(_alerts),
        "by_fraud_type":       by_type,
        "fan_in_alerts":       len(_report.get("fan_in_alerts",[])),
        "circular_loops":      len(_report.get("circular_loops",[])),
    }

@app.get("/fraud-story", tags=["Dashboard"])
async def fraud_stories():
    return {"stories": [
        {"id":"S1","title":"Mule Chain: Arjun→Priya→Karthik","fraud_type":"Mule Chain",
         "risk_score":91.0,"ip":"103.161.159.227","device":"iPhone 14","duration":"1m 40s",
         "amounts":[50000,48000,46000],"churn":[0.975,0.982,0.943]},
        {"id":"S2","title":"Shared Device: Samsung S23","fraud_type":"Shared Device",
         "risk_score":86.0,"ip":"103.221.93.148","device":"Samsung S23",
         "accounts":5,"window_min":8,"total_amount":135000},
        {"id":"S3","title":"High Velocity: 8 IMPS in 4min","fraud_type":"High Velocity",
         "risk_score":93.5,"ip":"103.50.181.18","velocity_peak":9,
         "total_amount":77120,"evasion":"All <₹10K"},
        {"id":"S4","title":"Cross Channel: Chennai+Delhi 45s","fraud_type":"Cross Channel",
         "risk_score":95.0,"delta_seconds":45,"amount_1":20000,"amount_2":35000},
        {"id":"S5","title":"Mule Collection: 8 Accounts → COLL_ACC_01","fraud_type":"Mule Collection",
         "risk_score":90.0,"ip":"103.50.181.18","device":"OnePlus 11",
         "sender_count":8,"collector":"COLL_ACC_01","account_age":5},
        {"id":"S6","title":"Circular Loop: Alpha→Beta→Gamma→Alpha","fraud_type":"Circular Loop",
         "risk_score":93.0,"ip":"192.168.1.1","device":"OnePlus 11",
         "cycle":["ACC_A","ACC_B","ACC_C","ACC_A"],"amounts":[10000,9900,9800]},
    ]}

# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("╔══════════════════════════════════════════╗")
    print("║  IntelliTrace — API Layer v2             ║")
    print("║  Cyber Dynamos · 2026                    ║")
    print("╚══════════════════════════════════════════╝\n")
    print("[API] http://127.0.0.1:8000/docs\n")
    uvicorn.run("api_layer:app", host="127.0.0.1", port=8000, reload=True)