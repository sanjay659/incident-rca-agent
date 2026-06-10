"""
Foundry IQ Client — Search Wrapper
===================================
Wraps Azure AI Search to provide hybrid search (text + vector)
over the incident knowledge base.

Agent 2 calls this to find relevant runbooks, past incidents, known issues.
"""
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential

EMBEDDING_MODEL = "text-embedding-3-small"


class FoundryIQClient:

    def __init__(self, search_endpoint: str, search_key: str, index_name: str, openai_client: AzureOpenAI):
        self.search_client = SearchClient(
            endpoint=search_endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(search_key),
        )
        self.openai_client = openai_client
        self.index_name = index_name

    def _get_embedding(self, text: str) -> list[float]:
        response = self.openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=[text],
        )
        return response.data[0].embedding

    def search(self, query: str, doc_type: str = None, top: int = 5) -> list[dict]:
        query_vector = VectorizedQuery(
            vector=self._get_embedding(query),
            k=top,
            fields="content_vector",
        )

        filter_expr = f"doc_type eq '{doc_type}'" if doc_type else None

        results = self.search_client.search(
            search_text=query,
            vector_queries=[query_vector],
            filter=filter_expr,
            top=top,
            select=["content", "source_file", "doc_type", "title"],
        )

        documents = []
        for result in results:
            documents.append({
                "content": result["content"],
                "source_file": result["source_file"],
                "doc_type": result["doc_type"],
                "title": result["title"],
                "relevance_score": result["@search.score"],
            })
        return documents

    def search_multiple(self, queries: list[str], top_per_query: int = 3) -> list[dict]:
        seen_ids = set()
        all_results = []

        for query in queries:
            results = self.search(query, top=top_per_query)
            for doc in results:
                doc_id = f"{doc['source_file']}_{doc['content'][:50]}"
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    all_results.append(doc)

        all_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return all_results
