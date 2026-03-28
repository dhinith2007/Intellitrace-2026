🛡️ IntelliTrace 2026: Real-Time Cross-Channel Mule Detection

IntelliTrace is a Graph Intelligence platform designed to disrupt money mule networks by unifying siloed multi-channel banking logs into a structured entity graph. We use Graph Neural Networks (GNN) and real-time relational scoring to identify fraud patterns that traditional systems miss.

🚩 Problem Statement

Traditional fraud detection systems operate in silos. Money mules exploit this by rapidly moving funds across different channels (UPI, Web, ATM, Wallets).

•The Gap: Static rules only detect isolated anomalies.

•The Risk: Fraudulent trails are obscured within minutes, making recovery impossible once funds are withdrawn.

•The Complexity: High-velocity mule rings involve complex relationships between accounts, shared devices, and common IP addresses.

💡 Our Solution: The Graph Intelligence Approach

We resolve these challenges by moving from transaction-based monitoring to Relationship-based Intelligence:

1.Unified Entity Graph: Mapping transactions, devices, and IPs as interconnected nodes.

2.GNN-Based Strategy: Applying Node Classification and Relationship Strength Scoring to detect "Mule Rings."

3.Explainable Risk Scoring: Every flag comes with a confidence percentage and a "Reason Code" (e.g., "Shared Device with 3 flagged accounts").

⚙️ Prototype Workflow

Our building process follows a 5-stage pipeline:

1.Data Ingestion: Aggregating raw CSV logs into a cleaned, feature-rich format.

2.Streaming Simulation: Pushing data through a simulator to mimic real-time banking traffic.

3.Graph Orchestration: An API layer receives data and updates the NetworkX graph state.

4.Intelligence Layer: Running GNN algorithms to identify loops, fan-ins, and smurfing patterns.

5.Command Center: A real-time Dashboard and AI Bot for investigator action.

DATASET->TRANSACTION SIMULATOR->REST API ->GRAPH INTELLIGENCE ->FRONTEND/BACKEND DASHBOARD ->AIBOTS

👥 Team Responsibilities & Contributions

🔹 Dhinith Pragalyan | Lead Intelligence Architect
Dataset Engineering: Curating the "Mule-Enhanced" dataset with 22+ behavioral markers (Churn Rate, IP Density, Account Age).

Graph Intelligence: Implementing the NetworkX engine to detect circular loops and complex layering structures.

🔹 Elamaran B & Venkatesan S | Simulation & Learning Engineers
Transaction Simulator: Building the real-time data streamer to mimic multi-channel fund movement.

ML Integration: Implementing Supervised Learning (for known fraud signatures) and Unsupervised Learning (for anomaly detection in new mule clusters).

🔹 Dhanveer M | Backend & AI Integration
API Layer: Developing the FastAPI infrastructure to handle transaction ingestion and engine communication.

AI Investigative Bot: Building the LLM-powered assistant that translates complex graph data into human-readable fraud reports.

🔹 Full Team | Frontend & Dashboard Logic
Dashboard (Full-Stack): Creating the Streamlit interface, incorporating Pyvis for interactive graph visualization and real-time alert feeds.

🛠️ Tech Stack
•Backend: Python (FastAPI, Uvicorn)

•Intelligence: NetworkX, Pandas, Scikit-Learn

•Frontend: Streamlit, Pyvis (Graph Visualization)

•Data: Synthetic Multi-Channel Banking Logs

🚀 Installation & Execution
1.Setup Environment: pip install -r requirements.txt

2.Run API: uvicorn main:app --reload

3.Run Dashboard: streamlit run dashboard.py

4.Start Simulator: python simulator.py
