from pathlib import Path
import json

import faiss
from sentence_transformers import SentenceTransformer


# ---------------------------------------
# PATHS
# ---------------------------------------

BASE_DIR = Path(__file__).parent

VECTOR_DIR = BASE_DIR / "vector_db"

INDEX_PATH = VECTOR_DIR / "abes_faq.index"
METADATA_PATH = VECTOR_DIR / "metadata.json"


# ---------------------------------------
# LOAD MODEL
# ---------------------------------------

print("Loading embedding model...")

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

print("Model loaded.")


# ---------------------------------------
# LOAD FAISS
# ---------------------------------------

index = faiss.read_index(
    str(INDEX_PATH)
)


# ---------------------------------------
# LOAD METADATA
# ---------------------------------------

with open(
    METADATA_PATH,
    "r",
    encoding="utf-8"
) as f:

    metadata = json.load(f)


print(f"Loaded {index.ntotal} vectors.")


# ---------------------------------------
# SEARCH FUNCTION
# ---------------------------------------

def search(query, top_k=3):

    # Convert question into embedding

    query_embedding = model.encode(
        [query],
        normalize_embeddings=True
    )

    # Search FAISS

    scores, indices = index.search(
        query_embedding,
        top_k
    )

    results = []

    for score, idx in zip(
        scores[0],
        indices[0]
    ):

        if idx == -1:
            continue

        result = metadata[idx].copy()

        result["score"] = float(score)

        results.append(result)

    return results


# ---------------------------------------
# INTERACTIVE CHAT
# ---------------------------------------

print("\n================================")
print("ABES RAG Retriever")
print("================================")

while True:

    query = input(
        "\nAsk a question "
        "(type 'exit' to stop): "
    )

    if query.lower() == "exit":
        break

    results = search(
        query,
        top_k=5
    )

    print("\n----- RETRIEVED RESULTS -----")

    for i, result in enumerate(
        results,
        start=1
    ):

        print(
            f"\nResult {i}"
        )

        print(
            f"Score: {result['score']:.4f}"
        )

        print(
            f"Source: {result['source']}"
        )

        print(
            f"Page: {result['page']}"
        )

        print(
            f"Text:\n{result['text']}"
        )

        print(
            "-" * 60
        )