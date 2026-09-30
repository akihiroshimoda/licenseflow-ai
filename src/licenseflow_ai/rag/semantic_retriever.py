from sentence_transformers import SentenceTransformer
from sentence_transformers.util import semantic_search as st_semantic_search

from licenseflow_ai.rag.document_loader import load_chunks


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

model = SentenceTransformer(MODEL_NAME)


def semantic_search(
    query: str,
    top_k: int = 3,
) -> list[dict]:
    chunks = load_chunks()

    texts = [chunk["content"] for chunk in chunks]

    query_embedding = model.encode_query(
        [query],
        convert_to_tensor=True,
    )

    document_embeddings = model.encode_document(
        texts,
        convert_to_tensor=True,
    )

    hits = st_semantic_search(
        query_embedding,
        document_embeddings,
        top_k=min(top_k, len(chunks)),
    )[0]

    results = []

    for hit in hits:
        index = hit["corpus_id"]

        results.append(
            {
                **chunks[index],
                "score": float(hit["score"]),
            }
        )

    return results