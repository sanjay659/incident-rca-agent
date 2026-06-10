"""
Agent 3: Root Cause Reasoner
==============================
INPUT:  Agent 1 analysis + Agent 2 knowledge
OUTPUT: Root cause diagnosis with confidence and reasoning chain

This is the CORE reasoning agent. It does what a senior SRE does:
  - Correlates current symptoms with past incidents
  - Matches failure patterns to known causes
  - Follows runbook diagnosis steps mentally
  - Produces a root cause with confidence score + reasoning chain

The reasoning chain is KEY for the hackathon demo — it shows HOW
the agent thinks, not just WHAT it concludes.
"""
import json

SYSTEM_PROMPT = """You are a senior Site Reliability Engineer performing root cause analysis.

You have THREE inputs:
1. INCIDENT ANALYSIS — structured analysis of the current incident (errors, timeline, patterns)
2. KNOWLEDGE — relevant runbooks, past incidents, and known issues from the knowledge base
3. Your task — correlate all evidence to identify the most likely root cause

Your reasoning process:
1. EVIDENCE COLLECTION: List all facts from the incident analysis
2. KNOWLEDGE CORRELATION: Match current symptoms against past incidents and known issues
3. HYPOTHESIS FORMATION: Form 1-3 possible root causes
4. HYPOTHESIS EVALUATION: Score each hypothesis against the evidence
5. CONCLUSION: State the most likely root cause with confidence

You MUST respond with a valid JSON object:
{
    "reasoning_chain": [
        {"step": 1, "action": "Evidence Collection", "details": "..."},
        {"step": 2, "action": "Knowledge Correlation", "details": "..."},
        {"step": 3, "action": "Hypothesis Formation", "details": "..."},
        {"step": 4, "action": "Hypothesis Evaluation", "details": "..."},
        {"step": 5, "action": "Conclusion", "details": "..."}
    ],
    "hypotheses": [
        {
            "cause": "description of potential root cause",
            "confidence": 0.0 to 1.0,
            "supporting_evidence": ["evidence 1", "evidence 2"],
            "contradicting_evidence": ["if any"]
        }
    ],
    "primary_root_cause": {
        "cause": "the most likely root cause",
        "confidence": 0.0 to 1.0,
        "category": "deployment_regression|resource_exhaustion|configuration_error|infrastructure_failure|database_issue|network_issue|unknown",
        "affected_component": "the specific service or component that caused the issue",
        "explanation": "detailed explanation of how this cause led to the observed symptoms"
    },
    "correlated_past_incidents": ["INC-xxx if any matching past incidents were found"],
    "correlated_known_issues": ["KI-xxx if any matching known issues were found"]
}

Be rigorous. Show your reasoning. Confidence should reflect actual evidence strength."""


class RootCauseReasonerAgent:
    """
    Agent 3 in the RCA pipeline.

    Takes Agent 1 analysis + Agent 2 knowledge → reasons about root cause.
    The reasoning_chain in the output is what makes this agent special
    for the hackathon — it shows multi-step thinking, not just an answer.
    """

    def __init__(self, openai_client, model: str):
        self.client = openai_client
        self.model = model
        self.name = "Root Cause Reasoner"

    def _prepare_knowledge_context(self, knowledge: dict) -> str:
        """
        Format Agent 2's knowledge results into a readable context block.
        This becomes part of the prompt so the LLM can reference it.
        """
        context_parts = []

        if knowledge.get("runbooks"):
            context_parts.append("=== RELEVANT RUNBOOKS ===")
            for doc in knowledge["runbooks"][:5]:
                context_parts.append(f"\n[Source: {doc['source_file']}]\n{doc['content']}\n")

        if knowledge.get("past_incidents"):
            context_parts.append("=== PAST INCIDENTS ===")
            for doc in knowledge["past_incidents"][:5]:
                context_parts.append(f"\n[Source: {doc['source_file']}]\n{doc['content']}\n")

        if knowledge.get("known_issues"):
            context_parts.append("=== KNOWN ISSUES ===")
            for doc in knowledge["known_issues"][:3]:
                context_parts.append(f"\n[Source: {doc['source_file']}]\n{doc['content']}\n")

        return "\n".join(context_parts) if context_parts else "No relevant knowledge found."

    def run(self, analysis: dict, knowledge: dict) -> dict:
        """
        Reason about root cause using analysis + knowledge.

        Args:
            analysis: Output from Agent 1 (LogAnalyzerAgent)
            knowledge: Output from Agent 2 (KnowledgeRetrieverAgent)

        Returns:
            dict with reasoning_chain, hypotheses, primary_root_cause
        """
        print(f"\n{'='*60}")
        print(f"  Agent 3: {self.name}")
        print(f"  Correlating evidence with knowledge base...")
        print(f"{'='*60}")

        knowledge_context = self._prepare_knowledge_context(knowledge)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Perform root cause analysis using the following inputs:\n\n"
                        "=== INCIDENT ANALYSIS (from log analysis) ===\n"
                        f"{json.dumps(analysis, indent=2)}\n\n"
                        "=== KNOWLEDGE BASE RESULTS ===\n"
                        f"{knowledge_context}\n\n"
                        "Correlate the evidence, form hypotheses, and identify the root cause."
                    ),
                },
            ],
            temperature=0.2,
        )

        raw_content = response.choices[0].message.content
        try:
            clean = raw_content.strip()
            if clean.startswith("```json"):
                clean = clean[7:]
            if clean.startswith("```"):
                clean = clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]

            result = json.loads(clean.strip())

            primary = result.get("primary_root_cause", {})
            print(f"\n  🔍 Root Cause: {primary.get('cause', 'unknown')[:80]}")
            print(f"  📊 Confidence: {primary.get('confidence', 0):.0%}")
            print(f"  📁 Category : {primary.get('category', 'unknown')}")
            print(f"  🔗 Reasoning steps: {len(result.get('reasoning_chain', []))}")
            print(f"\n  ✅ Root cause analysis complete")
            return result

        except json.JSONDecodeError:
            print(f"  ⚠️  Model returned non-JSON response")
            return {"raw_analysis": raw_content, "parse_error": True}
