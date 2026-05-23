# Agentic Honeypot Core & Interactive Sandbox (v2.0.0)

An asynchronous, lightweight, high-interaction honeypot system designed to capture, engagement-track, and extract structured intelligence metrics from text-based social engineering threats in real-time. 

This repository provides an isolated local developer sandbox where you can interactively roleplay as a scammer to stress-test your AI victim persona and observe real-time intelligence data extraction without touching mobile hardware infrastructure.

---

## 🏗️ Architecture Overview

The system is built on a non-blocking asynchronous pipeline engineered to ensure low latency and high scalability across parallel turns.

- **FastAPI Core Application (`main.py`):** Acts as the central traffic manager. Features strict API security validation and real-time conversation turn tracking.
- **Dynamic Intent Detection Engine:** Forwards incoming messages to a Groq Cloud LLM instance to evaluate threat vectors. Once a threat is confirmed, the engine locks the session into active tracking state.
- **JSON-Mode Intelligence Extraction:** Leverages strongly typed LLM structures to isolate critical forensic indicators (UPI IDs, Phone Numbers, Phishing Links, and Bank Accounts) out of messy conversational text.
- **Time-Isolated File Logging System (`logger.py`):** Dumps transactional interactions concurrently into distinct, append-only JSON Lines (`.jsonl`) text streams. 
- **Interactive Sandbox Command Center (`sandbox.py`):** Runs an infinite terminal loop utilizing background worker threads to keep network connections stable while awaiting developer input.

---

## 📂 Project Structure
```
Honeypot-api/
├── main.py              # Async FastAPI router endpoints & core orchestrator
├── config.py            # Environment validation layer via pydantic-settings
├── models.py            # Strictly typed validation structures & message schemas
├── logger.py            # Timezone-aware asynchronous JSONL file logging utility
├── sandbox.py           # Multi-turn Interactive Terminal Command Center
├── test_script.py       # tests the model with a script
├── requirements.txt     # Locked production dependencies
├── .env                 # Private environment variables & credentials (git-ignored)
└── logs/                # Audit trails directory (git-ignored)
    ├── SYSTEM.jsonl                         # System health & upstream exception log
    └── interactive-sandbox-session-*.jsonl  # Isolated multi-turn conversation logs
```

---

## 🛠️ Installation & Setup
### 1. Clone & Enter Project Environment
```
git clone <your-github-repo-url>
cd Honeypot-api
```

### 2. Configure Virtual Environment & Packages
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Establish Runtime Configurations (`.env`)
```
API_SECRET_KEY="test-key-12345"
AI_BASE_URL="[https://api.groq.com/openai/v1](https://api.groq.com/openai/v1)"
AI_API_KEY="gsk_your_actual_groq_api_key"
AI_MODEL_NAME="llama-3.3-70b-specdec"
```

## 🚀 Running the Sandbox
### 1. Boot up the Core API Server
Open your primary terminal window and start the ASGI process container:
```
uvicorn main:app --reload
```
### Option A: Interactive Terminal Sandbox (Manual Explorer)
This pathway launches an interactive loop, allowing you to manually type or paste live scam sequences to test the flexibility and conversational limits of your persona.
- Open a secondary terminal window and initialize the live test panel:
```
python sandbox.py
```
### Option B: Scripted Test Simulation (Automated Regression)
This pathway executes a pre-programmed, multi-turn transaction script sequentially. It is designed for fast, reproducible regression testing to ensure code modifications do not break core integrations.
- Open a secondary terminal window and initialize the scripted test panel:
```
python test_script.py
```

### 3. Roleplay and Audit Logs
Type your threat configurations into the sandbox. To check the live intelligence extraction, inspect the freshly populated .jsonl audit streams under the logs/ directory.

## 🔒 Security & Performance Features
- **Pristine State Isolation:** Every single execution of ```sandbox.py``` anchors itself to a micro-marker ISO timestamp string. This guarantees that your server allocates a clean data frame in memory, completely eliminating cross-session state pollution.
- **Append-Only Performance:** Utilizing JSON Lines format allows the backend logging utility to run extremely lightweight $O(1)$ disk appends without loading heavy historic array models into RAM.
- **Linter Alignment:** Leverages explicit type casting (```typing.cast``` and literal declarations) to enforce 100% linter and type-checker compliance without sacrificing flexibility.