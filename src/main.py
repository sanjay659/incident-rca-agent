"""
Incident Root Cause Analyzer — Entry Point
============================================
Run: python -m src.main
"""
import json
from openai import AzureOpenAI
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from src.config import (
    validate_config, PROJECT_ENDPOINT, FOUNDRY_MODEL,
    AZURE_AI_SEARCH_ENDPOINT, AZURE_AI_SEARCH_KEY, KNOWLEDGE_BASE_INDEX,
)
from src.agents.log_analyzer import LogAnalyzerAgent
from src.agents.knowledge_retriever import KnowledgeRetrieverAgent
from src.agents.root_cause_reasoner import RootCauseReasonerAgent
from src.agents.action_recommender import ActionRecommenderAgent
from src.knowledge.foundry_iq_client import FoundryIQClient
from src.orchestrator.rca_pipeline import RCAPipeline


def get_resource_endpoint():
    return PROJECT_ENDPOINT.split("/api/projects")[0]


def setup():
    """Create all clients and agents. Returns pipeline + incident loader."""
    validate_config()

    project = AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=DefaultAzureCredential(),
    )
    openai_client = project.get_openai_client()

    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
    )
    embedding_client = AzureOpenAI(
        azure_endpoint=get_resource_endpoint(),
        azure_ad_token_provider=token_provider,
        api_version="2025-03-01-preview",
    )

    foundry_iq = FoundryIQClient(
        search_endpoint=AZURE_AI_SEARCH_ENDPOINT,
        search_key=AZURE_AI_SEARCH_KEY,
        index_name=KNOWLEDGE_BASE_INDEX,
        openai_client=embedding_client,
    )

    pipeline = RCAPipeline(
        log_analyzer=LogAnalyzerAgent(openai_client, FOUNDRY_MODEL),
        knowledge_retriever=KnowledgeRetrieverAgent(openai_client, FOUNDRY_MODEL, foundry_iq),
        root_cause_reasoner=RootCauseReasonerAgent(openai_client, FOUNDRY_MODEL),
        action_recommender=ActionRecommenderAgent(openai_client, FOUNDRY_MODEL),
    )

    return pipeline


def main():
    print("\n" + "=" * 60)
    print("  INCIDENT ROOT CAUSE ANALYZER")
    print("  4-Agent Reasoning Pipeline")
    print("=" * 60)

    pipeline = setup()
    print("  ✅ All connections ready\n")

    with open("data/sample_incidents/incident_001.json", "r") as f:
        incident = json.load(f)
    print(f"  📋 Incident: {incident['incident_id']} — {incident['title']}")

    report = pipeline.run(incident)

    # ── Final Summary ─────────────────────────────────────
    primary = report["root_cause"].get("primary_root_cause", {})
    print(f"\n{'='*60}")
    print(f"  FINAL RCA REPORT")
    print(f"{'='*60}")
    print(f"  Incident     : {incident['incident_id']}")
    print(f"  Root Cause   : {primary.get('cause', 'unknown')}")
    print(f"  Confidence   : {primary.get('confidence', 0):.0%}")
    print(f"  Category     : {primary.get('category', 'unknown')}")
    print(f"  Time taken   : {report['metadata']['time_seconds']}s")
    print(f"{'='*60}")

    output_path = "data/rca_report_001.json"
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  📄 Full report saved to: {output_path}")


if __name__ == "__main__":
    main()
