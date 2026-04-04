# 🔐 Real-Time Cross-Channel Mule Account Detection Using Graph Intelligence

### 🚀 Built by **Cyber Dynamos**

---

## 📌 Problem Statement

Money mule networks exploit **multi-channel banking systems** by rapidly transferring funds across:

* 📱 Mobile Applications
* 🌐 Web Platforms
* 💳 Digital Wallets
* 🏧 ATM Networks

These networks are designed to **obscure fraudulent trails** through high-speed, multi-hop transactions across different platforms.

### ❌ Limitations of Traditional Systems:

* Rule-based detection (static & outdated)
* Siloed data across channels
* No relationship-level visibility
* Poor detection of coordinated fraud networks

👉 As a result, **organized mule rings remain undetected** until major financial damage occurs.

---

## 💡 Proposed Solution

We propose a **Real-Time Graph Intelligence Platform** that:

* Unifies multi-channel transaction logs
* Builds a structured **entity relationship graph**
* Applies **Machine Learning + Graph Intelligence**
* (Future Scope) Integrates **Graph Neural Networks (GNNs)**

### 🎯 Key Capabilities:

* Detect high-velocity mule account networks
* Generate **explainable risk scores**
* Enable **real-time fraud monitoring**
* Support **compliance and reporting**

👉 Our system transforms fraud detection from **transaction-level → network-level intelligence**

---

## 🧩 System Architecture

```id="arch1"
Transaction Simulator → Detection Engine → Graph Intelligence → API Layer → Dashboard + AI Assistant
```

---

## ⚙️ System Modules

### 🔹 1. Transaction Simulator (Multi-Channel Data Generator)

Simulates real-world financial activity across multiple channels.

**Includes:**

* Account-to-account transfers
* Cross-platform transactions (mobile, web, ATM, wallet)
* Time-based transaction flows

**Fraud Patterns Injected:**

* 🔁 Multi-hop mule chains
* ⏱️ Rapid fund transfers
* 🔄 Circular transactions (laundering loops)
* 🌐 One-to-many distribution patterns

👉 Provides a **realistic dataset** for testing fraud detection.

---

### 🔹 2. Detection Engine (Machine Learning Layer)

Applies both **Supervised and Unsupervised Learning**:

#### ✅ Supervised Learning

* Classifies transactions as fraud / non-fraud
* Learns from labeled patterns

#### ✅ Unsupervised Learning

* Detects anomalies without prior labels
* Identifies unusual transaction behaviors

**Outputs:**

* Risk Score
* Fraud Classification

👉 Forms the **initial screening layer** of the system.

---

### 🔹 3. Graph Intelligence Layer (Core Innovation)

This is the **heart of the system**.

**Technologies:**

* NetworkX
* PyVis

**How it Works:**

* Converts transactions into a graph:

  * Nodes → Accounts / Devices / Channels
  * Edges → Transactions

**Detects:**

* 🔁 Multi-hop mule chains
* 🌐 Fraud clusters (rings)
* 📍 High-risk central nodes
* ⏱️ Rapid transaction paths

👉 Enables **network-level fraud detection**, not just individual analysis.

---

### 🔹 4. API Layer

Acts as a communication bridge between backend and frontend.

**Built Using:**

* Flask / FastAPI

**Handles:**

* ML predictions
* Graph data serving
* Chatbot queries
* Dataset uploads

---

### 🔹 5. Interactive Dashboard

Provides a real-time view of system insights.

**Features:**

* 📂 Upload transaction datasets
* 📊 View fraud detection results
* 🌐 Interactive graph visualization
* 🚨 Highlight suspicious accounts
* 📈 Risk scoring dashboard

👉 Designed for **analysts and investigators**

---

### 🔹 6. AI Chatbot (Explainable Intelligence Layer)

An AI-powered assistant integrated into the dashboard.

**Capabilities:**

* Explains fraud detection results
* Answers queries like:

  * “Why is this account suspicious?”
  * “Show mule network pattern”
  * “Which node has highest risk?”
* Provides **natural language insights**

**Technology:**

* LLM (OpenAI API)

👉 Adds **explainability + usability** to the system.

---

## 🛠️ Tech Stack

| Layer            | Technology            |
| ---------------- | --------------------- |
| Backend          | Python                |
| API              | Flask / FastAPI       |
| Machine Learning | Scikit-learn          |
| Graph Analysis   | NetworkX              |
| Visualization    | PyVis                 |
| Frontend         | HTML, CSS, JavaScript |
| AI Assistant     | OpenAI API            |
| Deployment       | Render                |

---

## 📊 Fraud Patterns Detected

* 🔁 Multi-hop mule account chains
* 🌐 Distributed fund splitting
* ⏱️ High-velocity transactions
* 🔄 Circular laundering loops
* 📍 Cross-channel anomalies

---

## 📁 Project Structure

```id="struct1"
├── dashboard.py
├── ai_chatbot.py
├── transaction_simulator.py
├── detection_engine.py
├── graph_module.py
├── api_layer.py
├── templates/
├── static/
└── dataset/
```

---

## 🚀 How to Run

```bash id="run1"
# Clone repository
git clone https://github.com/dhinith2007/Intellitrace-2026

# Navigate to project
cd your-repo-name

# Install dependencies
pip install -r requirements.txt

# Run application
python dashboard.py
```

---

## 🤖 Example AI Queries

* "Which account is part of a mule network?"
* "Explain this fraud pattern"
* "Show high-risk transaction chain"

---

## 🎯 Use Cases

* Banking Fraud Detection
* Anti-Money Laundering (AML)
* Financial Intelligence Systems
* Cybersecurity Monitoring

---

## 👨‍💻 Team – Cyber Dynamos

* **Dhinith Pragalyan M** – Backend Integration, Graph Intelligence, UI Dashboard
* **Dhanveer M** – API Layer, AI Chatbot Integration
* **Elamaran B** – Transaction Simulator, Detection Engine
* **Venkatesan** – Transaction Simulator, Detection Engine

---

## 🚀 Future Enhancements

* Graph Neural Networks (GNN) for deep pattern learning
* Real-time streaming fraud detection
* Cross-bank data integration
* Advanced explainable AI (XAI)

---

## ⭐ Conclusion

This project demonstrates how **Graph Intelligence + Machine Learning + AI Assistants** can revolutionize fraud detection by shifting from:

👉 **Isolated Transactions → Connected Intelligence**
 
 Live Deployed Prototype->https://intellitrace-2026.onrender.com/
---

⭐ If you like this project, give it a star!
