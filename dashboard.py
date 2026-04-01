"""
═══════════════════════════════════════════════════════════════════════════════
  IntelliTrace 2026 — Enhanced UI Dashboard (V2 Updated)
  File: dashboard.py
  Team: Cyber Dynamos
═══════════════════════════════════════════════════════════════════════════════
"""

import os, csv, json, datetime
from typing import List, Dict, Any
from flask import Flask, render_template_string, jsonify, request

try:
    import requests as req_lib
    REQUESTS = True
except ImportError:
    REQUESTS = False

app  = Flask(__name__)
app.config["SECRET_KEY"] = "intellitrace-v2-hackathon-2026"
API_BASE  = "http://127.0.0.1:8000"
CHAT_BASE = "http://127.0.0.1:8001"
CSV_PATH  = "transactions.csv"


# ─── DATA ─────────────────────────────────────────────────────────────────────

def _load() -> List[Dict]:
    if not os.path.exists(CSV_PATH): return []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["amount"]             = float(r["amount"])
        r["risk_score"]         = float(r["risk_score"])
        r["is_fraud"]           = int(r["is_fraud"])
        r["account_age_days"]   = float(r.get("account_age_days",365))
        r["velocity_l6h"]       = float(r.get("velocity_l6h",1))
        r["churn_rate"]         = float(r.get("churn_rate",0.1))
        r["ip_account_density"] = int(r.get("ip_account_density",5))
    return rows

def _chat(msg: str) -> str:
    if not REQUESTS: return "Install 'requests' and start ai_chatbot.py --api"
    try:
        r = req_lib.post(f"{CHAT_BASE}/chat", json={"message":msg}, timeout=10)
        return r.json().get("response","No response")
    except Exception:
        return "Chatbot offline. Start: python ai_chatbot.py --api"


BADGE = {
    "Normal":         "b-n",
    "Mule Chain":     "b-m",
    "Shared Device":  "b-d",
    "High Velocity":  "b-v",
    "Cross Channel":  "b-c",
    "Mule Collection":"b-f",
    "Circular Loop":  "b-l",
}

FT_COLORS = {
    "Mule Chain":     "#ffb700",
    "Shared Device":  "#c864ff",
    "High Velocity":  "#ff3c5a",
    "Cross Channel":  "#00d4ff",
    "Mule Collection":"#ff6a00",
    "Circular Loop":  "#ff00ff",
}

ALERTS_STATIC = [
    {"title":"🔴 Mule Collection: 8 Mules → COLL_ACC_01","meta":"2025-07-02 10:00–10:07 · IP: 103.50.181.18 · acct age: 5d","risk":90},
    {"title":"🔴 Circular Loop: Alpha→Beta→Gamma→Alpha","meta":"2025-07-02 15:00–15:10 · IP: 192.168.1.1 · churn >0.95","risk":93},
    {"title":"🔴 Cross Channel: Saranya Venkat 45s apart","meta":"2025-06-10 11:05 · Chennai ATM + Delhi Net Banking","risk":95},
    {"title":"🔴 High Velocity: Senthil Kumar 8 IMPS/4min","meta":"2025-06-09 16:00 · velocity_l6h peaks at 9","risk":93},
    {"title":"🔴 Mule Chain: Arjun→Priya→Karthik","meta":"2025-06-05 14:00 · IP: 103.161.159.227 · iPhone 14","risk":91},
    {"title":"⚠ Shared Device: Samsung S23 · 5 Accounts","meta":"2025-06-07 10:30–38 · ip_account_density: 14","risk":86},
    {"title":"⚡ High Churn: Priya Nair churn 0.982","meta":"2025-06-05 14:00:50 · Mule Chain hop 2","risk":88},
    {"title":"⚡ New Account: FAN accounts age=5 days","meta":"2025-07-02 · 8 throwaway accounts detected","risk":90},
]


# ─── TEMPLATE ─────────────────────────────────────────────────────────────────

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>IntelliTrace 2026 v2</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&family=Exo+2:wght@300;400;600;800&display=swap');
:root{--bg:#040c14;--bg2:#071420;--bg3:#0a1d2e;--panel:#0d2035;--panel2:#0f2540;
  --border:#1a4060;--border2:#1e4f78;--accent:#00d4ff;--accent2:#00ff9d;
  --danger:#ff3c5a;--warn:#ffb700;--orange:#ff6a00;--purple:#ff00ff;
  --text:#c8e8ff;--text2:#7aadcc;--text3:#4a7a9a;}
*{margin:0;padding:0;box-sizing:border-box;}
body{background:var(--bg);color:var(--text);font-family:'Exo 2',sans-serif;font-size:13px;}
body::before{content:'';position:fixed;top:0;left:0;right:0;bottom:0;
  background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,212,255,.015) 2px,rgba(0,212,255,.015) 4px);
  pointer-events:none;z-index:9999;}
.header{display:flex;align-items:center;justify-content:space-between;padding:12px 28px;
  background:linear-gradient(90deg,#040c14,#071e35 50%,#040c14);
  border-bottom:1px solid var(--border2);position:sticky;top:0;z-index:100;}
.brand{font-family:'Rajdhani',sans-serif;font-size:22px;font-weight:700;color:var(--accent);letter-spacing:2px;}
.sub{font-size:10px;color:var(--text3);letter-spacing:3px;text-transform:uppercase;}
.live-dot{width:8px;height:8px;border-radius:50%;background:var(--accent2);
  animation:blink 1.2s ease-in-out infinite;box-shadow:0 0 8px var(--accent2);display:inline-block;margin-right:6px;}
@keyframes blink{0%,100%{opacity:1;}50%{opacity:.2;}}
.hstat .val{font-family:'Rajdhani',sans-serif;font-size:18px;font-weight:800;}
.nav-tabs{display:flex;background:var(--bg2);border-bottom:1px solid var(--border);padding:0 20px;}
.nav-tab{padding:10px 20px;cursor:pointer;font-family:'Rajdhani',sans-serif;font-size:13px;
  font-weight:600;letter-spacing:1px;color:var(--text3);border-bottom:3px solid transparent;transition:all .2s;text-transform:uppercase;}
.nav-tab.active{color:var(--accent);border-bottom-color:var(--accent);}
.main{padding:16px 20px;}
.tab-content{display:none;}.tab-content.active{display:block;}
.kpi-strip{display:grid;grid-template-columns:repeat(7,1fr);gap:10px;margin-bottom:14px;}
.kpi{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:12px 14px;position:relative;overflow:hidden;}
.kpi::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;}
.kpi.red::before{background:linear-gradient(90deg,var(--danger),transparent);}
.kpi.blue::before{background:linear-gradient(90deg,var(--accent),transparent);}
.kpi.green::before{background:linear-gradient(90deg,var(--accent2),transparent);}
.kpi.yellow::before{background:linear-gradient(90deg,var(--warn),transparent);}
.kpi.orange::before{background:linear-gradient(90deg,var(--orange),transparent);}
.kpi.purple::before{background:linear-gradient(90deg,var(--purple),transparent);}
.kpi-val{font-family:'Rajdhani',sans-serif;font-size:26px;font-weight:800;line-height:1;}
.kpi.red .kpi-val{color:var(--danger);} .kpi.blue .kpi-val{color:var(--accent);}
.kpi.green .kpi-val{color:var(--accent2);} .kpi.yellow .kpi-val{color:var(--warn);}
.kpi.orange .kpi-val{color:var(--orange);} .kpi.purple .kpi-val{color:var(--purple);}
.kpi-lbl{font-size:10px;color:var(--text3);text-transform:uppercase;letter-spacing:1.5px;margin-top:4px;}
.kpi-sub{font-size:10px;color:var(--text3);margin-top:2px;font-family:'Share Tech Mono',monospace;}
.grid-wide{display:grid;grid-template-columns:2fr 1fr;gap:12px;margin-bottom:12px;}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;}
.grid-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:12px;}
.panel{background:var(--panel);border:1px solid var(--border);border-radius:10px;overflow:hidden;}
.ph{display:flex;align-items:center;justify-content:space-between;padding:10px 16px;background:var(--panel2);border-bottom:1px solid var(--border);}
.pt{font-family:'Rajdhani',sans-serif;font-size:13px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--accent);}
.pb{padding:14px;}
.alert-feed{max-height:320px;overflow-y:auto;}
.ai{display:flex;gap:10px;align-items:flex-start;padding:10px 14px;border-bottom:1px solid var(--border);cursor:pointer;}
.ai:hover{background:rgba(0,212,255,.04);}
.sev{width:6px;height:6px;border-radius:50%;margin-top:4px;flex-shrink:0;}
.sc{background:var(--danger);box-shadow:0 0 6px var(--danger);}
.sh{background:var(--warn);}
.at{font-size:12px;font-weight:600;color:var(--text);}
.am{font-size:10px;color:var(--text3);font-family:'Share Tech Mono',monospace;}
.asc{font-family:'Rajdhani',sans-serif;font-size:18px;font-weight:700;color:var(--danger);}
.ft-item{margin-bottom:10px;}
.ft-hdr{display:flex;justify-content:space-between;font-size:11px;margin-bottom:4px;color:var(--text2);}
.bt{height:6px;background:var(--bg3);border-radius:3px;overflow:hidden;}
.bf{height:100%;border-radius:3px;transition:width 1.5s ease;}
#graph-cont{width:100%;height:440px;background:radial-gradient(ellipse at center,#0a1d30,#040c14);border-radius:8px;position:relative;overflow:hidden;}
#graph-cont svg{width:100%;height:100%;}
.gl{display:flex;gap:12px;padding:8px 14px;border-top:1px solid var(--border);background:var(--bg2);flex-wrap:wrap;}
.li{display:flex;align-items:center;gap:6px;font-size:11px;color:var(--text3);}
.ld{width:10px;height:10px;border-radius:50%;}
.tw{max-height:420px;overflow-y:auto;}
.dt{width:100%;border-collapse:collapse;}
.dt th{padding:8px 10px;text-align:left;font-size:10px;text-transform:uppercase;letter-spacing:1.5px;color:var(--text3);font-weight:600;border-bottom:1px solid var(--border2);position:sticky;top:0;background:var(--panel2);}
.dt td{padding:6px 10px;font-size:11px;border-bottom:1px solid rgba(26,64,96,.4);font-family:'Share Tech Mono',monospace;vertical-align:middle;}
.dt tr:hover td{background:rgba(0,212,255,.03);}
.badge{display:inline-block;padding:2px 7px;border-radius:4px;font-size:10px;font-weight:600;font-family:'Rajdhani',sans-serif;}
.b-n{background:rgba(0,255,157,.1);color:var(--accent2);border:1px solid rgba(0,255,157,.25);}
.b-m{background:rgba(255,183,0,.15);color:var(--warn);border:1px solid rgba(255,183,0,.3);}
.b-d{background:rgba(200,100,255,.15);color:#c864ff;border:1px solid rgba(200,100,255,.3);}
.b-v{background:rgba(255,60,90,.2);color:var(--danger);border:1px solid rgba(255,60,90,.4);}
.b-c{background:rgba(0,212,255,.15);color:var(--accent);border:1px solid rgba(0,212,255,.3);}
.b-f{background:rgba(255,106,0,.2);color:var(--orange);border:1px solid rgba(255,106,0,.4);}
.b-l{background:rgba(255,0,255,.15);color:var(--purple);border:1px solid rgba(255,0,255,.3);}
.sp{background:linear-gradient(135deg,#0d1f2f,#0a1520);border:1px solid var(--border2);border-radius:10px;padding:16px;margin-bottom:12px;position:relative;overflow:hidden;}
.sp::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;
  background:linear-gradient(90deg,var(--danger),var(--warn),var(--danger));animation:ss 3s linear infinite;background-size:200% 100%;}
@keyframes ss{0%{background-position:0%}100%{background-position:200%}}
.stitle{font-family:'Rajdhani',sans-serif;font-size:16px;font-weight:700;color:var(--danger);margin-bottom:10px;}
.chain{display:flex;align-items:center;gap:0;flex-wrap:wrap;margin-bottom:12px;}
.cn{background:var(--panel2);border:1px solid var(--border2);border-radius:6px;padding:6px 12px;font-family:'Share Tech Mono',monospace;font-size:11px;color:var(--accent);}
.cn.atm{border-color:var(--danger);color:var(--danger);}
.ca{color:var(--warn);font-size:16px;padding:0 4px;}
.ct{font-size:10px;color:var(--text3);display:block;margin-top:2px;}
.sf{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;}
.fi{background:var(--bg3);border-radius:6px;padding:8px;border-left:3px solid var(--danger);}
.fv{font-family:'Rajdhani',sans-serif;font-size:18px;font-weight:700;color:var(--danger);}
.fl{font-size:10px;color:var(--text3);}
.signal-row{display:flex;align-items:center;gap:10px;padding:8px 14px;border-bottom:1px solid var(--border);}
.sig-icon{font-size:18px;width:28px;text-align:center;}
.sig-info{flex:1;}
.sig-name{font-size:12px;color:var(--text);}
.sig-desc{font-size:10px;color:var(--text3);font-family:'Share Tech Mono',monospace;}
.sig-val{font-family:'Rajdhani',sans-serif;font-size:18px;font-weight:700;}
.chat-wrap{display:flex;flex-direction:column;height:480px;}
.chat-msgs{flex:1;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:10px;}
.msg{max-width:80%;padding:10px 14px;border-radius:10px;font-size:12px;line-height:1.6;animation:mi .3s ease;}
@keyframes mi{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
.msg.bot{background:var(--panel2);border:1px solid var(--border2);align-self:flex-start;}
.msg.user{background:linear-gradient(135deg,#0a2a45,#0d3558);border:1px solid var(--accent);align-self:flex-end;color:var(--accent);}
.ms{font-size:10px;font-weight:700;letter-spacing:1px;margin-bottom:4px;text-transform:uppercase;}
.ms.bot{color:var(--accent2);} .ms.usr{color:var(--accent);}
.ci{display:flex;gap:8px;padding:10px 14px;border-top:1px solid var(--border);background:var(--bg2);}
.cin{flex:1;background:var(--bg3);border:1px solid var(--border2);border-radius:6px;padding:8px 12px;color:var(--text);font-size:12px;font-family:'Exo 2',sans-serif;outline:none;}
.cin:focus{border-color:var(--accent);}
.csend{background:linear-gradient(135deg,#0a3a5a,#0d4a7a);border:1px solid var(--accent);color:var(--accent);padding:8px 16px;border-radius:6px;cursor:pointer;font-family:'Rajdhani',sans-serif;font-size:13px;font-weight:700;}
.csend:hover{background:rgba(0,212,255,.15);}
.qbs{display:flex;gap:6px;flex-wrap:wrap;padding:8px 14px;border-bottom:1px solid var(--border);background:var(--bg2);}
.qb{background:var(--bg3);border:1px solid var(--border2);color:var(--text3);border-radius:4px;padding:4px 10px;font-size:10px;cursor:pointer;font-family:'Share Tech Mono',monospace;transition:all .2s;}
.qb:hover{border-color:var(--accent);color:var(--accent);}
.typing span{width:5px;height:5px;border-radius:50%;background:var(--accent2);display:inline-block;animation:dot 1.2s ease-in-out infinite;}
.typing span:nth-child(2){animation-delay:.2s;} .typing span:nth-child(3){animation-delay:.4s;}
@keyframes dot{0%,80%,100%{transform:scale(.6);opacity:.4;}40%{transform:scale(1);opacity:1;}}
::-webkit-scrollbar{width:4px;} ::-webkit-scrollbar-thumb{background:var(--border2);border-radius:2px;}
</style>
</head>
<body>

<div class="header">
  <div>
    <div class="brand">IntelliTrace <span style="font-size:14px;color:var(--text3)">v2</span></div>
    <div class="sub">Enhanced Mule Detection · Cyber Dynamos 2026</div>
  </div>
  <div style="font-size:11px;color:var(--text3);font-family:'Share Tech Mono',monospace">
    <span class="live-dot"></span>LIVE&nbsp;|&nbsp;<span id="clock">--:--:--</span>&nbsp;|&nbsp;
    API:<span id="api-s" style="color:var(--warn)">Checking...</span>
  </div>
  <div style="display:flex;gap:20px">
    <div class="hstat"><div class="val" style="color:var(--danger)">{{ stats.blocked }}</div><div style="font-size:9px;color:var(--text3)">BLOCKED IPs</div></div>
    <div class="hstat"><div class="val" style="color:var(--danger)">{{ stats.fraud }}</div><div style="font-size:9px;color:var(--text3)">ALERTS</div></div>
    <div class="hstat"><div class="val" style="color:var(--warn)">{{ stats.max_risk }}</div><div style="font-size:9px;color:var(--text3)">PEAK RISK</div></div>
    <div class="hstat"><div class="val" style="color:var(--accent)">{{ stats.total }}</div><div style="font-size:9px;color:var(--text3)">TXNS</div></div>
    <div class="hstat"><div class="val" style="color:var(--orange)">6</div><div style="font-size:9px;color:var(--text3)">PATTERNS</div></div>
  </div>
</div>

<div class="nav-tabs">
  <div class="nav-tab active" onclick="showTab('overview',this)">📊 Overview</div>
  <div class="nav-tab" onclick="showTab('graph',this)">🕸 Graph</div>
  <div class="nav-tab" onclick="showTab('transactions',this)">📋 Transactions</div>
  <div class="nav-tab" onclick="showTab('signals',this)">⚡ Signals</div>
  <div class="nav-tab" onclick="showTab('story',this)">📖 Fraud Stories</div>
  <div class="nav-tab" onclick="showTab('chatbot',this)">🤖 AI Assistant</div>
</div>

<div class="main">

<!-- ═══ OVERVIEW ══════════════════════════════════════════════════════════════ -->
<div class="tab-content active" id="tab-overview">
  <div class="kpi-strip">
    <div class="kpi red"><div class="kpi-val">{{ stats.fraud }}</div><div class="kpi-lbl">Fraud Alerts</div><div class="kpi-sub">6 pattern types</div></div>
    <div class="kpi blue"><div class="kpi-val">{{ stats.total }}</div><div class="kpi-lbl">Transactions</div><div class="kpi-sub">Jun–Jul 2025</div></div>
    <div class="kpi yellow"><div class="kpi-val">{{ stats.max_risk }}</div><div class="kpi-lbl">Peak Risk</div><div class="kpi-sub">Cross Channel</div></div>
    <div class="kpi green"><div class="kpi-val">91.7%</div><div class="kpi-lbl">Detection Rate</div></div>
    <div class="kpi orange"><div class="kpi-val">8</div><div class="kpi-lbl">Fan-In Mules</div><div class="kpi-sub">→ COLL_ACC_01</div></div>
    <div class="kpi purple"><div class="kpi-val">3</div><div class="kpi-lbl">Circular Loop</div><div class="kpi-sub">A→B→C→A</div></div>
    <div class="kpi red"><div class="kpi-val">₹3.5L</div><div class="kpi-lbl">Fraud Amount</div><div class="kpi-sub">29 txns</div></div>
  </div>

  <div class="grid-wide">
    <div class="panel">
      <div class="ph"><div class="pt">🚨 Live Alert Feed</div></div>
      <div class="alert-feed">
        {% for a in alerts %}
        <div class="ai">
          <div class="sev {{ 'sc' if a.risk >= 90 else 'sh' }}"></div>
          <div style="flex:1">
            <div class="at">{{ a.title }}</div>
            <div class="am">{{ a.meta }}</div>
          </div>
          <div class="asc">{{ a.risk }}</div>
        </div>
        {% endfor %}
      </div>
    </div>

    <div class="panel">
      <div class="ph"><div class="pt">📊 Fraud Breakdown</div></div>
      <div class="pb">
        {% for ft in fraud_types %}
        <div class="ft-item">
          <div class="ft-hdr"><span>{{ ft.name }}</span><span style="color:{{ ft.color }}">{{ ft.count }} txns</span></div>
          <div class="bt"><div class="bf" style="width:{{ ft.pct }}%;background:{{ ft.color }}"></div></div>
        </div>
        {% endfor %}
      </div>
    </div>
  </div>
</div>

<!-- ═══ GRAPH ════════════════════════════════════════════════════════════════ -->
<div class="tab-content" id="tab-graph">
  <div class="panel" style="margin-bottom:12px">
    <div class="ph">
      <div class="pt">🕸 Graph Intelligence — 6 Fraud Patterns</div>
      <div style="display:flex;gap:8px">
        <button class="qb" onclick="resetGraph()">Reset</button>
        <button class="qb" onclick="showFraud()">Fraud Nodes</button>
        <button class="qb" onclick="showFanIn()">Fan-In</button>
        <button class="qb" onclick="showLoop()">Circular Loop</button>
      </div>
    </div>
    <div id="graph-cont"><svg id="g-svg"></svg></div>
    <div class="gl">
      <div class="li"><div class="ld" style="background:#ff3c5a"></div>Mule Chain</div>
      <div class="li"><div class="ld" style="background:#c864ff"></div>Shared Device</div>
      <div class="li"><div class="ld" style="background:#ff6a00"></div>Fan-In / Collector</div>
      <div class="li"><div class="ld" style="background:#ff00ff"></div>Circular Loop</div>
      <div class="li"><div class="ld" style="background:#00ff9d"></div>IP Node</div>
      <div class="li"><div class="ld" style="background:#7eb8ff"></div>Device Node</div>
      <div class="li"><div class="ld" style="background:#00d4ff"></div>Normal Account</div>
    </div>
  </div>
</div>

<!-- ═══ TRANSACTIONS ══════════════════════════════════════════════════════════ -->
<div class="tab-content" id="tab-transactions">
  <div class="panel">
    <div class="ph">
      <div class="pt">📋 Transaction Log — {{ stats.total }} Records · 22 Columns</div>
      <select id="flt" style="background:var(--bg3);border:1px solid var(--border2);color:var(--text3);border-radius:4px;padding:4px 8px;font-size:11px;outline:none" onchange="filterTable()">
        <option value="all">All</option><option value="1">Fraud</option><option value="0">Normal</option>
      </select>
    </div>
    <div class="tw">
      <table class="dt">
        <thead>
          <tr>
            <th>TXN ID</th><th>TIMESTAMP</th><th>NAME</th><th>ACCOUNT</th>
            <th>AMOUNT</th><th>DEVICE</th><th>IP</th><th>RECV PIN</th>
            <th>VEL/6H</th><th>CHURN</th><th>IP DENS</th><th>AGE(d)</th>
            <th>FRAUD TYPE</th><th>RISK</th>
          </tr>
        </thead>
        <tbody id="txn-body">
          {% for t in transactions %}
          <tr data-fraud="{{ t.is_fraud }}">
            <td style="color:var(--accent)">{{ t.txn_id }}</td>
            <td>{{ t.timestamp[:16] }}</td>
            <td style="color:var(--text)">{{ t.name }}</td>
            <td style="color:var(--text2)">{{ t.account_number }}</td>
            <td style="color:var(--warn);font-family:'Rajdhani',sans-serif;font-weight:700">₹{{ "{:,.0f}".format(t.amount) }}</td>
            <td style="color:var(--text3)">{{ t.device[:12] }}</td>
            <td style="color:var(--text3)">{{ t.ip_address }}</td>
            <td style="color:var(--text3)">{{ t.receiver_pincode }}</td>
            <td style="color:{{ '#ff3c5a' if t.velocity_l6h >= 5 else '#ffb700' if t.velocity_l6h >= 3 else 'var(--text3)' }}">{{ t.velocity_l6h }}</td>
            <td style="color:{{ '#ff3c5a' if t.churn_rate >= 0.85 else '#ffb700' if t.churn_rate >= 0.5 else 'var(--text3)' }}">{{ "%.3f"|format(t.churn_rate) }}</td>
            <td style="color:{{ '#ff3c5a' if t.ip_account_density >= 15 else 'var(--text3)' }}">{{ t.ip_account_density }}</td>
            <td style="color:{{ '#ff3c5a' if t.account_age_days < 30 else 'var(--text3)' }}">{{ "%.0f"|format(t.account_age_days) }}</td>
            <td><span class="badge {{ t.badge }}">{{ t.fraud_type }}</span></td>
            <td style="color:{{ '#ff3c5a' if t.risk_score >= 80 else '#ffb700' if t.risk_score >= 50 else '#00ff9d' }};font-family:'Rajdhani',sans-serif;font-weight:700">{{ t.risk_score }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>

<!-- ═══ SIGNALS ═══════════════════════════════════════════════════════════════ -->
<div class="tab-content" id="tab-signals">
  <div class="grid-2">
    <div class="panel">
      <div class="ph"><div class="pt">⚡ velocity_l6h — Escalation Alerts</div></div>
      <div class="signal-row"><div class="sig-icon">⚡</div>
        <div class="sig-info"><div class="sig-name">Senthil Kumar — HVEL account</div><div class="sig-desc">velocity_l6h escalates: 2→3→4→5→6→7→8→9 (8 txns/4min)</div></div>
        <div class="sig-val" style="color:var(--danger)">9</div></div>
      <div class="signal-row"><div class="sig-icon">⚡</div>
        <div class="sig-info"><div class="sig-name">Balaji Natarajan — Shared Device</div><div class="sig-desc">velocity_l6h=2 · Samsung S23 · ip_density:14</div></div>
        <div class="sig-val" style="color:var(--warn)">2</div></div>
      <div class="signal-row"><div class="sig-icon">⚡</div>
        <div class="sig-info"><div class="sig-name">Saranya Venkat — Cross Channel</div><div class="sig-desc">velocity_l6h: 1→2 · Chennai→Delhi 45s</div></div>
        <div class="sig-val" style="color:var(--warn)">2</div></div>
    </div>
    <div class="panel">
      <div class="ph"><div class="pt">📉 churn_rate — Mule Indicators</div></div>
      <div class="signal-row"><div class="sig-icon">📉</div>
        <div class="sig-info"><div class="sig-name">Priya Nair (Mule Chain #2)</div><div class="sig-desc">Highest churn in dataset — money exits immediately</div></div>
        <div class="sig-val" style="color:var(--danger)">0.982</div></div>
      <div class="signal-row"><div class="sig-icon">📉</div>
        <div class="sig-info"><div class="sig-name">Arjun Sharma (Mule Chain #1)</div><div class="sig-desc">churn_rate 0.975 · Account age 224d</div></div>
        <div class="sig-val" style="color:var(--danger)">0.975</div></div>
      <div class="signal-row"><div class="sig-icon">📉</div>
        <div class="sig-info"><div class="sig-name">FAN accounts (Mule Collection)</div><div class="sig-desc">8 accounts · avg churn: 0.940 · age: 5 days</div></div>
        <div class="sig-val" style="color:var(--danger)">0.940</div></div>
      <div class="signal-row"><div class="sig-icon">📉</div>
        <div class="sig-info"><div class="sig-name">Arun Menon (Shared Device)</div><div class="sig-desc">churn: 0.983 — highest in shared device cluster</div></div>
        <div class="sig-val" style="color:var(--danger)">0.983</div></div>
    </div>
  </div>
  <div class="grid-2">
    <div class="panel">
      <div class="ph"><div class="pt">🌐 ip_account_density — Dense Clusters</div></div>
      <div class="signal-row"><div class="sig-icon">🌐</div>
        <div class="sig-info"><div class="sig-name">103.50.181.18 — HVEL + FAN accounts</div><div class="sig-desc">Shared by High Velocity + 8 Mule Collection accounts</div></div>
        <div class="sig-val" style="color:var(--danger)">19</div></div>
      <div class="signal-row"><div class="sig-icon">🌐</div>
        <div class="sig-info"><div class="sig-name">103.221.93.148 — Samsung S23 cluster</div><div class="sig-desc">5 shared-device accounts · ip_density: 14</div></div>
        <div class="sig-val" style="color:var(--warn)">14</div></div>
      <div class="signal-row"><div class="sig-icon">🌐</div>
        <div class="sig-info"><div class="sig-name">103.161.159.227 — Mule Chain</div><div class="sig-desc">3 mule chain accounts · Arjun, Priya, Karthik</div></div>
        <div class="sig-val" style="color:var(--warn)">11</div></div>
      <div class="signal-row"><div class="sig-icon">🌐</div>
        <div class="sig-info"><div class="sig-name">192.168.1.1 — Circular Loop</div><div class="sig-desc">Private IP · Alpha, Beta, Gamma accounts</div></div>
        <div class="sig-val" style="color:var(--warn)">3</div></div>
    </div>
    <div class="panel">
      <div class="ph"><div class="pt">🆕 account_age_days — New Account Alerts</div></div>
      <div class="signal-row"><div class="sig-icon">🆕</div>
        <div class="sig-info"><div class="sig-name">MULE_ACC_0 – MULE_ACC_7 (Fan-In)</div><div class="sig-desc">8 throwaway accounts · created just before attack</div></div>
        <div class="sig-val" style="color:var(--danger)">5d</div></div>
      <div class="signal-row"><div class="sig-icon">🆕</div>
        <div class="sig-info"><div class="sig-name">ACC_A, ACC_B, ACC_C (Circular Loop)</div><div class="sig-desc">3 newly created accounts · cyclic fund flow</div></div>
        <div class="sig-val" style="color:var(--danger)">5d</div></div>
      <div class="signal-row"><div class="sig-icon">🆕</div>
        <div class="sig-info"><div class="sig-name">Balaji Natarajan (Shared Device)</div><div class="sig-desc">Youngest in shared device cluster</div></div>
        <div class="sig-val" style="color:var(--warn)">45d</div></div>
      <div class="signal-row"><div class="sig-icon">🆕</div>
        <div class="sig-info"><div class="sig-name">Dinesh Raj</div><div class="sig-desc">account_age_days: 4 — normal txn but monitor</div></div>
        <div class="sig-val" style="color:var(--warn)">4d</div></div>
    </div>
  </div>
</div>

<!-- ═══ FRAUD STORIES ══════════════════════════════════════════════════════════════ -->
<div class="tab-content" id="tab-story">

  <!-- STORY 1 -->
  <div class="sp">
    <div class="stitle">🔥 FRAUD #1 — Mule Chain: Arjun → Priya → Karthik (ATM)</div>
    <div style="font-size:11px;color:var(--text3);margin-bottom:10px;font-family:'Share Tech Mono',monospace">2025-06-05 14:00–14:01:40 · IP: 103.161.159.227 · iPhone 14 · churn: 0.975/0.982/0.943</div>
    <div class="chain">
      <div class="cn">Arjun Sharma<span class="ct">14:00:00 · ₹50K · churn:0.975</span></div>
      <div class="ca">━━▶</div>
      <div class="cn">Priya Nair<span class="ct">14:00:50 · ₹48K · churn:0.982</span></div>
      <div class="ca">━━▶</div>
      <div class="cn atm">🏧 ATM (Karthik)<span class="ct">14:01:40 · ₹46K · churn:0.943</span></div>
    </div>
    <div class="sf">
      <div class="fi"><div class="fv">1m 40s</div><div class="fl">Total duration</div></div>
      <div class="fi"><div class="fv">0.975</div><div class="fl">Avg churn rate</div></div>
      <div class="fi"><div class="fv">103.161.159.227</div><div class="fl">Shared IP · 3 hops</div></div>
    </div>
  </div>

  <!-- STORY 2 -->
  <div class="sp">
    <div class="stitle">🔥 FRAUD #2 — Shared Device: Samsung S23</div>
    <div style="font-size:11px;color:var(--text3);margin-bottom:10px;font-family:'Share Tech Mono',monospace">
      2025-06-07 10:30 – 10:38 · Risk: 86 · IP: 103.78.90.12 · 5 accounts in 8 min
    </div>
    <div class="chain">
      {% for n in ['Manoj Patel','Rekha Singh','Arun Menon','Sindhu Rao','Balaji N.'] %}
      <div class="cn" style="border-color:#c864ff;color:#c864ff">{{ n }}</div>
      {% if not loop.last %}<div class="ca" style="color:#c864ff">━━▶</div>{% endif %}
      {% endfor %}
    </div>
    <div class="sf">
      <div class="fi" style="border-left-color:#c864ff"><div class="fv" style="color:#c864ff">5</div><div class="fl">Accounts — 1 device</div></div>
      <div class="fi" style="border-left-color:#c864ff"><div class="fv" style="color:#c864ff">8 min</div><div class="fl">All transactions</div></div>
      <div class="fi" style="border-left-color:#c864ff"><div class="fv" style="color:#c864ff">₹1.35L</div><div class="fl">Total outflow</div></div>
    </div>
  </div>

   <!-- STORY 3 -->
  <div class="sp">
    <div class="stitle">🔥 FRAUD #3 — High Velocity: 8 IMPS in 4 min</div>
    <div style="font-size:11px;color:var(--text3);margin-bottom:8px;font-family:'Share Tech Mono',monospace">Senthil Kumar · velocity_l6h climbs 2→9 · All &lt;₹10K</div>
    <div style="background:var(--bg3);border-radius:6px;padding:10px;font-family:'Share Tech Mono',monospace;font-size:10px">
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:4px">
        {% for v in ['₹9,990\nvel:2','₹9,890\nvel:3','₹9,790\nvel:4','₹9,690\nvel:5','₹9,590\nvel:6','₹9,490\nvel:7','₹9,390\nvel:8','₹9,290\nvel:9🚨'] %}
        <div style="background:var(--panel);border:1px solid rgba(255,183,0,.3);border-radius:3px;padding:4px;text-align:center">
          <div style="color:var(--warn)">{{ v.split('\n')[0] }}</div>
          <div style="color:var(--text3);font-size:9px">{{ v.split('\n')[1] }}</div>
        </div>
        {% endfor %}
      </div>
    </div>
  </div>

  <!-- STORY 4 -->
  <div class="sp" style="border-color:rgba(0, 212, 255, 0.4)">
    <div class="stitle" style="color:var(--accent)">🔥 FRAUD #4 — Cross Channel: Saranya Venkat</div>
    <div style="font-size:11px;color:var(--text3);margin-bottom:12px;font-family:'Share Tech Mono',monospace">
      2025-06-10 11:05:00 · Chennai + Delhi in 45 seconds · impossible travel
    </div>

    <div style="display:grid;grid-template-columns:1fr 30px 1fr;gap:8px;align-items:center;margin-bottom:12px">
      <div style="background:var(--bg3);border:1px solid rgba(0, 212, 255, 0.3);border-radius:6px;padding:12px;font-family:'Share Tech Mono',monospace;font-size:11px">
        <div style="color:var(--accent);font-size:12px;font-weight:700;margin-bottom:6px">🏧 Chennai ATM</div>
        <div style="color:var(--text)">Time: 11:05:00</div>
        <div style="color:var(--warn)">Amount: ₹20,000</div>
        <div style="color:var(--text3)">IP: 103.21.219.60</div>
      </div>

      <div style="color:var(--accent);font-size:18px;text-align:center;font-weight:bold;">⚡</div>

      <div style="background:var(--bg3);border:1px solid rgba(0, 212, 255, 0.3);border-radius:6px;padding:12px;font-family:'Share Tech Mono',monospace;font-size:11px">
        <div style="color:var(--accent);font-size:12px;font-weight:700;margin-bottom:6px">💻 Delhi Net Banking</div>
        <div style="color:var(--text)">Time: 11:05:45</div>
        <div style="color:var(--warn)">Amount: ₹35,000</div>
        <div style="color:var(--text3)">IP: 103.172.69.180</div>
      </div>
    </div>

    <div style="background:rgba(0, 212, 255, 0.08);border:1px solid rgba(0, 212, 255, 0.3);border-radius:6px;padding:10px;font-size:11px;color:var(--accent);font-family:'Share Tech Mono',monospace;margin-bottom:12px">
      ⚠ GEOGRAPHIC ANOMALY: Same account accessed from locations 2,200 km apart in 45 seconds. Indicates severe credential compromise and physical card cloning.
    </div>

    <div class="sf">
      <div class="fi" style="border-left-color:var(--accent)"><div class="fv" style="color:var(--accent)">45s</div><div class="fl">Time difference</div></div>
      <div class="fi" style="border-left-color:var(--accent)"><div class="fv" style="color:var(--accent)">2,200 km</div><div class="fl">Distance apart</div></div>
      <div class="fi" style="border-left-color:var(--accent)"><div class="fv" style="color:var(--accent)">₹55,000</div><div class="fl">Total at risk</div></div>
    </div>
  </div>

  <!-- STORY 5 -->
  <div class="sp" style="margin-top:12px">
    <div class="stitle">🔥 FRAUD #5 (NEW) — Mule Collection: 8 Accounts → Collector</div>
    <div style="font-size:11px;color:var(--text3);margin-bottom:12px;font-family:'Share Tech Mono',monospace">
      2025-07-02 10:00–10:07 · IP: 103.50.181.18 · OnePlus 11 · account_age: 5 days · churn: 0.904–0.975
    </div>
    <div style="background:var(--bg3);border-radius:8px;padding:14px;font-family:'Share Tech Mono',monospace;font-size:11px;margin-bottom:12px">
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-bottom:10px">
        {% for m in ['Mule0','Mule1','Mule2','Mule3','Mule4','Mule5','Mule6','Mule7'] %}
        <div style="background:var(--panel);border:1px solid rgba(255,106,0,.4);border-radius:4px;padding:6px;text-align:center">
          <div style="color:var(--orange)">{{ m }}</div>
          <div style="color:var(--text3);font-size:9px">₹5,000 · age:5d</div>
        </div>
        {% endfor %}
      </div>
      <div style="text-align:center;color:var(--warn);font-size:14px">↓ &nbsp; ↓ &nbsp; ↓ &nbsp; ↓ &nbsp; ↓ &nbsp; ↓ &nbsp; ↓ &nbsp; ↓ &nbsp; (8 UPI transfers)</div>
      <div style="text-align:center;margin-top:8px;background:rgba(255,106,0,.15);border:2px solid var(--orange);border-radius:8px;padding:10px">
        <div style="color:var(--orange);font-size:14px;font-weight:700">🎯 COLL_ACC_01</div>
        <div style="color:var(--text3);font-size:10px">Collector Account · Received ₹40,000 · IP: 103.50.181.18</div>
      </div>
    </div>
    <div class="sf">
      <div class="fi" style="border-left-color:var(--orange)"><div class="fv" style="color:var(--orange)">8</div><div class="fl">Mule accounts</div></div>
      <div class="fi" style="border-left-color:var(--orange)"><div class="fv" style="color:var(--orange)">5 days</div><div class="fl">Account age (throwaway)</div></div>
      <div class="fi" style="border-left-color:var(--orange)"><div class="fv" style="color:var(--orange)">₹40,000</div><div class="fl">Collected in 7 min</div></div>
    </div>
  </div>

  <!-- STORY 6 -->
  <div class="sp" style="border-color:rgba(255,0,255,.4)">
    <div class="stitle" style="color:var(--purple)">🔥 FRAUD #6 (NEW) — Circular Loop: Alpha → Beta → Gamma → Alpha</div>
    <div style="font-size:11px;color:var(--text3);margin-bottom:12px;font-family:'Share Tech Mono',monospace">
      2025-07-02 15:00–15:10 · IP: 192.168.1.1 · OnePlus 11 · cyclic fund laundering
    </div>
    <div class="chain">
      <div class="cn" style="border-color:var(--purple);color:var(--purple)">Alpha (ACC_A)<span class="ct">15:00 · ₹10,000</span></div>
      <div class="ca" style="color:var(--purple)">━━▶</div>
      <div class="cn" style="border-color:var(--purple);color:var(--purple)">Beta (ACC_B)<span class="ct">15:05 · ₹9,900</span></div>
      <div class="ca" style="color:var(--purple)">━━▶</div>
      <div class="cn" style="border-color:var(--purple);color:var(--purple)">Gamma (ACC_C)<span class="ct">15:10 · ₹9,800</span></div>
      <div class="ca" style="color:var(--purple)">━━▶</div>
      <div class="cn" style="border-color:var(--purple);color:var(--purple)">↩ Alpha (ACC_A)<span class="ct">Cycle closes</span></div>
    </div>
    <div style="background:rgba(255,0,255,.08);border:1px solid rgba(255,0,255,.3);border-radius:6px;padding:10px;font-size:11px;color:var(--purple);font-family:'Share Tech Mono',monospace;margin-bottom:12px">
      ⚠ Diminishing amounts (₹10K→₹9.9K→₹9.8K) = fee extraction at each hop. Cyclic pattern obscures fund origin. All accounts age: 5 days. IP: 192.168.1.1 (private/VPN).
    </div>
    <div class="sf">
      <div class="fi" style="border-left-color:var(--purple)"><div class="fv" style="color:var(--purple)">A→B→C→A</div><div class="fl">Cyclic path</div></div>
      <div class="fi" style="border-left-color:var(--purple)"><div class="fv" style="color:var(--purple)">10 min</div><div class="fl">Full cycle</div></div>
      <div class="fi" style="border-left-color:var(--purple)"><div class="fv" style="color:var(--purple)">₹200</div><div class="fl">Fee per hop (extraction)</div></div>
    </div>
  </div>

</div>
<!-- ═══ CHATBOT ════════════════════════════════════════════════════════════════ -->
<div class="tab-content" id="tab-chatbot">
  <div class="panel">
    <div class="ph">
      <div class="pt">🤖 IntelliTrace AI v2 — Enhanced Fraud Assistant</div>
      <span style="font-size:10px;color:var(--accent2);font-family:'Share Tech Mono',monospace" id="llm-badge">claude-sonnet · Loading...</span>
    </div>
    <div class="qbs">
      <div class="qb" onclick="qsend('Explain the Mule Collection fan-in pattern')">Fan-In Pattern</div>
      <div class="qb" onclick="qsend('How does circular loop laundering work?')">Circular Loop</div>
      <div class="qb" onclick="qsend('What does churn_rate tell us?')">Churn Rate Signal</div>
      <div class="qb" onclick="qsend('Explain velocity_l6h escalation')">Velocity Signal</div>
      <div class="qb" onclick="qsend('Why are new accounts suspicious?')">New Accounts</div>
      <div class="qb" onclick="qsend('What is ip_account_density?')">IP Density</div>
      <div class="qb" onclick="qsend('Which account has the highest risk?')">Highest Risk</div>
      <div class="qb" onclick="qsend('Give me all 6 fraud stories in brief')">All 6 Stories</div>
    </div>
    <div class="chat-wrap">
      <div class="chat-msgs" id="chat-msgs">
        <div class="msg bot">
          <div class="ms bot">🤖 INTELLITRACE AI v2</div>
          Welcome to IntelliTrace v2! I now understand <strong style="color:var(--accent)">6 fraud patterns</strong> across 229 transactions, including 2 new ones:<br><br>
          🟠 <strong>Mule Collection</strong> — 8 throwaway accounts (age: 5 days) → COLL_ACC_01<br>
          🟣 <strong>Circular Loop</strong> — Alpha→Beta→Gamma→Alpha cyclic laundering<br><br>
          I also analyze new signals: <code style="color:var(--accent2)">churn_rate</code>, <code style="color:var(--accent2)">velocity_l6h</code>, <code style="color:var(--accent2)">ip_account_density</code>, <code style="color:var(--accent2)">account_age_days</code>. Ask me anything!
        </div>
      </div>
      <div class="ci">
        <input class="cin" id="chat-in" type="text" placeholder="Ask about fraud patterns, signals, accounts..."
               onkeydown="if(event.key==='Enter')sendChat()"/>
        <button class="csend" onclick="sendChat()">SEND ▶</button>
      </div>
    </div>
  </div>
</div>

</div><!-- /main -->

<script>
setInterval(()=>{document.getElementById('clock').textContent=new Date().toLocaleTimeString('en-IN')},1000);
function showTab(n,el){
  document.querySelectorAll('.tab-content').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(t=>t.classList.remove('active'));
  document.getElementById('tab-'+n).classList.add('active');
  el.classList.add('active');
  if(n==='graph') setTimeout(renderGraph,100);
}
function filterTable(){
  const v=document.getElementById('flt').value;
  document.querySelectorAll('#txn-body tr').forEach(r=>{
    r.style.display=(v==='all'||(v==='1'&&r.dataset.fraud==='1')||(v==='0'&&r.dataset.fraud==='0'))?'':'none';
  });
}
async function checkAPI(){
  try{
    const r=await fetch('/api/status',{signal:AbortSignal.timeout(2000)});
    const d=await r.json();
    document.getElementById('api-s').style.color=d.api?'#00ff9d':'#ffb700';
    document.getElementById('api-s').textContent=d.api?'Online':'Standalone';
    document.getElementById('llm-badge').textContent=d.chat?'claude-sonnet · Connected':'Rule-based · Start ai_chatbot.py';
  }catch(e){}
}
checkAPI();

// ─── D3 GRAPH ────────────────────────────────────────────────────────────────
const NODES=[
  {id:'ARJUN',l:'Arjun Sharma',t:'mule',r:85},{id:'PRIYA',l:'Priya Nair',t:'mule',r:88},
  {id:'KARTHIK',l:'Karthik Rajan',t:'mule',r:91},
  {id:'MANOJ',l:'Manoj Patel',t:'shared',r:78},{id:'REKHA',l:'Rekha Singh',t:'shared',r:80},
  {id:'ARUN',l:'Arun Menon',t:'shared',r:82},{id:'SINDHU',l:'Sindhu Rao',t:'shared',r:84},
  {id:'BALAJI',l:'Balaji N.',t:'shared',r:86},
  {id:'SENTHIL',l:'Senthil Kumar',t:'velocity',r:93},
  {id:'SARANYA',l:'Saranya Venkat',t:'cross',r:95},
  {id:'MULE0',l:'Mule0',t:'fanin',r:90},{id:'MULE1',l:'Mule1',t:'fanin',r:90},
  {id:'MULE2',l:'Mule2',t:'fanin',r:90},{id:'MULE3',l:'Mule3',t:'fanin',r:90},
  {id:'MULE4',l:'Mule4',t:'fanin',r:90},{id:'MULE5',l:'Mule5',t:'fanin',r:90},
  {id:'MULE6',l:'Mule6',t:'fanin',r:90},{id:'MULE7',l:'Mule7',t:'fanin',r:90},
  {id:'COLL',l:'COLL_ACC_01',t:'collector',r:90},
  {id:'ACCA',l:'Alpha(A)',t:'circular',r:90},{id:'ACCB',l:'Beta(B)',t:'circular',r:90},
  {id:'ACCC',l:'Gamma(C)',t:'circular',r:91},
  {id:'IP1',l:'103.161.159.227',t:'ip',r:85},{id:'IP2',l:'103.221.93.148',t:'ip',r:80},
  {id:'IP3',l:'103.50.181.18',t:'ip',r:93},{id:'IPL',l:'192.168.1.1',t:'ip',r:90},
  {id:'DEV1',l:'iPhone 14',t:'device',r:88},{id:'DEV2',l:'Samsung S23',t:'device',r:84},
  {id:'DEV3',l:'OnePlus 11',t:'device',r:90},{id:'DEV4',l:'Laptop-Chrome',t:'device',r:93},
  {id:'NRM',l:'Normal Acct',t:'normal',r:10},
];
const LINKS=[
  {s:'ARJUN',t:'PRIYA',e:'mule'},{s:'PRIYA',t:'KARTHIK',e:'mule'},
  {s:'ARJUN',t:'IP1',e:'ip'},{s:'PRIYA',t:'IP1',e:'ip'},{s:'KARTHIK',t:'IP1',e:'ip'},
  {s:'ARJUN',t:'DEV1',e:'dev'},{s:'PRIYA',t:'DEV1',e:'dev'},
  {s:'MANOJ',t:'IP2',e:'ip'},{s:'REKHA',t:'IP2',e:'ip'},{s:'ARUN',t:'IP2',e:'ip'},
  {s:'MANOJ',t:'DEV2',e:'dev'},{s:'REKHA',t:'DEV2',e:'dev'},{s:'ARUN',t:'DEV2',e:'dev'},
  {s:'SENTHIL',t:'IP3',e:'ip'},{s:'SENTHIL',t:'DEV4',e:'dev'},
  {s:'MULE0',t:'COLL',e:'fanin'},{s:'MULE1',t:'COLL',e:'fanin'},{s:'MULE2',t:'COLL',e:'fanin'},
  {s:'MULE3',t:'COLL',e:'fanin'},{s:'MULE4',t:'COLL',e:'fanin'},{s:'MULE5',t:'COLL',e:'fanin'},
  {s:'MULE6',t:'COLL',e:'fanin'},{s:'MULE7',t:'COLL',e:'fanin'},
  {s:'MULE0',t:'IP3',e:'ip'},{s:'MULE1',t:'IP3',e:'ip'},
  {s:'MULE0',t:'DEV3',e:'dev'},{s:'MULE1',t:'DEV3',e:'dev'},
  {s:'ACCA',t:'ACCB',e:'loop'},{s:'ACCB',t:'ACCC',e:'loop'},{s:'ACCC',t:'ACCA',e:'loop'},
  {s:'ACCA',t:'IPL',e:'ip'},{s:'ACCA',t:'DEV3',e:'dev'},
];
const NC={mule:'#ff3c5a',shared:'#c864ff',velocity:'#ffb700',cross:'#00d4ff',
          fanin:'#ff6a00',circular:'#ff00ff',collector:'#ff4400',ip:'#00ff9d',device:'#7eb8ff',normal:'#3a8aff'};
const NR={mule:14,shared:13,velocity:15,cross:16,fanin:10,circular:12,collector:18,ip:9,device:11,normal:9};
let sim,gg;

function renderGraph(){
  const cont=document.getElementById('graph-cont');
  const W=cont.clientWidth,H=cont.clientHeight;
  d3.select('#g-svg').selectAll('*').remove();
  const svg=d3.select('#g-svg').attr('width',W).attr('height',H);
  const g=svg.append('g'); gg=g;
  svg.call(d3.zoom().scaleExtent([.25,3]).on('zoom',e=>g.attr('transform',e.transform)));

  const nodes=NODES.map(n=>({...n}));
  const links=LINKS.map(l=>({source:l.s,target:l.t,e:l.e}));

  sim=d3.forceSimulation(nodes)
    .force('link',d3.forceLink(links).id(d=>d.id).distance(d=>{
      if(d.e==='mule')return 85; if(d.e==='fanin')return 65;
      if(d.e==='loop')return 75; return 60;
    }))
    .force('charge',d3.forceManyBody().strength(-200))
    .force('center',d3.forceCenter(W/2,H/2))
    .force('collision',d3.forceCollide().radius(d=>NR[d.t]+14));

  const link=g.append('g').selectAll('line').data(links).join('line')
    .attr('stroke',d=>d.e==='mule'?'#ff3c5a':d.e==='fanin'?'#ff6a00aa':d.e==='loop'?'#ff00ffaa':d.e==='ip'?'#00ff9d55':'#3a6a9055')
    .attr('stroke-width',d=>d.e==='mule'||d.e==='loop'?2.5:1.5)
    .attr('stroke-dasharray',d=>d.e==='loop'?'4,2':'none')
    .attr('opacity',d=>d.e==='mule'?.9:.6);

  const node=g.append('g').selectAll('g').data(nodes).join('g').attr('cursor','pointer')
    .call(d3.drag()
      .on('start',(e,d)=>{if(!e.active)sim.alphaTarget(.3).restart();d.fx=d.x;d.fy=d.y;})
      .on('drag',(e,d)=>{d.fx=e.x;d.fy=e.y;})
      .on('end',(e,d)=>{if(!e.active)sim.alphaTarget(0);d.fx=null;d.fy=null;}));

  node.append('circle').attr('r',d=>NR[d.t]).attr('fill',d=>NC[d.t]+'33')
    .attr('stroke',d=>NC[d.t]).attr('stroke-width',d=>d.r>80?2.5:1.5);

  node.append('text').attr('text-anchor','middle').attr('dy','0.35em').attr('font-size','9px')
    .attr('fill',d=>NC[d.t]).attr('font-family','Share Tech Mono,monospace').attr('pointer-events','none')
    .text(d=>d.t==='ip'?'⬡':d.t==='device'?'▣':d.t==='collector'?'🎯':d.l.split(' ')[0].slice(0,6));

  node.append('text').attr('text-anchor','middle').attr('dy',d=>NR[d.t]+12)
    .attr('font-size','8px').attr('fill','#7aadcc')
    .attr('font-family','Share Tech Mono,monospace').attr('pointer-events','none')
    .text(d=>d.t==='ip'?d.l.slice(-8):d.l.slice(0,10));

  sim.on('tick',()=>{
    link.attr('x1',d=>d.source.x).attr('y1',d=>d.source.y)
        .attr('x2',d=>d.target.x).attr('y2',d=>d.target.y);
    node.attr('transform',d=>`translate(${d.x},${d.y})`);
  });
}
function resetGraph(){renderGraph();}
function showFraud(){if(!gg)return;gg.selectAll('circle').attr('opacity',d=>d.r>75?1:.2).attr('stroke-width',d=>d.r>75?4:1.5);}
function showFanIn(){
  if(!gg)return;
  const s=new Set(['MULE0','MULE1','MULE2','MULE3','MULE4','MULE5','MULE6','MULE7','COLL','IP3','DEV3']);
  gg.selectAll('circle').attr('opacity',d=>s.has(d.id)?1:.15).attr('stroke-width',d=>s.has(d.id)?4:1.5)
    .attr('stroke',d=>s.has(d.id)?'#ff6a00':NC[d.t]);
}
function showLoop(){
  if(!gg)return;
  const s=new Set(['ACCA','ACCB','ACCC','IPL']);
  gg.selectAll('circle').attr('opacity',d=>s.has(d.id)?1:.15).attr('stroke-width',d=>s.has(d.id)?4:1.5)
    .attr('stroke',d=>s.has(d.id)?'#ff00ff':NC[d.t]);
}

// ─── CHATBOT ──────────────────────────────────────────────────────────────────
async function sendChat(){
  const inp=document.getElementById('chat-in');
  const msg=inp.value.trim(); if(!msg)return; inp.value='';
  const msgs=document.getElementById('chat-msgs');
  msgs.innerHTML+=`<div class="msg user"><div class="ms usr">YOU</div>${msg}</div>`;
  const tp=document.createElement('div'); tp.className='msg bot';
  tp.innerHTML='<div class="ms bot">🤖 INTELLITRACE AI v2</div><div class="typing"><span></span><span></span><span></span></div>';
  msgs.appendChild(tp); msgs.scrollTop=msgs.scrollHeight;
  try{
    const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})});
    const d=await r.json();
    tp.innerHTML=`<div class="ms bot">🤖 INTELLITRACE AI v2</div>${(d.response||'').replace(/\n/g,'<br>')}`;
  }catch(e){
    tp.innerHTML=`<div class="ms bot">🤖 INTELLITRACE AI v2</div>
    Chatbot offline. Start: <code style="color:var(--accent)">python ai_chatbot.py --api</code><br><br>
    <em>Built-in:</em> Dataset has 229 txns · 29 fraud · 6 patterns including Mule Collection (8 mules → COLL_ACC_01, age:5d) and Circular Loop (A→B→C→A). New signals: churn_rate (fraud avg: 0.94), velocity_l6h (peaks at 9), ip_account_density (max:19).`;
  }
  msgs.scrollTop=msgs.scrollHeight;
}
function qsend(m){document.getElementById('chat-in').value=m;sendChat();}
</script>
</body>
</html>"""


# ─── ROUTES ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    txns = _load()
    fraud = [t for t in txns if t["is_fraud"]==1]
    ft_counts: dict = {}
    for t in fraud:
        ft_counts[t["fraud_type"]] = ft_counts.get(t["fraud_type"],0)+1
    total = max(len(fraud),1)
    fraud_types = [
        {"name":ft,"count":cnt,"pct":round(cnt/total*100),
         "color":FT_COLORS.get(ft,"#00d4ff")}
        for ft,cnt in ft_counts.items()
    ]
    for t in txns:
        t["badge"] = BADGE.get(t.get("fraud_type","Normal"),"b-n")
    
    # NEW: Calculate unique IPs to block
    blocked_ips_count = len(set(t["ip_address"] for t in fraud))
    
    mule_names = ['Mule0','Mule1','Mule2','Mule3','Mule4','Mule5','Mule6','Mule7']
    vel_vals    = ['₹9,990\nvel:2','₹9,890\nvel:3','₹9,790\nvel:4','₹9,690\nvel:5',
                   '₹9,590\nvel:6','₹9,490\nvel:7','₹9,390\nvel:8','₹9,290\nvel:9🚨']
    return render_template_string(HTML,
        stats={"total":len(txns),"fraud":len(fraud),
               "max_risk":max((t["risk_score"] for t in fraud),default=0),
               "blocked": blocked_ips_count},
        alerts=ALERTS_STATIC,
        fraud_types=fraud_types,
        transactions=txns,
        mule_names=mule_names,
        vel_vals=vel_vals,
    )

@app.route("/api/status")
def api_status():
    api, chat = False, False
    if REQUESTS:
        try: req_lib.get(f"{API_BASE}/", timeout=2); api=True
        except: pass
        try: req_lib.get(f"{CHAT_BASE}/", timeout=2); chat=True
        except: pass
    return jsonify({"api":api,"chat":chat})

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(force=True)
    return jsonify({"response": _chat(data.get("message",""))})

@app.route("/api/transactions")
def api_txns():
    fraud_only = request.args.get("fraud_only","false").lower()=="true"
    txns = _load()
    if fraud_only: txns=[t for t in txns if t["is_fraud"]]
    return jsonify(txns)

@app.route("/api/stats")
def api_stats():
    txns=_load(); fraud=[t for t in txns if t["is_fraud"]]
    return jsonify({"total":len(txns),"fraud":len(fraud),
                    "max_risk":max((t["risk_score"] for t in fraud),default=0)})

# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("╔══════════════════════════════════════════╗")
    print("║  IntelliTrace — Dashboard v2             ║")
    print("║  Cyber Dynamos · 2026                    ║")
    print("╚══════════════════════════════════════════╝\n")
    print("[DASH] Make sure transactions.csv is in the same folder.")
    print("[DASH] → http://127.0.0.1:5000\n")
    app.run(host="127.0.0.1", port=5000, debug=True)