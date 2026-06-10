"""
Agent 4: Action Recommender
=============================
INPUT:  All previous agents' outputs (analysis + knowledge + root cause)
OUTPUT: Prioritized remediation steps, escalation path, blast radius

This is the "so what do we DO about it?" agent.
It turns diagnosis into action — what a senior SRE would tell the team.
"""
import json

SYSTEM_PROMPT = """You are a senior SRE creating an actionable incident response plan.

You have the full incident context:
- Incident analysis (errors, timeline, affected services)
- Knowledge base results (runbooks, past incidents, known issues)
- Root cause analysis (diagnosed cause with confidence)

Create a response plan that an on-call engineer can follow RIGHT NOW.

You MUST respond with a valid JSON object:
{
    "immediate_actions": [
        {
            "priority": 1,
            "action": "what to do",
            "command": "specific command if applicable (kubectl, az cli, SQL, etc.)",
            "expected_outcome": "what should happen after this action",
            "risk_level": "low|medium|high"
        }
    ],
    "escalation": {
        "required": true or false,
        "teams": ["team names to engage"],
        "timeline": "when to escalate if not resolved",
        "communication": "suggested status update message for stakeholders"
    },
    "blast_radius": {
        "affected_users": "description of who is impacted",
        "affected_services": ["list of services"],
        "business_impact": "revenue, reputation, compliance implications",
        "estimated_duration": "how long until resolution based on past incidents"
    },
    "prevention": [
        {
            "recommendation": "what to do to prevent recurrence",
            "priority": "immediate|short_term|long_term",
            "effort": "low|medium|high"
        }
    ],
    "confidence_note": "any caveats about the recommendations"
}

Be specific. Include actual commands where possible. Prioritize by impact."""


class ActionRecommenderAgent:
    """
    Agent 4 (final) in the RCA pipeline.

    Takes all previous outputs → produces actionable remediation plan.
    This is what gets shown to the on-call engineer.
    """

    def __init__(self, openai_client, model: str):
        self.client = openai_client
        self.model = model
        self.name = "Action Recommender"

    def run(self, analysis: dict, knowledge: dict, root_cause: dict) -> dict:
        """
        Generate action plan from all previous agent outputs.

        Args:
            analysis: Output from Agent 1
            knowledge: Output from Agent 2
            root_cause: Output from Agent 3

        Returns:
            dict with immediate_actions, escalation, blast_radius, prevention
        """
        print(f"\n{'='*60}")
        print(f"  Agent 4: {self.name}")
        print(f"  Generating remediation plan...")
        print(f"{'='*60}")

        # Build a concise context from all agents
        context = {
            "incident_analysis": {
                "failure_pattern": analysis.get("failure_pattern"),
                "affected_services": analysis.get("affected_services"),
                "severity": analysis.get("severity_assessment"),
                "key_observations": analysis.get("key_observations"),
            },
            "knowledge_summary": {
                "runbooks_found": len(knowledge.get("runbooks", [])),
                "past_incidents_found": len(knowledge.get("past_incidents", [])),
                "known_issues_found": len(knowledge.get("known_issues", [])),
                "top_runbook": knowledge["runbooks"][0]["content"][:500] if knowledge.get("runbooks") else "none",
                "top_past_incident": knowledge["past_incidents"][0]["content"][:500] if knowledge.get("past_incidents") else "none",
            },
            "root_cause": root_cause.get("primary_root_cause"),
            "hypotheses": root_cause.get("hypotheses"),
            "correlated_past_incidents": root_cause.get("correlated_past_incidents"),
        }

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Create an actionable incident response plan based on:\n\n"
                        f"{json.dumps(context, indent=2)}"
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

            actions = result.get("immediate_actions", [])
            print(f"\n  🚨 Immediate actions: {len(actions)}")
            for a in actions[:3]:
                print(f"    P{a.get('priority', '?')}: {a.get('action', 'N/A')[:70]}")

            esc = result.get("escalation", {})
            print(f"  📞 Escalation required: {esc.get('required', 'unknown')}")

            prevention = result.get("prevention", [])
            print(f"  🛡️  Prevention items: {len(prevention)}")

            print(f"\n  ✅ Action plan complete")
            return result

        except json.JSONDecodeError:
            print(f"  ⚠️  Model returned non-JSON response")
            return {"raw_analysis": raw_content, "parse_error": True}
