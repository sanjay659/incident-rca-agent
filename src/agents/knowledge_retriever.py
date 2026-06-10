"""
Agent 2: Knowledge Retriever
=============================
INPUT:  Structured analysis from Agent 1 (errors, patterns, services)
OUTPUT: Relevant knowledge — runbooks, past incidents, known issues

This agent is the BRIDGE between "what happened" (Agent 1) and
"what do we know about this" (knowledge base).

It does TWO things:
1. Builds smart search queries from Agent 1's analysis
2. Searches Foundry IQ (Azure AI Search) for matching knowledge

Foundry IQ integration with multi-step reasoning.
"""
import json


class KnowledgeRetrieverAgent:
    """
    Agent 2 in the RCA pipeline.
    
    Takes Agent 1's structured analysis → builds search queries →
    searches Foundry IQ → returns relevant knowledge for Agent 3.
    """

    def __init__(self, openai_client, model: str, foundry_iq_client):
        """
        Args:
            openai_client: OpenAI client for LLM calls
            model: Deployment name (e.g., 'gpt-4.1-mini')
            foundry_iq_client: FoundryIQClient for searching knowledge base
        """
        self.client = openai_client
        self.model = model
        self.knowledge = foundry_iq_client
        self.name = "Knowledge Retriever"

    def _generate_search_queries(self, analysis: dict) -> list[str]:
        """
        Use LLM to generate smart search queries from Agent 1's analysis.
        
        Why not just search the raw error messages?
        Because the LLM can REASON about what to look for:
        - "circuit breaker + deployment" → search for deployment rollback runbooks
        - "connection pool exhausted" → search for connection pool issues
        - "fraud-detection-service" → search for past incidents with this service
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You generate search queries for an incident knowledge base. "
                        "The knowledge base contains: runbooks, past incident reports, and known issues.\n\n"
                        "Given an incident analysis, generate 3-5 targeted search queries that would find:\n"
                        "1. Runbooks matching the failure pattern\n"
                        "2. Past incidents with similar symptoms\n"
                        "3. Known issues for the affected services\n\n"
                        "Respond with a JSON array of strings. Example:\n"
                        '["circuit breaker failure after deployment", "payment service timeout runbook"]'
                    ),
                },
                {
                    "role": "user",
                    "content": f"Generate search queries for this incident analysis:\n\n{json.dumps(analysis, indent=2)}",
                },
            ],
            temperature=0.3,
        )

        raw = response.choices[0].message.content.strip()
        # Clean markdown wrapping if present
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]

        try:
            queries = json.loads(raw.strip())
            return queries if isinstance(queries, list) else [str(queries)]
        except json.JSONDecodeError:
            # Fallback: build queries manually from analysis
            return self._fallback_queries(analysis)

    def _fallback_queries(self, analysis: dict) -> list[str]:
        """If LLM query generation fails, build queries from analysis fields."""
        queries = []
        pattern = analysis.get("failure_pattern", "")
        if pattern:
            queries.append(f"{pattern} runbook")

        for service in analysis.get("affected_services", []):
            name = service.get("name", "")
            if name:
                queries.append(f"{name} incident")

        for error in analysis.get("error_summary", [])[:2]:
            msg = error.get("message", "")
            if msg:
                queries.append(msg[:100])

        return queries if queries else ["incident troubleshooting"]

    def run(self, analysis: dict) -> dict:
        """
        Search knowledge base for information relevant to this incident.
        
        Args:
            analysis: Output from Agent 1 (LogAnalyzerAgent)
            
        Returns:
            dict with search_queries, runbooks, past_incidents, known_issues
        """
        print(f"\n{'='*60}")
        print(f"  Agent 2: {self.name}")
        print(f"  Searching knowledge base for matching patterns...")
        print(f"{'='*60}")

        # ── Step 1: Generate search queries using LLM ─────
        print("\n  Generating search queries from analysis...")
        queries = self._generate_search_queries(analysis)
        for i, q in enumerate(queries):
            print(f"    Query {i+1}: {q}")

        # ── Step 2: Search Foundry IQ ─────────────────────
        print(f"\n  Searching knowledge base ({self.knowledge.index_name})...")
        all_results = self.knowledge.search_multiple(queries, top_per_query=3)
        print(f"  Found {len(all_results)} relevant documents")

        # ── Step 3: Categorize results ────────────────────
        runbooks = [r for r in all_results if r["doc_type"] == "runbook"]
        past_incidents = [r for r in all_results if r["doc_type"] == "past_incident"]
        known_issues = [r for r in all_results if r["doc_type"] == "known_issues"]

        print(f"\n  📋 Runbooks found        : {len(runbooks)}")
        print(f"  📜 Past incidents found  : {len(past_incidents)}")
        print(f"  ⚠️  Known issues found   : {len(known_issues)}")

        result = {
            "search_queries": queries,
            "total_results": len(all_results),
            "runbooks": runbooks,
            "past_incidents": past_incidents,
            "known_issues": known_issues,
        }

        print(f"\n  ✅ Knowledge retrieval complete")
        return result
