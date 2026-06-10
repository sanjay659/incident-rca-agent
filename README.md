# 🔍 Incident Root Cause Analyzer

**Multi-agent reasoning system that diagnoses production incidents through intelligent log analysis, knowledge retrieval, and root cause correlation.**

Built for the [Agents League Hackathon @ AISF 2026](https://github.com/microsoft/Agents-League-AISF-Regulations) — **Reasoning Agents Track**.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Azure AI Foundry](https://img.shields.io/badge/Azure%20AI%20Foundry-Agents-purple)
![Foundry IQ](https://img.shields.io/badge/Foundry%20IQ-Knowledge%20Base-green)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-red)

---

## 🎯 Problem

When production incidents occur, SRE and DevOps teams waste **30-60 minutes** manually:
- Reading through logs and alerts
- Searching runbooks and past incidents
- Correlating symptoms with known issues
- Identifying root cause and remediation steps

**80% of incidents have known patterns**, yet the diagnosis process is repeated from scratch every time.

## 💡 Solution

A **4-agent reasoning pipeline** built on **Microsoft Foundry + Foundry IQ** that performs automated root cause analysis through multi-step reasoning:

| Agent | Role | What It Does |
|-------|------|--------------|
| 🔎 **Log Analyzer** | Structured Analysis | Parses incident alerts, extracts errors, builds timeline, identifies failure patterns |
| 📚 **Knowledge Retriever** | Foundry IQ Search | Generates smart search queries, retrieves matching runbooks, past incidents, and known issues |
| 🧠 **Root Cause Reasoner** | Multi-step Reasoning | Correlates symptoms with historical patterns, forms hypotheses, diagnoses root cause with confidence |
| 🚨 **Action Recommender** | Remediation Plan | Generates prioritized actions with actual commands, escalation paths, and prevention recommendations |

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        Streamlit UI                              │
│              (Select incident → View reasoning chain)            │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                    RCA Pipeline Orchestrator                      │
│              (Chains agents, passes shared state)                │
└──────┬──────────┬──────────────┬─────────────┬───────────────────┘
       │          │              │             │
       ▼          ▼              ▼             ▼
  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
  │ Agent 1  │ │ Agent 2  │ │ Agent 3  │ │ Agent 4  │
  │   Log    │ │Knowledge │ │Root Cause│ │ Action   │
  │ Analyzer │ │Retriever │ │ Reasoner │ │Recommender│
  └─────────┘ └────┬─────┘ └──────────┘ └──────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │     Foundry IQ        │
        │  (Azure AI Search)    │
        │                       │
        │  📋 Runbooks          │
        │  📜 Past Incidents    │
        │  ⚠️ Known Issues      │
        │                       │
        │  Hybrid Search:       │
        │  Text + Vector        │
        └───────────────────────┘
```

### Microsoft IQ Integration: **Foundry IQ**

- **Knowledge Base**: 29 indexed documents (runbooks, past incidents, known issues) in Azure AI Search
- **Hybrid Search**: Text (BM25) + Vector (text-embedding-3-small) for best retrieval quality
- **Agentic Retrieval**: Agent 2 uses LLM to generate smart multi-angle search queries from incident analysis
- **Multi-hop Reasoning**: Agent 3 correlates retrieved knowledge with current symptoms across multiple reasoning steps

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Azure subscription with:
  - Azure AI Foundry project
  - `gpt-4.1-mini` model deployed
  - `text-embedding-3-small` model deployed
  - Azure AI Search resource

### Setup

```bash
# Clone
git clone https://github.com/sanjay659/incident-rca-agent.git
cd incident-rca-agent

# Virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Azure credentials
```

### Index Knowledge Base (Run Once)

```bash
python -m src.knowledge.index_knowledge
```

### Run CLI

```bash
python -m src.main
```

### Run Streamlit UI

```bash
streamlit run src/ui/app.py
```

## 📊 Demo Results

### Incident 1: Payment Service — 503 Errors (P1)

| Metric | Result |
|--------|--------|
| **Root Cause** | Regression in fraud-detection-service v2.4.1 causing resource exhaustion |
| **Confidence** | 90% |
| **Category** | deployment_regression |
| **Correlated Past Incident** | INC-2025-847 (same service, same pattern) |
| **Correlated Known Issue** | KI-002 (connection pool sizing) |
| **Immediate Action** | Rollback to previous version + scale pods |
| **Analysis Time** | ~130 seconds |

### Incident 2: Order Database — High Latency (P2)

| Metric | Result |
|--------|--------|
| **Root Cause** | Database resource exhaustion (DTU throttling + missing indexes) |
| **Confidence** | 85-90% |
| **Category** | resource_exhaustion / database_issue |
| **Correlated Past Incident** | INC-2025-623 (similar deadlock pattern) |
| **Immediate Action** | Kill long-running queries + scale database tier |
| **Analysis Time** | ~130 seconds |

## 🧠 Multi-Step Reasoning Example

Agent 3 follows a 5-step reasoning chain:

1. **Evidence Collection** — Lists all facts from log analysis
2. **Knowledge Correlation** — Matches symptoms against past incidents and runbooks
3. **Hypothesis Formation** — Forms 2-3 possible root causes
4. **Hypothesis Evaluation** — Scores each hypothesis against evidence (with supporting AND contradicting evidence)
5. **Conclusion** — States root cause with confidence score and explanation

This transparent reasoning chain is visible in both the CLI and the Streamlit UI.

## 🔧 Tech Stack

| Component | Technology |
|-----------|-----------|
| **LLM** | Azure AI Foundry — gpt-4.1-mini |
| **Embeddings** | Azure AI Foundry — text-embedding-3-small |
| **Knowledge Base** | Foundry IQ (Azure AI Search — hybrid vector + text) |
| **Agent Framework** | Microsoft Agent Framework (Python SDK) |
| **Orchestration** | Custom pipeline with shared state passing |
| **UI** | Streamlit |
| **Auth** | Azure Identity (DefaultAzureCredential) |

## 📁 Project Structure

```
incident-rca-agent/
├── src/
│   ├── config.py                    # Configuration (loads .env)
│   ├── main.py                      # CLI entry point
│   ├── agents/
│   │   ├── log_analyzer.py          # Agent 1: Log analysis
│   │   ├── knowledge_retriever.py   # Agent 2: Foundry IQ search
│   │   ├── root_cause_reasoner.py   # Agent 3: Root cause diagnosis
│   │   └── action_recommender.py    # Agent 4: Remediation plan
│   ├── orchestrator/
│   │   └── rca_pipeline.py          # 4-agent pipeline orchestrator
│   ├── knowledge/
│   │   ├── foundry_iq_client.py     # Azure AI Search hybrid search
│   │   └── index_knowledge.py       # One-time knowledge base indexer
│   └── ui/
│       └── app.py                   # Streamlit web UI
├── data/
│   ├── sample_incidents/            # Sample incident JSONs
│   └── knowledge_base/              # Runbooks, past incidents, known issues
├── .env.example
├── requirements.txt
└── README.md
```

## 📝 Judging Criteria Alignment

| Criteria | How This Project Addresses It |
|----------|------------------------------|
| **Accuracy & Relevance (20%)** | Grounded in Foundry IQ knowledge base — no hallucination, citations from real runbooks |
| **Reasoning & Multi-step (20%)** | 5-step reasoning chain with hypothesis formation and evaluation |
| **Creativity & Originality (15%)** | Domain-specific multi-agent for incident RCA — not a generic chatbot |
| **User Experience (15%)** | Streamlit UI with progress tracking, expandable reasoning steps, downloadable reports |
| **Reliability & Safety (20%)** | Confidence scores, supporting/contradicting evidence, human-readable reasoning chain |

## 👤 Author

**Sanjay Thakur** — Cloud & AI Solution Architect
- GitHub: [sanjay659](https://github.com/sanjay659)

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.
