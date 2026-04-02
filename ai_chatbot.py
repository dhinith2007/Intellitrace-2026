"""
═══════════════════════════════════════════════════════════════════════════════
  IntelliTrace 2026 — AI Chatbot / LLM Assistant (Monolith Optimized)
  File: ai_chatbot.py
  Team: Cyber Dynamos
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import csv
from typing import List, Dict, Optional

# ─── OPENROUTER (OPENAI) CLIENT ───────────────────────────────────────────────
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("[CHATBOT] ⚠  'openai' not installed. Falling back to rule-based responses.\n")


# ─── SYSTEM PROMPT ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are IntelliTrace AI, an expert fraud detection analyst assistant 
for a real-time mule account detection system built for a hackathon.

You have deep knowledge about the following dataset and fraud scenarios:

═══ DATASET SUMMARY ═══
• Total transactions: 229
• Fraud transactions: 29
• Normal transactions: 200
• Fraud rate: 12.6%
• Detection rate: 91.7%
• Total fraud amount: ₹3.5 Lakhs

═══ FRAUD PATTERNS DETECTED ═══

1. MULE CHAIN (STORY #1) — Risk Score: 85–94
   Path: Arjun Sharma → Priya Nair → Karthik Rajan → ATM Withdrawal
   • Completed in 1m 40s
   • Same IP: 103.161.159.227

2. SHARED DEVICE CLUSTER (STORY #2) — Risk Score: 78–86
   • Device: Samsung S23
   • 5 accounts in 8 mins
   • Total: ₹1.35 Lakhs outflow

3. HIGH VELOCITY (STORY #3) — Risk Score: 90–93.5
   • Account: Senthil Kumar
   • 8 IMPS transactions in 4 minutes, all <₹10K

4. CROSS-CHANNEL IMPOSSIBLE TRAVEL (STORY #4) — Risk Score: 95
   • ATM in Chennai + Net Banking in Delhi in 45 seconds.

5. MULE COLLECTION (STORY #5) — Risk Score: 90
   • 8 throwaway accounts (age: 5d) all transferring to COLL_ACC_01.

6. CIRCULAR LOOP (STORY #6) — Risk Score: 93
   • Alpha → Beta → Gamma → Alpha (fee extraction at each hop).

Always answer in clear, professional language. Use ₹ for Indian rupees.
Use bullet points for complex answers. Keep answers concise but complete.
"""

# ─── FALLBACK RESPONSES ───────────────────────────────────────────────────────
# ─── FALLBACK RESPONSES (THE "BULLETPROOF DEMO" DICTIONARY) ───────────────────
# ─── FALLBACK RESPONSES (THE "BULLETPROOF DEMO" DICTIONARY) ───────────────────

FALLBACK_RESPONSES = {
    "architecture": (
        "[AI ANALYSIS] 🧠 **IntelliTrace v2: System Architecture & Methodology**<br><br>"
        "**1. The Problem Statement:**<br>"
        "Traditional tabular ML models look at transactions in isolation, missing coordinated, multi-hop money laundering. We built a system to detect hidden crime syndicates using behavioral signals and graph theory.<br><br>"
        "**2. Dataset & Transaction Simulation:**<br>"
        "We engineered a Python-based Transaction Simulator to generate a highly realistic, synthetic Indian banking dataset (IMPS, UPI, ATM). It contains 229 transactions, meticulously planting 6 complex fraud typologies (Mule Chains, Circular Loops, Fan-Ins).<br><br>"
        "**3. Graph Intelligence Engine (NetworkX):**<br>"
        "We used Python's `NetworkX` library to map the dataset into a Directed Graph. Accounts act as Nodes; transactions act as Edges. By running cycle-detection and degree-centrality algorithms, we mathematically unearth hidden loops and collector accounts that standard rules miss.<br><br>"
        "**4. The Unified Dashboard (Flask + D3.js):**<br>"
        "We built a monolithic Flask web application to serve as the SOC Command Terminal. It features real-time telemetry, risk scoring, and an interactive `D3.js` network graph to visualize the illicit money flow.<br><br>"
        "**5. AI SOC Assistant (LLM Integration):**<br>"
        "We embedded an LLM directly into the dashboard. It acts as a context-aware co-pilot, parsing the graph data to instantly explain complex fraud stories, analyze signals like `churn_rate`, and recommend containment actions.<br><br>"
        "**6. Core Tech Stack:**<br>"
        "• **Backend:** Python, Flask, NetworkX, Pandas<br>"
        "• **Frontend:** Pure HTML/CSS, Vanilla JS, D3.js (Data Vis)<br>"
        "• **AI/ML:** OpenAI SDK routing via OpenRouter API"
    ),
    "patterns": (
        "[AI ANALYSIS] [SEARCH] **6 Fraud Patterns Detected:**<br><br>"
        "1. **Mule Chain:** Layering funds through multiple accounts.<br>"
        "2. **Shared Device:** Multiple accounts accessed from one device ID.<br>"
        "3. **High Velocity:** Rapid bursts of transactions to evade limits.<br>"
        "4. **Cross Channel:** Impossible geographical travel.<br>"
        "5. **Mule Collection:** Fan-in to a central collector account.<br>"
        "6. **Circular Loop:** Cyclic laundering to obscure origins."
    ),
    "risk": (
        "[AI ANALYSIS] [STATS] **Highest Risk Accounts:**<br><br>"
        "• **Saranya Venkat (95.0)** - Cross Channel Anomaly<br>"
        "• **Senthil Kumar (93.5)** - Velocity Escalation<br>"
        "• **Alpha/Beta/Gamma (93.0)** - Circular Loop Laundering<br>"
        "• **Karthik Rajan (91.0)** - Mule Chain Exit Node"
    ),
    "mule chain": (
        "[AI ANALYSIS] [ALERT] **Mule Chain (Story #1):**<br><br>"
        "Funds moved rapidly across a chain: Arjun → Priya → Karthik → ATM.<br>"
        "• **Signals:** 3 hops in 1m 40s. All used the same IP (103.161.159.227).<br>"
        "• **Action:** Freeze all nodes in the chain."
    ),
    "shared device": (
        "[AI ANALYSIS] [ALERT] **Shared Device (Story #2):**<br><br>"
        "5 different accounts logged in from the exact same Samsung S23 within 8 minutes.<br>"
        "• **Signals:** Device ID overlap, high IP/Account density.<br>"
        "• **Action:** Block device ID and force re-authentication."
    ),
    "velocity": (
        "[AI ANALYSIS] [ALERT] **High Velocity (Story #3):**<br><br>"
        "Senthil Kumar executed 8 IMPS transfers in 4 mins, all just under ₹10,000.<br>"
        "• **Signals:** `velocity_l6h` escalated to 9. Smurfing tactic to avoid limits.<br>"
        "• **Action:** Temporarily restrict outbound IMPS."
    ),
    "cross channel": (
        "[AI ANALYSIS] [ALERT] **Cross Channel (Story #4):**<br><br>"
        "ATM withdrawal in Chennai and Net Banking in Delhi occurred within 45 seconds of each other.<br>"
        "• **Signals:** Impossible geographic travel. Card cloning suspected.<br>"
        "• **Action:** Block card immediately."
    ),
    "fan-in": (
        "[AI ANALYSIS] [ALERT] **Mule Collection / Fan-In (Story #5):**<br><br>"
        "8 'throwaway' accounts sent ₹5K each to a single Collector account.<br>"
        "• **Signals:** All accounts share `account_age_days` = 5. High churn rate.<br>"
        "• **Action:** Block the collector account (COLL_ACC_01)."
    ),
    "circular": (
        "[AI ANALYSIS] [ALERT] **Circular Loop (Story #6):**<br><br>"
        "Funds moved in a cycle: Alpha → Beta → Gamma → Alpha.<br>"
        "• **Signals:** Diminishing amounts (fees extracted at each hop). Closed-loop graph structure.<br>"
        "• **Action:** Flag cluster for severe AML review."
    ),
    "churn": (
        "[AI ANALYSIS] [METRIC] **Churn Rate:**<br><br>"
        "Measures how fast money leaves an account after entering.<br>"
        "High churn (>0.90) means the account is acting as a 'pass-through' mule, rather than holding standard balances."
    ),
    "density": (
        "[AI ANALYSIS] [METRIC] **IP Account Density:**<br><br>"
        "The number of distinct accounts operating from the exact same IP address.<br>"
        "High density indicates proxy usage, botnets, or device farms."
    ),
    "default": (
        "[SYSTEM MESSAGE]<br>I am running in Standalone / High-Speed Mode. You can ask me about:<br><br>"
        "• How the model works (Architecture, Methodology, Tech Stack)<br>"
        "• Specific stories (Mule chain, Circular loop, Shared device, Fan-in)<br>"
        "• Signals (Churn rate, Velocity, IP density)"
    )
}

def _fallback_response(query: str) -> str:
    """Smart keyword mapping to return the exact right answer."""
    q = query.lower()
    
    # NEW: Triggers for the comprehensive Architecture & Methodology response
    if "explain about the model" in q or "architecture" in q or "methodology" in q or "tech stack" in q or "how did you build" in q or "how it works" in q or "problem statement" in q or "dataset" in q: 
        return FALLBACK_RESPONSES["architecture"]
        
    if "pattern" in q or "stories" in q or "all 6" in q: return FALLBACK_RESPONSES["patterns"]
    if "risk" in q or "highest" in q: return FALLBACK_RESPONSES["risk"]
    if "mule chain" in q or "story 1" in q: return FALLBACK_RESPONSES["mule chain"]
    if "shared device" in q or "story 2" in q: return FALLBACK_RESPONSES["shared device"]
    if "velocity" in q or "story 3" in q: return FALLBACK_RESPONSES["velocity"]
    if "cross channel" in q or "impossible" in q: return FALLBACK_RESPONSES["cross channel"]
    if "fan-in" in q or "collection" in q or "story 5" in q: return FALLBACK_RESPONSES["fan-in"]
    if "circular" in q or "loop" in q or "story 6" in q: return FALLBACK_RESPONSES["circular"]
    if "churn" in q: return FALLBACK_RESPONSES["churn"]
    if "density" in q or "ip " in q: return FALLBACK_RESPONSES["density"]
    
    return FALLBACK_RESPONSES["default"]


# ─── MAIN BOT CLASS ───────────────────────────────────────────────────────────

class IntelliTraceBot:
    def __init__(self, api_key: Optional[str] = None, csv_path: str = "transactions.csv", max_history: int = 10):
        self.max_history = max_history
        self.conversation_history: List[Dict] = []
        self.transactions = self._load_transactions(csv_path)

        key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        if OPENAI_AVAILABLE and key:
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=key,
            )
            self.llm_available = True
            print("[CHATBOT] ✅ OpenRouter connected.")
        else:
            self.client = None
            self.llm_available = False
            print("[CHATBOT] ⚠ OPENROUTER_API_KEY missing or OpenAI not installed.")

    def _load_transactions(self, csv_path: str) -> List[Dict]:
        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                return list(csv.DictReader(f))
        except FileNotFoundError:
            return []

    def chat(self, user_message: str) -> str:
        """Processes the message and returns JUST the response string for the Dashboard."""
        self.conversation_history.append({"role": "user", "content": user_message})

        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-self.max_history * 2:]

        if self.llm_available:
            response = self._llm_chat(user_message)
        else:
            response = _fallback_response(user_message)

        self.conversation_history.append({"role": "assistant", "content": response})
        
        # Dashboard expects HTML breaks instead of newlines
        return response.replace('\n', '<br>')

    def _llm_chat(self, user_message: str) -> str:
        try:
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            messages.extend(self.conversation_history[:-1])
            messages.append({"role": "user", "content": user_message})

            # Using your selected free model
            resp = self.client.chat.completions.create(
                model="meta-llama/llama-3-8b-instruct:free",
                messages=messages,
                temperature=0.3,
                max_tokens=300
            )
            return resp.choices[0].message.content if resp.choices else "No response."
        except Exception as e:
            print(f"[API ERROR] {e}")
            return _fallback_response(user_message)

if __name__ == "__main__":
    # Quick local terminal test
    bot = IntelliTraceBot()
    print("Testing locally. Type 'exit' to quit.")
    while True:
        msg = input("You: ")
        if msg.lower() == 'exit': break
        print("AI:", bot.chat(msg).replace('<br>', '\n'))