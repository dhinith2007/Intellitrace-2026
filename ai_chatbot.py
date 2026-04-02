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

FALLBACK_RESPONSES = {
    "fraud pattern": (
        "🔍 6 fraud patterns detected:\n<br>"
        "1. Mule Chain (Risk 94)<br>"
        "2. Shared Device (Risk 86)<br>"
        "3. High Velocity (Risk 93.5)<br>"
        "4. Cross Channel (Risk 95)<br>"
        "5. Mule Collection (Risk 90)<br>"
        "6. Circular Loop (Risk 93)"
    ),
    "risk": (
        "📊 Highest risk accounts:\n<br>"
        "• Saranya Venkat   — 95.0 (Cross Channel)<br>"
        "• Senthil Kumar    — 93.5 (High Velocity)<br>"
        "• Karthik Rajan    — 91.0 (Mule Chain)"
    ),
    "mule": (
        "🔴 Mule Chain Detected:<br>"
        "• Arjun Sharma → Priya Nair → Karthik Rajan → ATM<br>"
        "• Shared IP: 103.161.159.227<br>"
        "• Action: Freeze all 4 accounts immediately."
    ),
    "default": (
        "[SYSTEM MESSAGE]<br>"
        "The live AI connection is currently unreachable (Missing API Key or openrouter issue).<br><br>"
        "I can still provide static data about:<br>"
        "• Fraud patterns<br>"
        "• Risk scores<br>"
        "• Mule chains"
    )
}

def _fallback_response(query: str) -> str:
    q = query.lower()
    for key, resp in FALLBACK_RESPONSES.items():
        if key in q:
            return resp
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