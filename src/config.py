"""
Configuration — loads .env and exposes settings to all modules.
Every file imports from here. No file reads .env directly.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Azure AI Foundry ─────────────────────────────────────
PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
FOUNDRY_MODEL = os.getenv("FOUNDRY_MODEL", "gpt-4.1-mini")

# ── Azure AI Search (Foundry IQ) ─────────────────────────
AZURE_AI_SEARCH_ENDPOINT = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
AZURE_AI_SEARCH_KEY = os.getenv("AZURE_AI_SEARCH_KEY", "")
KNOWLEDGE_BASE_INDEX = os.getenv("KNOWLEDGE_BASE_NAME", "incident-knowledge-base")

def validate_config():
    """Check all required settings are present. Call at startup."""
    missing = []
    if not PROJECT_ENDPOINT:
        missing.append("PROJECT_ENDPOINT")
    if not AZURE_AI_SEARCH_ENDPOINT:
        missing.append("AZURE_AI_SEARCH_ENDPOINT")
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"Copy .env.example to .env and fill in your values."
        )
    print(f"  Config loaded:")
    print(f"    Foundry : {PROJECT_ENDPOINT[:60]}...")
    print(f"    Model   : {FOUNDRY_MODEL}")
    print(f"    Search  : {AZURE_AI_SEARCH_ENDPOINT}")
    print(f"    Index   : {KNOWLEDGE_BASE_INDEX}")
