"""
Streamlit UI for Incident Root Cause Analyzer
==============================================
Run: streamlit run src/ui/app.py
"""
import streamlit as st
import json
import os
import sys

# Add project root to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.main import setup


st.set_page_config(
    page_title="Incident RCA Agent",
    page_icon="🔍",
    layout="wide",
)

st.title("🔍 Incident Root Cause Analyzer")
st.markdown("**4-Agent Reasoning Pipeline** — powered by Microsoft Foundry + Foundry IQ")
st.markdown("---")

# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")
    st.success("✅ Connected to Azure AI Foundry")
    st.info(f"🧠 Model: gpt-4.1-mini")
    st.info(f"🔎 Search: Foundry IQ")

    st.markdown("---")
    st.header("📂 Sample Incidents")
    sample_dir = "data/sample_incidents"
    sample_files = [f for f in os.listdir(sample_dir) if f.endswith(".json")]

    selected_file = st.selectbox("Select an incident:", sample_files)

    st.markdown("---")
    st.markdown("### 🏗️ Architecture")
    st.markdown("""
    ```
    Agent 1 → Log Analyzer
    Agent 2 → Knowledge Retriever
    Agent 3 → Root Cause Reasoner
    Agent 4 → Action Recommender
    ```
    """)

# ── Load incident ─────────────────────────────────────────
with open(os.path.join(sample_dir, selected_file), "r") as f:
    incident = json.load(f)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Incident ID", incident["incident_id"])
with col2:
    st.metric("Severity", incident["severity"])
with col3:
    st.metric("Error Rate", incident["alert_details"]["error_rate"])

st.subheader(f"📋 {incident['title']}")

with st.expander("View Raw Incident Data", expanded=False):
    st.json(incident)

# ── Run Pipeline ──────────────────────────────────────────
if st.button("🚀 Run RCA Analysis", type="primary", use_container_width=True):

    # Initialize pipeline (cached to avoid reconnecting each time)
    @st.cache_resource
    def get_pipeline():
        return setup()

    pipeline = get_pipeline()

    # Agent progress tracking
    progress = st.progress(0, text="Starting analysis...")
    agent_status = st.empty()

    # Containers for each agent output
    containers = {
        "agent1": st.container(),
        "agent2": st.container(),
        "agent3": st.container(),
        "agent4": st.container(),
    }

    def on_step(agent_name, step_number, result):
        progress.progress(step_number * 25, text=f"Agent {step_number}: {agent_name} complete")

    report = pipeline.run(incident, on_step=on_step)
    progress.progress(100, text="✅ Analysis complete!")

    # ── Display Agent 1 Results ───────────────────────────
    with containers["agent1"]:
        st.markdown("---")
        st.subheader("🔎 Agent 1: Log Analyzer")
        analysis = report["analysis"]

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Failure Pattern", analysis.get("failure_pattern", "unknown"))
        with col2:
            severity = analysis.get("severity_assessment", {})
            st.metric("Severity", severity.get("recommended", "N/A"))

        st.markdown("**Timeline:**")
        for event in analysis.get("timeline", []):
            st.markdown(f"- `{event['timestamp']}` — {event['event']}")

        st.markdown("**Key Observations:**")
        for obs in analysis.get("key_observations", []):
            st.markdown(f"- {obs}")

    # ── Display Agent 2 Results ───────────────────────────
    with containers["agent2"]:
        st.markdown("---")
        st.subheader("📚 Agent 2: Knowledge Retriever (Foundry IQ)")
        ks = report["knowledge_summary"]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Runbooks Found", ks["runbooks_found"])
        with col2:
            st.metric("Past Incidents", ks["past_incidents_found"])
        with col3:
            st.metric("Known Issues", ks["known_issues_found"])

        st.markdown("**Search Queries Generated:**")
        for q in ks.get("queries", []):
            st.markdown(f"- `{q}`")

    # ── Display Agent 3 Results ───────────────────────────
    with containers["agent3"]:
        st.markdown("---")
        st.subheader("🧠 Agent 3: Root Cause Reasoner")
        rc = report["root_cause"]
        primary = rc.get("primary_root_cause", {})

        col1, col2, col3 = st.columns(3)
        with col1:
            confidence = primary.get("confidence", 0)
            st.metric("Confidence", f"{confidence:.0%}")
        with col2:
            st.metric("Category", primary.get("category", "unknown"))
        with col3:
            st.metric("Component", primary.get("affected_component", "unknown"))

        st.error(f"**Root Cause:** {primary.get('cause', 'unknown')}")
        st.markdown(f"**Explanation:** {primary.get('explanation', '')}")

        st.markdown("**Reasoning Chain:**")
        for step in rc.get("reasoning_chain", []):
            with st.expander(f"Step {step['step']}: {step['action']}"):
                st.markdown(step["details"])

        if rc.get("hypotheses"):
            st.markdown("**All Hypotheses:**")
            for h in rc["hypotheses"]:
                conf = h.get("confidence", 0)
                icon = "🟢" if conf >= 0.7 else "🟡" if conf >= 0.4 else "🔴"
                st.markdown(f"{icon} **{h['cause']}** — Confidence: {conf:.0%}")

        if rc.get("correlated_past_incidents"):
            st.info(f"📜 Correlated Past Incidents: {', '.join(rc['correlated_past_incidents'])}")
        if rc.get("correlated_known_issues"):
            st.warning(f"⚠️ Correlated Known Issues: {', '.join(rc['correlated_known_issues'])}")

    # ── Display Agent 4 Results ───────────────────────────
    with containers["agent4"]:
        st.markdown("---")
        st.subheader("🚨 Agent 4: Action Recommender")
        actions = report["actions"]

        st.markdown("**Immediate Actions:**")
        for action in actions.get("immediate_actions", []):
            priority = action.get("priority", "?")
            risk = action.get("risk_level", "unknown")
            risk_color = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(risk, "⚪")

            with st.expander(f"P{priority} {risk_color} — {action['action'][:80]}"):
                st.markdown(f"**Expected Outcome:** {action.get('expected_outcome', 'N/A')}")
                st.markdown(f"**Risk Level:** {risk}")
                if action.get("command"):
                    st.code(action["command"], language="bash")

        esc = actions.get("escalation", {})
        if esc.get("required"):
            st.warning(f"📞 **Escalation Required** — Teams: {', '.join(esc.get('teams', []))}")
            st.markdown(f"**Timeline:** {esc.get('timeline', 'N/A')}")
            st.info(f"**Suggested Communication:** {esc.get('communication', 'N/A')}")

        blast = actions.get("blast_radius", {})
        if blast:
            st.markdown("**Blast Radius:**")
            st.markdown(f"- **Affected Users:** {blast.get('affected_users', 'N/A')}")
            st.markdown(f"- **Business Impact:** {blast.get('business_impact', 'N/A')}")
            st.markdown(f"- **Estimated Duration:** {blast.get('estimated_duration', 'N/A')}")

        if actions.get("prevention"):
            st.markdown("**Prevention Recommendations:**")
            for p in actions["prevention"]:
                st.markdown(f"- [{p.get('priority', 'N/A')}] {p['recommendation']}")

    # ── Final Summary ─────────────────────────────────────
    st.markdown("---")
    st.subheader("📊 Summary")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Time", f"{report['metadata']['time_seconds']}s")
    with col2:
        st.metric("LLM Calls", "4")
    with col3:
        st.metric("Search Queries", len(ks.get("queries", [])))
    with col4:
        st.metric("Model", report["metadata"]["model"])

    # Download report
    st.download_button(
        "📥 Download Full RCA Report (JSON)",
        data=json.dumps(report, indent=2),
        file_name=f"rca_report_{incident['incident_id']}.json",
        mime="application/json",
        use_container_width=True,
    )
