"""
Agent 1: Log Analyzer
=====================
INPUT:  Raw incident alert JSON (from PagerDuty/Datadog/etc.)
OUTPUT: Structured analysis dict with errors, timeline, severity

HOW IT CALLS THE LLM:
  main.py creates AIProjectClient (HTTP connection to Foundry)
  main.py calls project.get_openai_client() → returns OpenAI client
  This agent receives that OpenAI client
  Calls client.chat.completions.create() → same API you already know
  Foundry routes to your gpt-4.1-mini deployment
"""
import json

# ── System Prompt ─────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert Site Reliability Engineer (SRE) specializing in production incident log analysis.

Given a production incident alert with logs and infrastructure data, perform these steps:

1. ERROR EXTRACTION: List every error/warning from the logs with timestamp and severity
2. TIMELINE RECONSTRUCTION: Build a chronological timeline of what happened
3. SERVICE IMPACT: Identify all affected services and their dependencies
4. PATTERN RECOGNITION: Identify if errors suggest a specific failure pattern
   (e.g., cascade failure, resource exhaustion, deployment issue, network partition)
5. SEVERITY ASSESSMENT: Based on blast radius and business impact, confirm or adjust severity

You MUST respond with a valid JSON object using this exact structure:
{
    "error_summary": [
        {"timestamp": "...", "level": "ERROR|WARN|CRITICAL", "message": "...", "service": "..."}
    ],
    "timeline": [
        {"timestamp": "...", "event": "...", "significance": "..."}
    ],
    "affected_services": [
        {"name": "...", "role": "primary|downstream|upstream", "status": "..."}
    ],
    "failure_pattern": "cascade_failure|resource_exhaustion|deployment_regression|network_issue|database_issue|unknown",
    "blast_radius": "description of what is impacted and who is affected",
    "severity_assessment": {
        "current": "P1|P2|P3",
        "recommended": "P1|P2|P3",
        "justification": "..."
    },
    "key_observations": ["observation 1", "observation 2"]
}

Be precise and technical. Base analysis ONLY on provided data. Do not speculate beyond what logs show."""


class LogAnalyzerAgent:
    """
    Agent 1 in the RCA pipeline.
    
    Takes raw incident JSON → calls LLM via OpenAI client → returns structured analysis.
    The structured output becomes input for Agent 2 (Knowledge Retriever).
    """

    def __init__(self, openai_client, model: str):
        """
        Args:
            openai_client: OpenAI client from project.get_openai_client()
            model: Deployment name (e.g., 'gpt-4.1-mini')
        """
        self.client = openai_client
        self.model = model
        self.name = "Log Analyzer"

    def run(self, incident_data: dict) -> dict:
        """
        Analyze an incident alert and extract structured information.
        
        Args:
            incident_data: Raw incident JSON (from sample_incidents/)
            
        Returns:
            dict with error_summary, timeline, affected_services, etc.
        """
        print(f"\n{'='*60}")
        print(f"  Agent 1: {self.name}")
        print(f"  Analyzing incident: {incident_data.get('incident_id', 'unknown')}")
        print(f"{'='*60}")

        # ── Call LLM via OpenAI client ────────────────────────
        # project.get_openai_client() gives us a standard OpenAI client
        # so this is the SAME API as your previous projects:
        #   client.chat.completions.create()
        # 
        # Under the hood:
        #   OpenAI client → HTTPS POST → Foundry endpoint → gpt-4.1-mini → response
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Analyze this production incident alert. "
                        "Extract all errors, build timeline, identify patterns.\n\n"
                        f"{json.dumps(incident_data, indent=2)}"
                    ),
                },
            ],
            temperature=0.1,  # Low temperature = more deterministic/precise
        )

        # ── Parse response ────────────────────────────────────
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
            print(f"  ✅ Analysis complete — found {len(result.get('error_summary', []))} errors, "
                  f"pattern: {result.get('failure_pattern', 'unknown')}")
            return result

        except json.JSONDecodeError:
            print(f"  ⚠️  Model returned non-JSON response, wrapping as raw text")
            return {"raw_analysis": raw_content, "parse_error": True}
