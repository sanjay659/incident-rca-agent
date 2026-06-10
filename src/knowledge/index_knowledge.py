"""
Knowledge Base Indexer
=====================
Run ONCE to upload runbooks, past incidents, and known issues
into Azure AI Search so Agent 2 can search them via Foundry IQ.

Usage: python -m src.knowledge.index_knowledge
"""
import os
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
)
from azure.core.credentials import AzureKeyCredential
from src.config import (
    validate_config,
    PROJECT_ENDPOINT,
    AZURE_AI_SEARCH_ENDPOINT,
    AZURE_AI_SEARCH_KEY,
    KNOWLEDGE_BASE_INDEX,
)

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
KNOWLEDGE_DIR = "data/knowledge_base"


def get_resource_endpoint():
    """
    Extract resource-level endpoint from project endpoint.
    Project: https://xxx.services.ai.azure.com/api/projects/yyy
    Resource: https://xxx.services.ai.azure.com
    """
    parts = PROJECT_ENDPOINT.split("/api/projects")
    return parts[0]


def create_index(index_client: SearchIndexClient, index_name: str):
    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="hnsw-config")],
        profiles=[VectorSearchProfile(name="vector-profile", algorithm_configuration_name="hnsw-config")],
    )
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SimpleField(name="source_file", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="doc_type", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="title", type=SearchFieldDataType.String),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=EMBEDDING_DIMENSIONS,
            vector_search_profile_name="vector-profile",
        ),
    ]
    try:
        index_client.delete_index(index_name)
        print(f"  Deleted existing index: {index_name}")
    except Exception:
        pass

    index = SearchIndex(name=index_name, fields=fields, vector_search=vector_search)
    index_client.create_index(index)
    print(f"  ✅ Created index: {index_name}")


def chunk_document(filepath: str) -> list[dict]:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    filename = os.path.basename(filepath)

    if "runbook" in filename:
        doc_type = "runbook"
    elif "past_incident" in filename:
        doc_type = "past_incident"
    elif "known_issues" in filename:
        doc_type = "known_issues"
    else:
        doc_type = "general"

    title = filename
    for line in content.split("\n"):
        if line.startswith("# "):
            title = line.replace("# ", "").strip()
            break

    sections = []
    current_section = ""
    for line in content.split("\n"):
        if line.startswith("## ") and current_section.strip():
            sections.append(current_section.strip())
            current_section = line + "\n"
        else:
            current_section += line + "\n"
    if current_section.strip():
        sections.append(current_section.strip())

    if len(sections) <= 2 or len(content) < 1000:
        sections = [content]

    chunks = []
    for i, section in enumerate(sections):
        chunk_id = f"{filename.replace('.md', '')}_chunk_{i}"
        chunks.append({
            "id": chunk_id,
            "content": section,
            "source_file": filename,
            "doc_type": doc_type,
            "title": title,
        })
    return chunks


def generate_embeddings(openai_client, texts: list[str]) -> list[list[float]]:
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]


def main():
    print("\n>> Knowledge Base Indexer")
    print("=" * 60)

    validate_config()

    # ── Connect to Azure OpenAI at RESOURCE level (not project-scoped) ──
    # Why? Embeddings work at resource endpoint, not project-scoped endpoint.
    # Chat completions work at both, but embeddings only at resource level.
    print("\n>> Connecting to Foundry for embeddings...")
    resource_endpoint = get_resource_endpoint()
    print(f"  Resource endpoint: {resource_endpoint}")

    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
    )
    openai_client = AzureOpenAI(
        azure_endpoint=resource_endpoint,
        azure_ad_token_provider=token_provider,
        api_version="2025-03-01-preview",
    )
    print("  ✅ Foundry connected (resource-level)")

    # ── Connect to Azure AI Search ────────────────────────
    print("\n>> Connecting to Azure AI Search...")
    search_credential = AzureKeyCredential(AZURE_AI_SEARCH_KEY)
    index_client = SearchIndexClient(
        endpoint=AZURE_AI_SEARCH_ENDPOINT,
        credential=search_credential,
    )
    print("  ✅ Search connected")

    # ── Create index ──────────────────────────────────────
    print(f"\n>> Creating index: {KNOWLEDGE_BASE_INDEX}...")
    create_index(index_client, KNOWLEDGE_BASE_INDEX)

    # ── Read and chunk all knowledge files ────────────────
    print(f"\n>> Processing knowledge base files from {KNOWLEDGE_DIR}/...")
    all_chunks = []
    for filename in sorted(os.listdir(KNOWLEDGE_DIR)):
        if filename.endswith(".md"):
            filepath = os.path.join(KNOWLEDGE_DIR, filename)
            chunks = chunk_document(filepath)
            all_chunks.extend(chunks)
            print(f"  📄 {filename} → {len(chunks)} chunks")

    print(f"\n  Total chunks: {len(all_chunks)}")

    # ── Generate embeddings ───────────────────────────────
    print("\n>> Generating embeddings...")
    texts = [chunk["content"] for chunk in all_chunks]
    embeddings = generate_embeddings(openai_client, texts)
    for i, chunk in enumerate(all_chunks):
        chunk["content_vector"] = embeddings[i]
    print(f"  ✅ Generated {len(embeddings)} embeddings")

    # ── Upload to Azure AI Search ─────────────────────────
    print(f"\n>> Uploading to index: {KNOWLEDGE_BASE_INDEX}...")
    search_client = SearchClient(
        endpoint=AZURE_AI_SEARCH_ENDPOINT,
        index_name=KNOWLEDGE_BASE_INDEX,
        credential=search_credential,
    )
    result = search_client.upload_documents(documents=all_chunks)
    succeeded = sum(1 for r in result if r.succeeded)
    print(f"  ✅ Uploaded {succeeded}/{len(all_chunks)} documents")

    # ── Summary ───────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  INDEXING COMPLETE")
    print(f"  Index    : {KNOWLEDGE_BASE_INDEX}")
    print(f"  Endpoint : {AZURE_AI_SEARCH_ENDPOINT}")
    print(f"  Documents: {succeeded}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
