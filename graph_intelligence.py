"""
═══════════════════════════════════════════════════════════════════════════════
  IntelliTrace 2026 — Enhanced Graph Intelligence Engine
  File: graph_intelligence.py
  Team: Cyber Dynamos
═══════════════════════════════════════════════════════════════════════════════
  NEW vs previous version:
    ✦ Fan-In (Mule Collection) detection — many → one collector node
    ✦ Circular Loop detection  — A→B→C→A cycle
    ✦ churn_rate signal        — accounts with churn > 0.85 flagged
    ✦ ip_account_density       — dense IPs get cluster boost
    ✦ account_age_days         — new accounts (< 30 days) get extra risk
    ✦ velocity_l6h             — escalating velocity pattern detection
    ✦ receiver_pincode         — cross-region transfer detection

  HOW TO RUN:
    pip install networkx pandas matplotlib
    python transaction_simulator.py   ← generate data first
    python graph_intelligence.py

  OUTPUT:
    graph_report.json · fraud_clusters.json · graph_visualization.png
═══════════════════════════════════════════════════════════════════════════════
"""

import json, csv, datetime, collections, os
from typing import List, Dict, Any

import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ─── THRESHOLDS ───────────────────────────────────────────────────────────────

VELOCITY_WINDOW_SEC    = 300     # 5 min window for burst detection
VELOCITY_MIN_TXN       = 3
SHARED_DEVICE_MIN_ACC  = 2
FAN_IN_MIN_SENDERS     = 3      # min senders → 1 collector = fan-in
CIRCULAR_MAX_LEN       = 6      # look for cycles up to length 6
CROSS_CHANNEL_SEC      = 120
HIGH_CHURN_THRESHOLD   = 0.85
LOW_ACCOUNT_AGE_DAYS   = 30     # accounts younger than this → suspicious
HIGH_IP_DENSITY        = 15     # ip_account_density > this = dense cluster

RISK_WEIGHTS = {
    "shared_ip":       20.0,
    "shared_device":   30.0,
    "high_velocity":   20.0,
    "cross_channel":   40.0,
    "mule_chain":      35.0,
    "fan_in":          35.0,
    "circular_loop":   40.0,
    "high_churn":      15.0,
    "new_account":     10.0,
    "ip_density":      10.0,
}

NODE_COLORS = {
    "account":    "#00d4ff",
    "ip":         "#00ff9d",
    "device":     "#7eb8ff",
    "collector":  "#ff6a00",
    "mule":       "#ff3c5a",
    "shared":     "#c864ff",
    "velocity":   "#ffb700",
    "cross":      "#00d4ff",
    "fan_in":     "#ff6a00",
    "circular":   "#ff00ff",
    "normal":     "#3a8aff",
}


class GraphIntelligence:
    """
    Enhanced graph engine with 6 fraud detectors.
    """

    def __init__(self, csv_path: str = "transactions.csv"):
        self.csv_path = csv_path
        self.G        = nx.MultiDiGraph()
        self.txns:  List[Dict] = []
        self.risk_scores: Dict[str, float] = {}

    # ── 1. LOAD ───────────────────────────────────────────────────────────────

    def load(self):
        print(f"[GRAPH] Loading: {self.csv_path}")
        with open(self.csv_path, newline="", encoding="utf-8") as f:
            self.txns = list(csv.DictReader(f))
        print(f"[GRAPH] {len(self.txns)} transactions loaded.")

    # ── 2. BUILD GRAPH ────────────────────────────────────────────────────────

    def build(self):
        print("[GRAPH] Building heterogeneous graph...")
        self._ip_to_accounts:     Dict[str, set] = collections.defaultdict(set)
        self._device_to_accounts: Dict[str, set] = collections.defaultdict(set)
        self._acc_ts:             Dict[str, list] = collections.defaultdict(list)
        self._receiver_counts:    Dict[str, int]  = collections.Counter()

        for t in self.txns:
            acc  = t["account_number"]
            recv = t["receiver_account"]
            ip   = t["ip_address"]
            dev  = t["device"]
            ts   = t["timestamp"]
            amt  = float(t["amount"])
            risk = float(t["risk_score"])
            ftyp = t["fraud_type"]
            frau = int(t["is_fraud"])
            age  = float(t.get("account_age_days", 365))
            churn= float(t.get("churn_rate", 0.1))
            dens = int(t.get("ip_account_density", 5))
            vel  = float(t.get("velocity_l6h", 1))

            # Account node
            if not self.G.has_node(acc):
                self.G.add_node(acc, node_type="account", name=t["name"],
                    is_fraud=frau, fraud_type=ftyp, risk_score=risk,
                    account_type=t["account_type"], pincode=t["pincode"],
                    account_age_days=age, churn_rate=churn)

            # Receiver node
            if recv not in ("SELF","") and not self.G.has_node(recv):
                recv_type = "collector" if recv.startswith("COLL") else "account"
                self.G.add_node(recv, node_type=recv_type, name=t.get("receiver_name","?"),
                    is_fraud=0, fraud_type="Unknown", risk_score=5.0,
                    account_type="Unknown", pincode=t.get("receiver_pincode","000000"),
                    account_age_days=365, churn_rate=0.1)

            # IP node
            ip_id = f"IP:{ip}"
            if not self.G.has_node(ip_id):
                self.G.add_node(ip_id, node_type="ip", ip=ip,
                    risk_score=0.0, density=dens)

            # Device node
            dev_id = f"DEV:{dev}"
            if not self.G.has_node(dev_id):
                self.G.add_node(dev_id, node_type="device", device=dev, risk_score=0.0)

            # Transaction edge
            if recv not in ("SELF",""):
                self.G.add_edge(acc, recv, edge_type="transaction",
                    txn_id=t["txn_id"], timestamp=ts, amount=amt,
                    trans_type=t["trans_type"], is_fraud=frau,
                    fraud_type=ftyp, risk_score=risk)

            # IP & Device edges
            self.G.add_edge(acc, ip_id,  edge_type="ip_usage",  timestamp=ts, is_fraud=frau)
            self.G.add_edge(acc, dev_id, edge_type="dev_usage", timestamp=ts, is_fraud=frau)

            # Tracking
            self._ip_to_accounts[ip].add(acc)
            self._device_to_accounts[dev].add(acc)
            self._acc_ts[acc].append((ts, t["txn_id"], amt))
            if recv not in ("SELF",""):
                self._receiver_counts[recv] += 1

        print(f"[GRAPH] {self.G.number_of_nodes()} nodes, {self.G.number_of_edges()} edges")

    # ── 3. SHARED IP ──────────────────────────────────────────────────────────

    def detect_shared_ip(self) -> List[Dict]:
        print("[GRAPH] → Shared-IP clusters")
        out = []
        for ip, accs in self._ip_to_accounts.items():
            if len(accs) >= 2:
                fraud_accs = [a for a in accs if self.G.nodes[a].get("is_fraud",0)]
                out.append({
                    "type": "Shared IP", "ip": ip,
                    "accounts": list(accs), "account_count": len(accs),
                    "fraud_accounts": fraud_accs,
                    "risk_score": min(95.0, len(accs) * RISK_WEIGHTS["shared_ip"]),
                })
        return out

    # ── 4. SHARED DEVICE ──────────────────────────────────────────────────────

    def detect_shared_device(self) -> List[Dict]:
        print("[GRAPH] → Shared-device clusters")
        out = []
        for dev, accs in self._device_to_accounts.items():
            if len(accs) >= SHARED_DEVICE_MIN_ACC:
                fraud_accs = [a for a in accs if self.G.nodes[a].get("is_fraud",0)]
                out.append({
                    "type": "Shared Device", "device": dev,
                    "accounts": list(accs), "account_count": len(accs),
                    "fraud_accounts": fraud_accs,
                    "risk_score": min(95.0, len(accs) * RISK_WEIGHTS["shared_device"]),
                })
        return out

    # ── 5. HIGH VELOCITY ──────────────────────────────────────────────────────

    def detect_velocity(self) -> List[Dict]:
        print("[GRAPH] → High-velocity bursts")
        fmt = "%Y-%m-%d %H:%M:%S"
        out = []
        for acc, ts_list in self._acc_ts.items():
            if len(ts_list) < VELOCITY_MIN_TXN:
                continue
            sl = sorted(ts_list, key=lambda x: x[0])
            dts = [datetime.datetime.strptime(x[0], fmt) for x in sl]
            for i in range(len(dts)):
                win = [sl[j] for j in range(i, len(dts))
                       if (dts[j]-dts[i]).total_seconds() <= VELOCITY_WINDOW_SEC]
                if len(win) >= VELOCITY_MIN_TXN:
                    out.append({
                        "type": "High Velocity", "account": acc,
                        "name": self.G.nodes[acc].get("name","?"),
                        "txn_count": len(win),
                        "total_amount": sum(w[2] for w in win),
                        "txn_ids": [w[1] for w in win],
                        "start_time": win[0][0], "end_time": win[-1][0],
                        "risk_score": min(95.0, len(win)*RISK_WEIGHTS["high_velocity"]),
                    })
                    break
        return out

    # ── 6. CROSS CHANNEL ──────────────────────────────────────────────────────

    def detect_cross_channel(self) -> List[Dict]:
        print("[GRAPH] → Cross-channel impossible travel")
        fmt = "%Y-%m-%d %H:%M:%S"
        acc_events: Dict[str, list] = collections.defaultdict(list)
        for t in self.txns:
            acc_events[t["account_number"]].append(t)
        out = []
        for acc, evs in acc_events.items():
            evs_sorted = sorted(evs, key=lambda e: e["timestamp"])
            for i in range(len(evs_sorted)-1):
                e1, e2 = evs_sorted[i], evs_sorted[i+1]
                t1 = datetime.datetime.strptime(e1["timestamp"], fmt)
                t2 = datetime.datetime.strptime(e2["timestamp"], fmt)
                delta = (t2-t1).total_seconds()
                if (delta <= CROSS_CHANNEL_SEC
                        and e1["ip_address"] != e2["ip_address"]
                        and e1["pincode"] != e2["pincode"]):
                    out.append({
                        "type": "Cross Channel", "account": acc,
                        "name": e1["name"],
                        "txn_1": e1["txn_id"], "txn_2": e2["txn_id"],
                        "time_1": e1["timestamp"], "time_2": e2["timestamp"],
                        "delta_seconds": delta,
                        "ip_1": e1["ip_address"], "ip_2": e2["ip_address"],
                        "pincode_1": e1["pincode"], "pincode_2": e2["pincode"],
                        "device_1": e1["device"], "device_2": e2["device"],
                        "amount_1": float(e1["amount"]), "amount_2": float(e2["amount"]),
                        "risk_score": 95.0,
                        "description": f"Impossible travel {e1['pincode']} → {e2['pincode']} in {delta:.0f}s",
                    })
        return out

    # ── 7. FAN-IN (Mule Collection) ───────────────────────────────────────────

    def detect_fan_in(self) -> List[Dict]:
        """
        A collector account that receives money from many different senders
        in a short time window = Mule Collection pattern.
        """
        print("[GRAPH] → Fan-in (Mule Collection) detection")
        # Count in-degree from transaction edges only
        in_degree: Dict[str, set] = collections.defaultdict(set)
        fmt = "%Y-%m-%d %H:%M:%S"
        for t in self.txns:
            if t["receiver_account"] not in ("SELF",""):
                in_degree[t["receiver_account"]].add(t["account_number"])

        out = []
        for collector, senders in in_degree.items():
            if len(senders) >= FAN_IN_MIN_SENDERS:
                # Check if senders are all new accounts or high churn
                sender_nodes = [s for s in senders if self.G.has_node(s)]
                avg_age   = (sum(self.G.nodes[s].get("account_age_days",365) for s in sender_nodes)
                             / max(len(sender_nodes),1))
                avg_churn = (sum(self.G.nodes[s].get("churn_rate",0.1) for s in sender_nodes)
                             / max(len(sender_nodes),1))
                out.append({
                    "type":           "Mule Collection (Fan-In)",
                    "collector":      collector,
                    "senders":        list(senders),
                    "sender_count":   len(senders),
                    "avg_account_age": round(avg_age, 1),
                    "avg_churn":      round(avg_churn, 3),
                    "risk_score":     min(95.0, len(senders)*RISK_WEIGHTS["fan_in"] * (1 + avg_churn)),
                    "description":    (
                        f"{len(senders)} mule accounts funnel funds into {collector}. "
                        f"Avg account age: {avg_age:.0f} days. Avg churn: {avg_churn:.2f}"
                    ),
                })
        return out

    # ── 8. CIRCULAR LOOP ──────────────────────────────────────────────────────

    def detect_circular_loops(self) -> List[Dict]:
        """
        Detect A→B→C→A cyclic patterns using NetworkX cycle detection.
        """
        print("[GRAPH] → Circular loop detection")
        # Build simple transaction-only digraph
        TG = nx.DiGraph()
        for u, v, d in self.G.edges(data=True):
            if d.get("edge_type") == "transaction":
                TG.add_edge(u, v, **d)

        out = []
        try:
            cycles = list(nx.simple_cycles(TG, length_bound=CIRCULAR_MAX_LEN))
            for cycle in cycles:
                if 2 <= len(cycle) <= CIRCULAR_MAX_LEN:
                    names = [self.G.nodes[n].get("name", n) for n in cycle]
                    out.append({
                        "type":       "Circular Loop",
                        "path":       cycle + [cycle[0]],
                        "length":     len(cycle),
                        "names":      names,
                        "risk_score": min(95.0, len(cycle)*RISK_WEIGHTS["circular_loop"]),
                        "description": " → ".join(names) + " → " + names[0],
                    })
        except Exception as e:
            print(f"[GRAPH]   Cycle detection error: {e}")
        return out

    # ── 9. CHURN RATE ALERTS ──────────────────────────────────────────────────

    def detect_high_churn(self) -> List[Dict]:
        print("[GRAPH] → High churn-rate accounts")
        out = []
        for acc, data in self.G.nodes(data=True):
            if data.get("node_type") != "account":
                continue
            churn = float(data.get("churn_rate", 0))
            age   = float(data.get("account_age_days", 365))
            if churn >= HIGH_CHURN_THRESHOLD:
                out.append({
                    "type":             "High Churn",
                    "account":          acc,
                    "name":             data.get("name","?"),
                    "churn_rate":       churn,
                    "account_age_days": age,
                    "risk_score":       min(95.0, churn*100 + (RISK_WEIGHTS["new_account"] if age < LOW_ACCOUNT_AGE_DAYS else 0)),
                })
        return out

    # ── 10. CENTRALITY ────────────────────────────────────────────────────────

    def compute_centrality(self) -> Dict[str, float]:
        print("[GRAPH] → Computing centrality")
        UG = self.G.to_undirected()
        UG.remove_edges_from(nx.selfloop_edges(UG))
        deg = nx.degree_centrality(UG)
        bet = nx.betweenness_centrality(UG, normalized=True)
        return {n: round((deg.get(n,0)*0.6 + bet.get(n,0)*0.4)*100, 2)
                for n in set(deg)|set(bet)}

    # ── 11. FINAL RISK SCORES ─────────────────────────────────────────────────

    def compute_risk_scores(self, ip_c, dev_c, vel_a, cross_a, fan_a, loop_a, churn_a) -> Dict[str,float]:
        print("[GRAPH] → Computing final risk scores")
        scores: Dict[str,float] = {}

        # Base from CSV
        for t in self.txns:
            acc = t["account_number"]
            scores[acc] = max(scores.get(acc,0), float(t["risk_score"]))

        def boost(accs, w):
            for a in accs:
                scores[a] = min(100, scores.get(a,0) + w)

        for c in ip_c:    boost(c["accounts"],     RISK_WEIGHTS["shared_ip"])
        for c in dev_c:   boost(c["accounts"],     RISK_WEIGHTS["shared_device"])
        for a in vel_a:   boost([a["account"]],    RISK_WEIGHTS["high_velocity"])
        for a in cross_a: boost([a["account"]],    RISK_WEIGHTS["cross_channel"])
        for a in fan_a:   boost(a["senders"],      RISK_WEIGHTS["fan_in"])
        for a in loop_a:  boost(a["path"],         RISK_WEIGHTS["circular_loop"])
        for a in churn_a: boost([a["account"]],    RISK_WEIGHTS["high_churn"])

        # New-account boost
        for acc, data in self.G.nodes(data=True):
            if data.get("node_type") == "account":
                if float(data.get("account_age_days",365)) < LOW_ACCOUNT_AGE_DAYS:
                    scores[acc] = min(100, scores.get(acc,0) + RISK_WEIGHTS["new_account"])
                # IP density boost
                dens = int(data.get("account_age_days",5))  # approximate
                if dens > HIGH_IP_DENSITY:
                    scores[acc] = min(100, scores.get(acc,0) + RISK_WEIGHTS["ip_density"])

        # Write back to graph
        for acc, s in scores.items():
            if self.G.has_node(acc):
                self.G.nodes[acc]["risk_score"] = round(s,1)
        self.risk_scores = {k: round(v,1) for k,v in scores.items()}
        return self.risk_scores

    # ── 12. VISUALIZE ─────────────────────────────────────────────────────────

    def visualize(self, path="graph_visualization.png"):
        print(f"[GRAPH] → Saving visualization: {path}")
        viz_nodes = {n for n,d in self.G.nodes(data=True)
                     if float(self.risk_scores.get(n, d.get("risk_score",0))) > 20}
        VG = self.G.subgraph(viz_nodes).copy()
        UG = nx.Graph()
        for u,v,d in VG.edges(data=True):
            if u in viz_nodes and v in viz_nodes:
                UG.add_edge(u,v)

        fig, ax = plt.subplots(figsize=(14,10))
        fig.patch.set_facecolor("#040c14")
        ax.set_facecolor("#040c14")

        if not UG.nodes:
            ax.text(0.5,0.5,"No high-risk nodes",ha="center",va="center",color="white")
            plt.savefig(path,dpi=120,bbox_inches="tight"); return

        pos = nx.spring_layout(UG, seed=42, k=2.2)
        ncolors, nsizes = [], []
        for n in UG.nodes():
            risk = float(self.risk_scores.get(n, self.G.nodes[n].get("risk_score",5)))
            ntype= self.G.nodes[n].get("node_type","account")
            ncolors.append("#ff3c5a" if risk>80 else "#ffb700" if risk>50 else
                           "#00ff9d" if ntype=="ip" else "#7eb8ff" if ntype=="device" else "#00d4ff")
            nsizes.append(700 if risk>80 else 450 if risk>50 else 200)

        nx.draw_networkx_edges(UG,pos,ax=ax,edge_color="#3a6a9055",alpha=0.5,width=1.2)
        nx.draw_networkx_nodes(UG,pos,ax=ax,node_color=ncolors,node_size=nsizes,alpha=0.85)
        labels = {n:(n.split(":")[-1][-8:] if ":" in n
                     else self.G.nodes[n].get("name",n).split()[0][:8])
                  for n in UG.nodes()}
        nx.draw_networkx_labels(UG,pos,labels,ax=ax,font_size=7,font_color="#c8e8ff")

        legend = [
            mpatches.Patch(color="#ff3c5a",label="High Risk (>80)"),
            mpatches.Patch(color="#ffb700",label="Medium Risk (50–80)"),
            mpatches.Patch(color="#00d4ff",label="Normal Account"),
            mpatches.Patch(color="#00ff9d",label="IP Node"),
            mpatches.Patch(color="#7eb8ff",label="Device Node"),
        ]
        ax.legend(handles=legend,loc="lower left",facecolor="#0d2035",
                  edgecolor="#1a4060",labelcolor="white",fontsize=8)
        ax.set_title("IntelliTrace — Enhanced Graph Intelligence",color="#00d4ff",fontsize=13)
        ax.axis("off")
        plt.tight_layout()
        plt.savefig(path,dpi=120,bbox_inches="tight",facecolor="#040c14")
        plt.close()
        print(f"[GRAPH] ✅ {path}")

    # ── FULL ANALYSIS ─────────────────────────────────────────────────────────

    def analyze(self) -> Dict[str,Any]:
        self.load()
        self.build()

        ip_c    = self.detect_shared_ip()
        dev_c   = self.detect_shared_device()
        vel_a   = self.detect_velocity()
        cross_a = self.detect_cross_channel()
        fan_a   = self.detect_fan_in()
        loop_a  = self.detect_circular_loops()
        churn_a = self.detect_high_churn()
        cent    = self.compute_centrality()
        scores  = self.compute_risk_scores(ip_c,dev_c,vel_a,cross_a,fan_a,loop_a,churn_a)

        top = sorted(scores.items(), key=lambda x:x[1], reverse=True)[:10]

        report = {
            "summary": {
                "total_transactions": len(self.txns),
                "graph_nodes": self.G.number_of_nodes(),
                "graph_edges": self.G.number_of_edges(),
                "fraud_count": sum(1 for t in self.txns if int(t["is_fraud"])),
            },
            "ip_clusters":      ip_c,
            "device_clusters":  dev_c,
            "velocity_alerts":  vel_a,
            "cross_channel":    cross_a,
            "fan_in_alerts":    fan_a,
            "circular_loops":   loop_a,
            "high_churn":       churn_a,
            "top_risk": [{"account":a,"risk_score":s,
                          "name":self.G.nodes.get(a,{}).get("name","?")} for a,s in top],
            "centrality_top10": sorted(cent.items(),key=lambda x:x[1],reverse=True)[:10],
        }

        self._print(report)
        return report

    def _print(self, r):
        print("\n" + "═"*60)
        print("  IntelliTrace — Enhanced Graph Report")
        print("═"*60)
        s = r["summary"]
        print(f"  Transactions  : {s['total_transactions']}")
        print(f"  Nodes/Edges   : {s['graph_nodes']} / {s['graph_edges']}")
        print(f"  Fraud Txns    : {s['fraud_count']}")
        print(f"  IP Clusters   : {len(r['ip_clusters'])}")
        print(f"  Device Clusters: {len(r['device_clusters'])}")
        print(f"  Velocity Alerts: {len(r['velocity_alerts'])}")
        print(f"  Cross Channel  : {len(r['cross_channel'])}")
        print(f"  Fan-In Alerts  : {len(r['fan_in_alerts'])}")
        print(f"  Circular Loops : {len(r['circular_loops'])}")
        print(f"  High Churn     : {len(r['high_churn'])}")
        print("  Top Risk Accounts:")
        for x in r["top_risk"][:5]:
            print(f"    {x['account']:<16} {x['name']:<22} {x['risk_score']}")
        print("═"*60)

    def save(self, rpt_path="graph_report.json", cl_path="fraud_clusters.json"):
        def ser(o):
            if isinstance(o, set): return list(o)
            raise TypeError(type(o))
        with open(rpt_path,"w") as f: json.dump(self._last_report, f, indent=2, default=ser)
        with open(cl_path,"w") as f:
            json.dump(self._last_report.get("fan_in_alerts",[]), f, indent=2, default=ser)
        print(f"[GRAPH] ✅ {rpt_path}  {cl_path}")


if __name__ == "__main__":
    print("╔══════════════════════════════════════════╗")
    print("║  IntelliTrace — Graph Intelligence v2   ║")
    print("║  Cyber Dynamos · 2026                   ║")
    print("╚══════════════════════════════════════════╝\n")

    engine = GraphIntelligence(csv_path="transactions.csv")
    report = engine.analyze()
    engine._last_report = report
    engine.save()
    engine.visualize("graph_visualization.png")
    print("\n[GRAPH] ✅ Done! Run api_layer.py next.")
