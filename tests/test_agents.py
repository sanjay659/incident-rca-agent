"""Basic smoke tests for the RCA pipeline."""
import json
import os


def test_sample_incidents_valid():
    """Verify sample incident files are valid JSON."""
    for f in os.listdir("data/sample_incidents"):
        if f.endswith(".json"):
            with open(f"data/sample_incidents/{f}") as fh:
                data = json.load(fh)
                assert "incident_id" in data
                assert "logs" in data


def test_knowledge_base_exists():
    """Verify knowledge base files exist."""
    kb_files = os.listdir("data/knowledge_base")
    assert len(kb_files) >= 5
    assert any("runbook" in f for f in kb_files)
    assert any("past_incident" in f for f in kb_files)


def test_config_loads():
    """Verify config loads without error."""
    from src.config import PROJECT_ENDPOINT, FOUNDRY_MODEL
    assert FOUNDRY_MODEL == "gpt-4.1-mini"


if __name__ == "__main__":
    test_sample_incidents_valid()
    test_knowledge_base_exists()
    test_config_loads()
    print("All tests passed!")
