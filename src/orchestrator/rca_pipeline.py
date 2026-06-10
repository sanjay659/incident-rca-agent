"""
RCA Pipeline Orchestrator
==========================
Chains all 4 agents in sequence, passing state between them.

This is the "conductor" — it doesn't do analysis itself,
it coordinates who runs when and what data flows where.

Flow:
  incident JSON
      → Agent 1 (Log Analyzer)      → analysis
      → Agent 2 (Knowledge Retriever) → knowledge
      → Agent 3 (Root Cause Reasoner)  → root_cause
      → Agent 4 (Action Recommender)   → actions
      → Final RCA Report
"""
import time
import json


class RCAPipeline:
    """
    Orchestrates the 4-agent RCA pipeline.
    
    Usage:
        pipeline = RCAPipeline(agent1, agent2, agent3, agent4)
        report = pipeline.run(incident_data)
    """

    def __init__(self, log_analyzer, knowledge_retriever, root_cause_reasoner, action_recommender):
        self.agent1 = log_analyzer
        self.agent2 = knowledge_retriever
        self.agent3 = root_cause_reasoner
        self.agent4 = action_recommender

    def run(self, incident: dict, on_step=None) -> dict:
        """
        Run the full RCA pipeline.

        Args:
            incident: Raw incident JSON
            on_step: Optional callback function called after each agent.
                     Signature: on_step(agent_name, step_number, result)
                     Used by Streamlit UI to show progress.

        Returns:
            Complete RCA report dict
        """
        start_time = time.time()

        # ── Agent 1: Log Analyzer ─────────────────────────
        analysis = self.agent1.run(incident)
        if on_step:
            on_step("Log Analyzer", 1, analysis)

        # ── Agent 2: Knowledge Retriever ──────────────────
        knowledge = self.agent2.run(analysis)
        if on_step:
            on_step("Knowledge Retriever", 2, knowledge)

        # ── Agent 3: Root Cause Reasoner ──────────────────
        root_cause = self.agent3.run(analysis, knowledge)
        if on_step:
            on_step("Root Cause Reasoner", 3, root_cause)

        # ── Agent 4: Action Recommender ───────────────────
        actions = self.agent4.run(analysis, knowledge, root_cause)
        if on_step:
            on_step("Action Recommender", 4, actions)

        elapsed = time.time() - start_time

        # ── Build final report ────────────────────────────
        report = {
            "incident": incident,
            "analysis": analysis,
            "knowledge_summary": {
                "queries": knowledge.get("search_queries", []),
                "runbooks_found": len(knowledge.get("runbooks", [])),
                "past_incidents_found": len(knowledge.get("past_incidents", [])),
                "known_issues_found": len(knowledge.get("known_issues", [])),
            },
            "root_cause": root_cause,
            "actions": actions,
            "metadata": {
                "model": self.agent1.model,
                "time_seconds": round(elapsed, 1),
                "agents": ["Log Analyzer", "Knowledge Retriever", "Root Cause Reasoner", "Action Recommender"],
            },
        }

        return report
