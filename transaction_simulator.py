"""
═══════════════════════════════════════════════════════════════════════════════
  IntelliTrace 2026 — Enhanced Transaction Simulator
  File: transaction_simulator.py
  Team: Cyber Dynamos
═══════════════════════════════════════════════════════════════════════════════
  SCHEMA (Enhanced Dataset — 22 columns):
    timestamp, txn_id, name, account_number, account_type, mobile_number,
    pincode, narration, trans_type, amount, ip_address, device,
    receiver_account, is_fraud, fraud_type, risk_score,
    account_age_days, receiver_name, receiver_pincode,
    velocity_l6h, churn_rate, ip_account_density

  FRAUD PATTERNS (5):
    1. Mule Chain       — A→B→C linear relay (same IP + device)
    2. Shared Device    — 5 accounts, 1 Samsung S23
    3. High Velocity    — 8 IMPS in minutes, velocity_l6h climbs to 9
    4. Cross Channel    — Same account, different city + IP within 2 min
    5. Mule Collection  — 8 mule accounts fan-in to 1 collector
    6. Circular Loop    — A→B→C→A cyclic laundering

  HOW TO RUN:
    pip install faker pandas
    python transaction_simulator.py
═══════════════════════════════════════════════════════════════════════════════
"""

import csv, random, uuid, datetime, json, os
from dataclasses import dataclass, asdict, field
from typing import List

random.seed(42)

# ─── MASTER DATA ──────────────────────────────────────────────────────────────

NAMES = [
    "Arjun Sharma","Priya Nair","Karthik Rajan","Meena Pillai","Rahul Gupta",
    "Deepa Krishnan","Suresh Babu","Anitha Reddy","Vijay Kumar","Lakshmi Iyer",
    "Manoj Patel","Rekha Singh","Arun Menon","Sindhu Rao","Balaji Natarajan",
    "Kavitha Srinivasan","Ramesh Verma","Jaya Devi","Ganesh Murugan","Nithya Chandran",
    "Senthil Kumar","Uma Shankar","Dinesh Raj","Saranya Venkat","Harish Naidu",
    "Swathi Balan","Vinoth Kumar","Madhavi Latha","Prakash Doss","Pooja Agarwal",
]

RECEIVER_NAMES = [
    "Priya Sharma","Anjali Gupta","Karan Malhotra","Sneha Nair","Vikram Rathore","Arun Singh",
]

PINCODES = {
    "Chennai":   ["600001","600002","600014","600028","600040","600091","600096"],
    "Bengaluru": ["560001"],
    "Mumbai":    ["400001"],
    "Delhi":     ["110001"],
    "Kolkata":   ["700001"],
    "Kochi":     ["682001"],
    "Suburban":  ["601302","602001","603202"],
}
ALL_PINCODES = [p for ps in PINCODES.values() for p in ps]

ACCOUNT_TYPES  = ["Savings","Current","Salary","Joint","NRI"]
TRANS_TYPES    = ["Online Transfer","ATM Withdrawal","UPI Payment","NEFT","IMPS","Mobile Banking","Net Banking"]
DEVICES_NORMAL = ["iPhone 13","iPhone 14","Samsung S23","Redmi Note 12","OnePlus 11",
                  "Vivo V25","Laptop-Chrome","Desktop-Firefox","Tablet-Android","ATM Terminal"]
NARRATIONS_NORMAL = [
    "Monthly salary credit","Grocery payment","Electricity bill","Rent payment",
    "Insurance premium","Loan EMI","Medical expense","Amazon purchase","Petrol expense",
    "Subscription fee",
]
NARRATIONS_FRAUD = [
    "Transfer to wallet","Quick fund move","Urgent cash out","Split transfer",
    "Relay txn","Pass-through","Layer funds","ATM burst","Rapid transfer","Fund routing",
]


# ─── DATACLASS ────────────────────────────────────────────────────────────────

@dataclass
class Transaction:
    timestamp:          str
    txn_id:             str
    name:               str
    account_number:     str
    account_type:       str
    mobile_number:      str
    pincode:            str
    narration:          str
    trans_type:         str
    amount:             float
    ip_address:         str
    device:             str
    receiver_account:   str
    is_fraud:           int
    fraud_type:         str
    risk_score:         float
    account_age_days:   float   # NEW: how old is the account
    receiver_name:      str     # NEW: receiver's name
    receiver_pincode:   str     # NEW: receiver's city pincode
    velocity_l6h:       float   # NEW: transactions by this account in last 6h
    churn_rate:         float   # NEW: 0–1, high = mule behavior
    ip_account_density: int     # NEW: how many accounts share this IP


# ─── SIMULATOR ────────────────────────────────────────────────────────────────

class TransactionSimulator:

    def __init__(self, n_normal: int = 200, seed: int = 42):
        random.seed(seed)
        self.n_normal = n_normal
        self.txns: List[Transaction] = []

        self.accounts = [f"SB{random.randint(10_000_000,99_999_999)}" for _ in range(30)]
        self.mobiles  = [f"9{random.randint(100_000_000,999_999_999)}" for _ in range(30)]
        self.ips_pool = [f"103.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}"
                         for _ in range(20)]
        self.base     = datetime.datetime(2025, 6, 1, 9, 0, 0)

        # Fixed fraud IPs
        self.ip_chain   = "103.161.159.227"
        self.ip_shared  = "103.221.93.148"
        self.ip_vel     = "103.50.181.18"
        self.ip_cross1  = "103.21.219.60"
        self.ip_cross2  = "103.172.69.180"
        self.ip_collect = "103.50.181.18"
        self.ip_loop    = "192.168.1.1"

    # helpers
    def _ts(self, dt): return dt.strftime("%Y-%m-%d %H:%M:%S")
    def _rts(self): return self.base + datetime.timedelta(hours=random.randint(0,720), minutes=random.randint(0,59))
    def _rname(self): return random.choice(RECEIVER_NAMES)
    def _rpin(self):  return random.choice(ALL_PINCODES)
    def _age(self):   return round(random.uniform(30, 1000), 0)

    # ── NORMAL ────────────────────────────────────────────────────────────────

    def generate_normal(self):
        print(f"[SIM] Generating {self.n_normal} normal transactions...")
        for _ in range(self.n_normal):
            i = random.randint(0, 29)
            self.txns.append(Transaction(
                timestamp          = self._ts(self._rts()),
                txn_id             = str(uuid.uuid4())[:8].upper(),
                name               = NAMES[i],
                account_number     = self.accounts[i],
                account_type       = random.choice(ACCOUNT_TYPES),
                mobile_number      = self.mobiles[i],
                pincode            = random.choice(ALL_PINCODES),
                narration          = random.choice(NARRATIONS_NORMAL),
                trans_type         = random.choice(TRANS_TYPES),
                amount             = round(random.uniform(500, 50_000), 2),
                ip_address         = random.choice(self.ips_pool),
                device             = random.choice(DEVICES_NORMAL),
                receiver_account   = self.accounts[random.randint(0,29)],
                is_fraud           = 0,
                fraud_type         = "Normal",
                risk_score         = round(random.uniform(2, 30), 1),
                account_age_days   = self._age(),
                receiver_name      = self._rname(),
                receiver_pincode   = self._rpin(),
                velocity_l6h       = float(random.randint(1, 2)),
                churn_rate         = round(random.uniform(0.10, 0.50), 3),
                ip_account_density = random.randint(3, 15),
            ))

    # ── FRAUD 1: Mule Chain A→B→C ────────────────────────────────────────────
    def generate_mule_chain(self):
        print("[SIM] Injecting: Mule Chain (Arjun→Priya→Karthik, same IP+device)")
        base = datetime.datetime(2025, 6, 5, 14, 0, 0)
        steps = [
            ("Arjun Sharma",  self.accounts[0], "Online Transfer", 50000, 85.0, 224.0),
            ("Priya Nair",    self.accounts[1], "Online Transfer", 48000, 88.0, 304.0),
            ("Karthik Rajan", self.accounts[2], "ATM Withdrawal",  46000, 91.0, 896.0),
        ]
        for i, (name, acc, ttype, amt, risk, age) in enumerate(steps):
            recv = self.accounts[i+1] if i < len(steps)-1 else self.accounts[3]
            self.txns.append(Transaction(
                timestamp          = self._ts(base + datetime.timedelta(seconds=i*50)),
                txn_id             = f"MULE{i+1:04d}",
                name               = name,
                account_number     = acc,
                account_type       = "Savings",
                mobile_number      = self.mobiles[i],
                pincode            = "600001",
                narration          = NARRATIONS_FRAUD[i],
                trans_type         = ttype,
                amount             = float(amt),
                ip_address         = self.ip_chain,
                device             = "iPhone 14",
                receiver_account   = recv,
                is_fraud           = 1,
                fraud_type         = "Mule Chain",
                risk_score         = risk,
                account_age_days   = age,
                receiver_name      = NAMES[i+1] if i < 2 else "ATM",
                receiver_pincode   = "600001",
                velocity_l6h       = 1.0,
                churn_rate         = round(0.943 + i * 0.02, 3),
                ip_account_density = 11,
            ))

    # ── FRAUD 2: Shared Device ────────────────────────────────────────────────
    def generate_shared_device(self):
        print("[SIM] Injecting: Shared Device (Samsung S23, 5 accounts)")
        base = datetime.datetime(2025, 6, 7, 10, 30, 0)
        victims = [
            ("Manoj Patel",      self.accounts[10], 32000, 78.0, 547.0),
            ("Rekha Singh",      self.accounts[11], 28000, 80.0, 699.0),
            ("Arun Menon",       self.accounts[12], 35000, 82.0, 843.0),
            ("Sindhu Rao",       self.accounts[13], 18000, 84.0, 504.0),
            ("Balaji Natarajan", self.accounts[14], 22000, 86.0, 45.0),
        ]
        for i, (name, acc, amt, risk, age) in enumerate(victims):
            self.txns.append(Transaction(
                timestamp          = self._ts(base + datetime.timedelta(minutes=i*2)),
                txn_id             = f"SHDEV{i+1:04d}",
                name               = name,
                account_number     = acc,
                account_type       = random.choice(ACCOUNT_TYPES),
                mobile_number      = self.mobiles[10+i],
                pincode            = "600040",
                narration          = "Rapid transfer",
                trans_type         = "Mobile Banking",
                amount             = float(amt),
                ip_address         = self.ip_shared,
                device             = "Samsung S23",
                receiver_account   = self.accounts[20+i],
                is_fraud           = 1,
                fraud_type         = "Shared Device",
                risk_score         = risk,
                account_age_days   = age,
                receiver_name      = self._rname(),
                receiver_pincode   = "600002",
                velocity_l6h       = float(1 + (i // 4)),
                churn_rate         = round(0.913 + i * 0.015, 3),
                ip_account_density = 14,
            ))

    # ── FRAUD 3: High Velocity ────────────────────────────────────────────────
    def generate_high_velocity(self):
        print("[SIM] Injecting: High Velocity (8 IMPS in 4 min, velocity_l6h 2→9)")
        base = datetime.datetime(2025, 6, 9, 16, 0, 0)
        for i in range(8):
            self.txns.append(Transaction(
                timestamp          = self._ts(base + datetime.timedelta(seconds=i*35)),
                txn_id             = f"HVEL{i+1:04d}",
                name               = "Senthil Kumar",
                account_number     = self.accounts[20],
                account_type       = "Current",
                mobile_number      = self.mobiles[20],
                pincode            = "600096",
                narration          = "Split transfer",
                trans_type         = "IMPS",
                amount             = round(9990 - i*100, 2),
                ip_address         = self.ip_vel,
                device             = "Laptop-Chrome",
                receiver_account   = self.accounts[(21+i) % 30],
                is_fraud           = 1,
                fraud_type         = "High Velocity",
                risk_score         = round(90.0 + i*0.5, 1),
                account_age_days   = 463.0,
                receiver_name      = self._rname(),
                receiver_pincode   = self._rpin(),
                velocity_l6h       = float(i + 2),   # escalates: 2,3,4...9
                churn_rate         = round(0.907 + i*0.01, 3),
                ip_account_density = 19,
            ))

    # ── FRAUD 4: Cross Channel ────────────────────────────────────────────────
    def generate_cross_channel(self):
        print("[SIM] Injecting: Cross Channel (Saranya Venkat, Chennai+Delhi 45s)")
        self.txns.append(Transaction(
            timestamp="2025-06-10 11:05:00", txn_id="CROSS001",
            name="Saranya Venkat", account_number=self.accounts[23],
            account_type="Savings", mobile_number=self.mobiles[23],
            pincode="600001", narration="ATM Withdrawal Chennai",
            trans_type="ATM Withdrawal", amount=20000.0,
            ip_address=self.ip_cross1, device="ATM Terminal",
            receiver_account="SELF", is_fraud=1, fraud_type="Cross Channel",
            risk_score=95.0, account_age_days=546.0,
            receiver_name="SELF", receiver_pincode="600001",
            velocity_l6h=1.0, churn_rate=0.921, ip_account_density=6,
        ))
        self.txns.append(Transaction(
            timestamp="2025-06-10 11:05:45", txn_id="CROSS002",
            name="Saranya Venkat", account_number=self.accounts[23],
            account_type="Savings", mobile_number=self.mobiles[23],
            pincode="110001", narration="Net Banking Delhi",
            trans_type="Net Banking", amount=35000.0,
            ip_address=self.ip_cross2, device="Desktop-Firefox",
            receiver_account=self.accounts[28], is_fraud=1, fraud_type="Cross Channel",
            risk_score=95.0, account_age_days=546.0,
            receiver_name=self._rname(), receiver_pincode="110001",
            velocity_l6h=2.0, churn_rate=0.919, ip_account_density=5,
        ))

    # ── FRAUD 5: Mule Collection (Fan-In) ─────────────────────────────────────
    def generate_mule_collection(self):
        print("[SIM] Injecting: Mule Collection (8 accounts → COLL_ACC_01, fan-in)")
        base = datetime.datetime(2025, 7, 2, 10, 0, 0)
        for i in range(8):
            self.txns.append(Transaction(
                timestamp          = self._ts(base + datetime.timedelta(minutes=i)),
                txn_id             = f"FAN{i}",
                name               = f"Mule{i}",
                account_number     = f"MULE_ACC_{i}",
                account_type       = "Savings",
                mobile_number      = "9999999999",
                pincode            = "600001",
                narration          = "Transfer",
                trans_type         = "UPI Payment",
                amount             = 5000.0,
                ip_address         = self.ip_collect,
                device             = "OnePlus 11",
                receiver_account   = "COLL_ACC_01",
                is_fraud           = 1,
                fraud_type         = "Mule Collection",
                risk_score         = 90.0,
                account_age_days   = 5.0,   # Very new accounts — red flag
                receiver_name      = "Target",
                receiver_pincode   = "603202",
                velocity_l6h       = 1.0,
                churn_rate         = round(0.904 + random.uniform(0, 0.07), 3),
                ip_account_density = 19,
            ))

    # ── FRAUD 6: Circular Loop A→B→C→A ───────────────────────────────────────
    def generate_circular_loop(self):
        print("[SIM] Injecting: Circular Loop (Alpha→Beta→Gamma→Alpha)")
        base = datetime.datetime(2025, 7, 2, 15, 0, 0)
        steps = [
            ("Alpha","ACC_A","ACC_B",10000.0),
            ("Beta", "ACC_B","ACC_C", 9900.0),
            ("Gamma","ACC_C","ACC_A", 9800.0),
        ]
        for i, (name, sender, recv, amt) in enumerate(steps):
            self.txns.append(Transaction(
                timestamp          = self._ts(base + datetime.timedelta(minutes=i*5)),
                txn_id             = f"LOOP{i+1}",
                name               = name,
                account_number     = sender,
                account_type       = "Savings",
                mobile_number      = "9999999999",
                pincode            = "600001",
                narration          = "Transfer",
                trans_type         = "UPI Payment",
                amount             = amt,
                ip_address         = self.ip_loop,
                device             = "OnePlus 11",
                receiver_account   = recv,
                is_fraud           = 1,
                fraud_type         = "Circular Loop",
                risk_score         = round(90.0 + i*1.5, 1),
                account_age_days   = 5.0,
                receiver_name      = "Target",
                receiver_pincode   = "603202",
                velocity_l6h       = float(i+1),
                churn_rate         = round(0.903 + i*0.026, 3),
                ip_account_density = 3,
            ))

    # ── EXPORT ────────────────────────────────────────────────────────────────

    def run(self):
        self.generate_normal()
        self.generate_mule_chain()
        self.generate_shared_device()
        self.generate_high_velocity()
        self.generate_cross_channel()
        self.generate_mule_collection()
        self.generate_circular_loop()
        self.txns.sort(key=lambda t: t.timestamp)
        return self.txns

    def to_csv(self, path="transactions.csv"):
        fields = list(Transaction.__dataclass_fields__.keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows([asdict(t) for t in self.txns])
        print(f"[SIM] ✅ {len(self.txns)} rows → {path}")

    def to_json(self, path="transactions.json"):
        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump([asdict(t) for t in self.txns], f, indent=2)
        print(f"[SIM] ✅ JSON → {path}")

    def to_fraud_csv(self, path="fraud_only.csv"):
        fraud = [t for t in self.txns if t.is_fraud]
        fields = list(Transaction.__dataclass_fields__.keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows([asdict(t) for t in fraud])
        print(f"[SIM] ✅ {len(fraud)} fraud rows → {path}")

    def summary(self):
        from collections import Counter
        total  = len(self.txns)
        fraud  = [t for t in self.txns if t.is_fraud]
        print("\n" + "═"*60)
        print("  IntelliTrace — Enhanced Simulator Summary")
        print("═"*60)
        print(f"  Total        : {total}")
        print(f"  Normal       : {total - len(fraud)}")
        print(f"  Fraud        : {len(fraud)}  ({len(fraud)/total*100:.1f}%)")
        print()
        for ft, txns in Counter(t.fraud_type for t in fraud).items():
            grp = [t for t in fraud if t.fraud_type==ft]
            print(f"  {ft:<20} {txns:>3} txns  ₹{sum(t.amount for t in grp):>10,.0f}  "
                  f"avg_risk: {sum(t.risk_score for t in grp)/len(grp):.1f}  "
                  f"avg_churn: {sum(t.churn_rate for t in grp)/len(grp):.3f}")
        print("═"*60)


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("╔══════════════════════════════════════════╗")
    print("║  IntelliTrace — Enhanced Simulator       ║")
    print("║  Cyber Dynamos · 2026                    ║")
    print("╚══════════════════════════════════════════╝\n")

    sim = TransactionSimulator(n_normal=200)
    sim.run()
    sim.summary()
    sim.to_csv("transactions.csv")
    sim.to_fraud_csv("fraud_only.csv")
    sim.to_json("transactions.json")
    print("\n[SIM] Done! Run graph_intelligence.py next.")
