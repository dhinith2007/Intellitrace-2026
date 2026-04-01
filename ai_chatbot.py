"""
═══════════════════════════════════════════════════════════════════════════════
  IntelliTrace 2026 — AI Chatbot / LLM Assistant
  File: ai_chatbot.py
  Team: Cyber Dynamos
═══════════════════════════════════════════════════════════════════════════════
  PURPOSE:
    A terminal-based + API-ready AI chatbot that answers fraud-related
    questions using OpenRouter (OpenAI-compatible API).

    The chatbot has full context about the IntelliTrace dataset and can:
      - Explain any fraud pattern detected
      - Answer risk score queries
      - Describe fraud stories step-by-step
      - Suggest preventive actions
      - Answer natural language questions about transactions

  HOW TO RUN:
    pip install openai requests
    python ai_chatbot.py                 ← Terminal interactive mode
    python ai_chatbot.py --api           ← Starts chatbot as a REST endpoint

  USAGE MODES:
    1. Terminal mode:   python ai_chatbot.py
    2. API mode:        python ai_chatbot.py --api
    3. Single query:    python ai_chatbot.py --query "What is the highest risk account?"
    4. Import in code:  from ai_chatbot import IntelliTraceBot; bot = IntelliTraceBot()

  REQUIREMENTS:
    - Set OPENROUTER_API_KEY environment variable, OR
    - Pass api_key directly to IntelliTraceBot(api_key="your_key_here")

  API ENDPOINT (when --api flag used):
    POST /chat   { "message": "Which accounts are highest risk?" }
    GET  /history
    GET  /reset
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import json
import csv
import datetime
import argparse
from typing import List, Dict, Optional, Tuple

# ─── OPENROUTER (OPENAI) CLIENT ───────────────────────────────────────────────
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("[CHATBOT] ⚠  'openai' not installed. Run: pip install openai")
    print("[CHATBOT]    Falling back to rule-based responses.\n")


# ─── SYSTEM PROMPT ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are IntelliTrace AI, an expert fraud detection analyst assistant 
for a real-time mule account detection system built for a hackathon.

You have deep knowledge about the following dataset and fraud scenarios:

═══ DATASET SUMMARY ═══
• Total transactions: 218
• Fraud transactions: 18
• Normal transactions: 200
• Fraud rate: 8.3%
• Detection rate: 91.7%
• Total fraud amount: ₹4.2 Lakhs

═══ FRAUD PATTERNS DETECTED ═══

1. MULE CHAIN (STORY #1) — Risk Score: 85–94
   Path: Arjun Sharma → Priya Nair → Karthik Rajan → ATM Withdrawal
   • Completed in 2 minutes 30 seconds (14:00:00 to 14:02:30)
   • All 4 nodes used same IP address: 103.45.12.78
   • All used same device: iPhone 14
   • Pincode: 600001 (Chennai North)
   • Amounts: ₹50,000 → ₹48,000 → ₹46,000 → ₹44,000 (ATM exit)
   • Pattern: Classic money laundering layering phase

2. SHARED DEVICE CLUSTER (STORY #2) — Risk Score: 78–86
   • Device: Samsung S23
   • 5 accounts: Manoj Patel, Rekha Singh, Arun Menon, Sindhu Rao, Balaji Natarajan
   • All transactions between 10:30 and 10:38 (8 minutes)
   • IP: 103.78.90.12
   • Total: ~₹1.35 Lakhs via Mobile Banking
   • Pattern: Device takeover / credential harvesting / SIM swap

3. HIGH VELOCITY (STORY #3) — Risk Score: 90–93.5
   • Account: Senthil Kumar (SB11223344)
   • 8 IMPS transactions in 4 minutes (16:00 to 16:04)
   • All amounts just under ₹10,000 to evade detection
   • Total: ₹77,120 to 8 different receiver accounts
   • IP: 103.22.33.44, Device: Laptop-Chrome
   • Pattern: Structured transactions + velocity attack

4. CROSS-CHANNEL IMPOSSIBLE TRAVEL (STORY #4) — Risk Score: 95
   • Account: Pooja Agarwal (SB44332211)
   • ATM Withdrawal in Chennai at 11:05:00 (PIN: 600001)
   • Net Banking in Delhi at 11:05:45 (PIN: 110001)
   • Only 45 seconds between two geographically impossible locations
   • Pattern: Card cloning + credential theft

═══ RISK SCORING ═══
• 0–30: Normal (no action)
• 31–60: Low Risk (monitor)
• 61–80: Medium Risk (flag for review)
• 81–90: High Risk (temporary block + KYC)
• 91–100: Critical (immediate freeze + SAR filing)

═══ RECOMMENDATIONS ═══
• Mule Chain: Freeze all 4 accounts, trace fund source, file FIR
• Shared Device: Force re-authentication, contact account holders, block device ID
• High Velocity: Temporary transaction hold, velocity limit enforcement
• Cross-Channel: Immediate account freeze, card block, police intimation

Always answer in clear, professional language. Use ₹ for Indian rupees.
Use bullet points for complex answers. Keep answers concise but complete.
If asked about specific account numbers or transactions, refer to the dataset above.
"""


# ─── FALLBACK RESPONSES (when API unavailable) ───────────────────────────────

FALLBACK_RESPONSES = {
    "fraud pattern": (
        "🔍 4 fraud patterns detected:\n"
        "1. Mule Chain (Risk 94) — A→B→C→ATM in 2.5 min\n"
        "2. Shared Device (Risk 86) — Samsung S23, 5 accounts\n"
        "3. High Velocity (Risk 93.5) — 8 IMPS in 4 min\n"
        "4. Cross Channel (Risk 95) — Chennai + Delhi in 45s"
    ),
    "risk": (
        "📊 Highest risk accounts:\n"
        "• Pooja Agarwal    — 95.0 (Cross Channel)\n"
        "• Meena Pillai     — 94.0 (Mule Chain ATM exit)\n"
        "• Senthil Kumar    — 93.5 (High Velocity IMPS)\n"
        "• Karthik Rajan    — 91.0 (Mule Chain hop 3)\n"
        "• Priya Nair       — 88.0 (Mule Chain hop 2)"
    ),
    "mule": (
        "🔴 Mule Chain: Arjun Sharma → Priya Nair → Karthik Rajan → ATM\n"
        "• Duration: 2 minutes 30 seconds\n"
        "• Same IP (103.45.12.78) + Same device (iPhone 14)\n"
        "• Amounts: ₹50K → ₹48K → ₹46K → ₹44K (ATM exit)\n"
        "• Action: Freeze all 4 accounts immediately"
    ),
    "default": (
        "I can answer questions about:\n"
        "• Fraud patterns (mule chain, shared device, velocity, cross-channel)\n"
        "• Risk scores and account analysis\n"
        "• Fraud stories and step-by-step explanations\n"
        "• Preventive recommendations\n\n"
        "Please install 'openai' and set OPENROUTER_API_KEY for full AI responses."
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
    """
    AI-powered chatbot for the IntelliTrace fraud detection system.
    Uses OpenRouter to access LLMs like LLaMA 3.
    """

    def __init__(self,
                 api_key: Optional[str] = None,
                 csv_path: str = "transactions.csv",
                 max_history: int = 20):
        """
        Args:
            api_key:     OpenRouter API key. Falls back to OPENROUTER_API_KEY env var.
            csv_path:    Path to transactions CSV for live data context.
            max_history: Max conversation turns to keep in memory.
        """
        self.max_history = max_history
        self.conversation_history: List[Dict] = []

        # Load live transaction data for context
        self.transactions = self._load_transactions(csv_path)

        # Initialize OpenRouter client via OpenAI package
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
            if not key:
                print("[CHATBOT] ⚠  OPENROUTER_API_KEY not set — using fallback responses.")

    # ── Data Loading ──────────────────────────────────────────────────────────

    def _load_transactions(self, csv_path: str) -> List[Dict]:
        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                return list(csv.DictReader(f))
        except FileNotFoundError:
            print(f"[CHATBOT] ℹ  {csv_path} not found — using built-in context only.")
            return []

    def _build_live_context(self) -> str:
        """Build a short summary of live transaction data for context injection."""
        if not self.transactions:
            return ""
        fraud = [t for t in self.transactions if int(t.get("is_fraud", 0))]
        normal = [t for t in self.transactions if not int(t.get("is_fraud", 0))]
        total_fraud_amt = sum(float(t["amount"]) for t in fraud)
        return (
            f"\n[LIVE DATA] {len(self.transactions)} transactions loaded. "
            f"{len(fraud)} fraud, {len(normal)} normal. "
            f"Total fraud amount: ₹{total_fraud_amt:,.0f}."
        )

    # ── Core Chat ─────────────────────────────────────────────────────────────

    def chat(self, user_message: str) -> Tuple[str, dict]:
        """
        Send a message and get a response.

        Returns:
            (response_text, metadata_dict)
        """
        self.conversation_history.append({
            "role":    "user",
            "content": user_message
        })

        # Trim history
        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-self.max_history * 2:]

        if self.llm_available:
            response, meta = self._llm_chat(user_message)
        else:
            response = _fallback_response(user_message)
            meta = {"source": "fallback", "model": "rule-based"}

        self.conversation_history.append({
            "role":    "assistant",
            "content": response
        })
        return response, meta

    def _llm_chat(self, user_message: str) -> Tuple[str, dict]:
        """Call the OpenRouter API."""
        try:
            # Build system prompt with live context
            system = SYSTEM_PROMPT + self._build_live_context()
            
            # Format messages for OpenRouter
            messages = [{"role": "system", "content": system}]
            # Add history (excluding the very last user message which is handled below)
            messages.extend(self.conversation_history[:-1])
            # Add current user message
            messages.append({"role": "user", "content": user_message})

            # Select model: meta-llama/llama-3-8b-instruct:free is free and fast on OpenRouter
            target_model = "meta-llama/llama-3-8b-instruct:free"

            resp = self.client.chat.completions.create(
                model=target_model,
                messages=messages,
                extra_headers={
                    "HTTP-Referer": "https://intellitrace-hackathon.local", # Optional but recommended
                    "X-Title": "IntelliTrace App", # Optional but recommended
                }
            )
            
            text = resp.choices[0].message.content if resp.choices else "No response."
            
            # Attempt to gather token metrics if available
            input_tokens = resp.usage.prompt_tokens if hasattr(resp, "usage") else 0
            output_tokens = resp.usage.completion_tokens if hasattr(resp, "usage") else 0

            meta = {
                "source":        "openrouter",
                "model":         target_model,
                "input_tokens":  input_tokens,
                "output_tokens": output_tokens,
            }
            return text, meta

        except Exception as e:
            error_msg = f"⚠ API error: {e}\n\n" + _fallback_response(user_message)
            return error_msg, {"source": "fallback_error", "error": str(e)}

    # ── Convenience Methods ───────────────────────────────────────────────────

    def quick_summary(self) -> str:
        """Get a quick fraud summary."""
        resp, _ = self.chat("Give me a quick summary of all fraud detected in 5 bullet points.")
        return resp

    def explain_fraud(self, fraud_type: str) -> str:
        """Explain a specific fraud type."""
        resp, _ = self.chat(f"Explain the {fraud_type} fraud pattern in detail with recommendations.")
        return resp

    def analyze_account(self, account_number: str) -> str:
        """Analyze a specific account."""
        # Find transactions for this account
        acc_txns = [t for t in self.transactions if t.get("account_number") == account_number]
        if acc_txns:
            context = f"Account {account_number} has {len(acc_txns)} transactions. "
            fraud_txns = [t for t in acc_txns if int(t.get("is_fraud", 0))]
            if fraud_txns:
                context += f"{len(fraud_txns)} are flagged as fraud ({fraud_txns[0]['fraud_type']}). "
                context += f"Max risk score: {max(float(t['risk_score']) for t in acc_txns):.1f}. "
            query = context + f"Analyze this account and provide a risk assessment."
        else:
            query = f"Analyze account {account_number} based on what you know."
        resp, _ = self.chat(query)
        return resp

    def reset(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []
        print("[CHATBOT] Conversation history cleared.")

    def get_history(self) -> List[Dict]:
        """Return conversation history."""
        return self.conversation_history


# ─── TERMINAL INTERACTIVE MODE ────────────────────────────────────────────────

QUICK_COMMANDS = {
    "/summary":   "Give me a fraud summary in 5 bullet points.",
    "/mule":      "Explain the mule chain fraud pattern in detail.",
    "/device":    "Explain the shared device fraud cluster.",
    "/velocity":  "Explain the high velocity IMPS fraud attack.",
    "/cross":     "Explain the cross-channel impossible travel fraud.",
    "/top":       "Which accounts have the highest risk score?",
    "/amount":    "What is the total fraud amount detected?",
    "/recommend": "What are your recommendations for each fraud type?",
    "/help":      None,
    "/reset":     None,
    "/quit":      None,
}

def run_terminal(bot: IntelliTraceBot) -> None:
    """Interactive terminal chatbot loop."""
    print("\n" + "╔" + "═"*56 + "╗")
    print("║   IntelliTrace AI Assistant — Terminal Mode          ║")
    print("║   Type /help for commands · /quit to exit            ║")
    print("╚" + "═"*56 + "╝\n")

    bot_intro, _ = bot.chat("Hello! Give me a one-paragraph intro about what you can help with.")
    print(f"🤖 IntelliTrace AI:\n{bot_intro}\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[CHATBOT] Goodbye!")
            break

        if not user_input:
            continue

        # Handle commands
        if user_input == "/quit":
            print("[CHATBOT] Session ended. Goodbye!")
            break
        elif user_input == "/reset":
            bot.reset()
            print("🤖 Conversation reset.\n")
            continue
        elif user_input == "/help":
            print("\n📋 Quick Commands:")
            for cmd, desc in QUICK_COMMANDS.items():
                if desc:
                    print(f"  {cmd:<15} → {desc[:55]}")
            print()
            continue
        elif user_input in QUICK_COMMANDS and QUICK_COMMANDS[user_input]:
            user_input = QUICK_COMMANDS[user_input]

        # Send to bot
        print("\n🤖 IntelliTrace AI: ", end="", flush=True)
        response, meta = bot.chat(user_input)
        print(response)
        if meta.get("source") == "openrouter":
            tokens = meta.get("output_tokens", 0)
            print(f"\n   [Model: {meta.get('model','?')} · {tokens} tokens]\n")
        else:
            print()


# ─── API SERVER MODE ──────────────────────────────────────────────────────────

def run_api_server(bot: IntelliTraceBot, port: int = 8001) -> None:
    """Run chatbot as a simple HTTP API (no FastAPI dependency needed)."""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import urllib.parse

    class ChatHandler(BaseHTTPRequestHandler):

        def log_message(self, format, *args):
            pass  # Suppress default logs

        def _send_json(self, data: dict, status: int = 200) -> None:
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", len(body))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self):
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

        def do_GET(self):
            path = self.path.split("?")[0]
            if path == "/":
                self._send_json({"status": "online", "service": "IntelliTrace Chatbot API",
                                 "endpoints": ["/chat (POST)", "/history (GET)", "/reset (GET)"]})
            elif path == "/history":
                self._send_json({"history": bot.get_history()})
            elif path == "/reset":
                bot.reset()
                self._send_json({"status": "reset", "message": "Conversation cleared."})
            else:
                self._send_json({"error": "Not found"}, 404)

        def do_POST(self):
            if self.path == "/chat":
                length = int(self.headers.get("Content-Length", 0))
                body   = self.rfile.read(length)
                try:
                    data    = json.loads(body)
                    message = data.get("message", "").strip()
                    if not message:
                        self._send_json({"error": "message field required"}, 400)
                        return
                    response, meta = bot.chat(message)
                    self._send_json({
                        "response":  response,
                        "timestamp": datetime.datetime.now().isoformat(),
                        "meta":      meta
                    })
                except json.JSONDecodeError:
                    self._send_json({"error": "Invalid JSON"}, 400)
            else:
                self._send_json({"error": "Not found"}, 404)

    server = HTTPServer(("127.0.0.1", port), ChatHandler)
    print(f"[CHATBOT] 🚀 API server running on http://127.0.0.1:{port}")
    print(f"[CHATBOT]    POST /chat  {{\"message\": \"your question\"}}")
    print(f"[CHATBOT]    GET  /history")
    print(f"[CHATBOT]    GET  /reset")
    print(f"[CHATBOT]    Press Ctrl+C to stop\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[CHATBOT] Server stopped.")


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("╔══════════════════════════════════════════╗")
    print("║  IntelliTrace — AI Chatbot               ║")
    print("║  Cyber Dynamos · 2026                    ║")
    print("╚══════════════════════════════════════════╝\n")

    parser = argparse.ArgumentParser(description="IntelliTrace AI Chatbot")
    parser.add_argument("--api",   action="store_true", help="Run as HTTP API server")
    parser.add_argument("--query", type=str, default=None, help="Single query mode")
    parser.add_argument("--port",  type=int, default=8001, help="API port (default 8001)")
    parser.add_argument("--key",   type=str, default=None, help="OpenRouter API key")
    args = parser.parse_args()

    # Create bot
    bot = IntelliTraceBot(
        api_key  = args.key,
        csv_path = "transactions.csv"
    )

    if args.query:
        # Single query mode
        print(f"Query: {args.query}")
        print("─" * 50)
        resp, _ = bot.chat(args.query)
        print(resp)

    elif args.api:
        # API server mode
        run_api_server(bot, port=args.port)

    else:
        # Interactive terminal mode
        run_terminal(bot)