# Architecture — Incident Root Cause Analyzer

## System Architecture

```
                    ┌─────────────────────────┐
                    │      Streamlit UI        │
                    │   (User selects incident │
                    │    views reasoning chain) │
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │   RCA Pipeline           │
                    │   Orchestrator            │
                    │   (rca_pipeline.py)       │
                    └───┬───┬───┬───┬─────────┘
                        │   │   │   │
          ┌─────────────┘   │   │   └──────────────┐
          ▼                 ▼   ▼                   ▼
    ┌───────────┐   ┌───────────┐  ┌───────────┐  ┌───────────┐
    │  Agent 1  │   │  Agent 2  │  │  Agent 3  │  │  Agent 4  │
    │    Log    │──▶│ Knowledge │─▶│Root Cause │─▶│  Action   │
    │ Analyzer  │   │ Retriever │  │ Reasoner  │  │Recommender│
    └───────────┘   └─────┬─────┘  └───────────┘  └───────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │     Foundry IQ        │
              │  (Azure AI Search)    │
              │                       │
              │  ┌─────────────────┐  │
              │  │ 📋 Runbooks     │  │
              │  │ 📜 Past RCAs    │  │
              │  │ ⚠️ Known Issues │  │
              │  └─────────────────┘  │
              │                       │
              │  Hybrid Search:       │
              │  Text + Vector        │
              └───────────────────────┘
```

## Data Flow

```
Incident JSON → Agent 1 (analyze) → Structured Analysis
                                          │
                                          ▼
                                    Agent 2 (search)
                                    ├─ LLM generates queries
                                    ├─ Foundry IQ hybrid search
                                    └─ Returns: runbooks + past incidents
                                          │
                                          ▼
                                    Agent 3 (reason)
                                    ├─ Evidence collection
                                    ├─ Knowledge correlation
                                    ├─ Hypothesis formation
                                    ├─ Hypothesis evaluation
                                    └─ Root cause + confidence
                                          │
                                          ▼
                                    Agent 4 (recommend)
                                    ├─ Immediate actions + commands
                                    ├─ Escalation plan
                                    ├─ Blast radius assessment
                                    └─ Prevention recommendations
```

## Shared State Pattern

All 4 agents share a state dictionary that grows as it passes through each agent:

```python
# After Agent 1:
state = {
    "incident": {...raw alert...},
    "analysis": {errors, timeline, severity, affected_services}
}

# After Agent 2:
state = {
    ...,
    "knowledge": {matching_runbooks, past_incidents, known_fixes}
}

# After Agent 3:
state = {
    ...,
    "root_cause": {cause, confidence, reasoning_chain, hypotheses}
}

# After Agent 4 (final):
state = {
    ...,
    "actions": {remediation_steps, escalation, blast_radius, prevention}
}
```

## Azure Resources

| Resource | Service | Purpose |
|----------|---------|---------|
| Azure AI Foundry | gpt-4.1-mini | LLM for all 4 agents (analysis, query generation, reasoning, recommendations) |
| Azure AI Foundry | text-embedding-3-small | Vector embeddings for knowledge base indexing and search queries |
| Azure AI Search | incident-knowledge-base index | Hybrid search (BM25 + vector) over runbooks, past incidents, known issues |

## Microsoft IQ Integration

**Foundry IQ** is used as the knowledge retrieval layer:

1. **Indexing** (run once): `index_knowledge.py` reads markdown files from `data/knowledge_base/`, chunks them by section, generates embeddings via `text-embedding-3-small`, and uploads to Azure AI Search index.

2. **Retrieval** (every query): Agent 2 uses LLM to generate 3-6 targeted search queries from Agent 1's analysis. Each query is executed as a hybrid search (text + vector) against the index. Results are deduplicated and ranked by relevance.

3. **Reasoning** (every query): Agent 3 receives the retrieved knowledge and correlates it with the current incident analysis through a 5-step reasoning chain, producing a root cause diagnosis with confidence scores.

## Model Usage

| Agent | Model | Temperature | Purpose |
|-------|-------|-------------|---------|
| Agent 1 (Log Analyzer) | gpt-4.1-mini | 0.1 | Precise log analysis, deterministic output |
| Agent 2 (Query Generator) | gpt-4.1-mini | 0.3 | Creative query generation, slight variation OK |
| Agent 2 (Search) | text-embedding-3-small | N/A | Vector embeddings for hybrid search |
| Agent 3 (Root Cause) | gpt-4.1-mini | 0.2 | Rigorous reasoning, low creativity |
| Agent 4 (Actions) | gpt-4.1-mini | 0.2 | Specific recommendations, low creativity |

## Cost Efficiency

- All LLM calls use `gpt-4.1-mini` (cost-efficient)
- Embeddings use `text-embedding-3-small` (cheapest option)
- Azure AI Search on Free tier (50 MB, 3 indexes)
- Total cost per analysis: ~$0.01-0.02
