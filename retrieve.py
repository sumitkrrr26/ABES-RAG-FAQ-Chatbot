from pathlib import Path
import json
import os

import faiss
import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import types


# ---------------------------------------
# LOAD ENVIRONMENT
# ---------------------------------------

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found in environment variables."
    )


client = genai.Client(
    api_key=API_KEY
)


# ---------------------------------------
# PATHS
# ---------------------------------------

BASE_DIR = Path(__file__).parent

VECTOR_DIR = BASE_DIR / "vector_db"

INDEX_PATH = VECTOR_DIR / "abes_faq.index"
METADATA_PATH = VECTOR_DIR / "metadata.json"


# ---------------------------------------
# EMBEDDING MODEL
# ---------------------------------------

EMBEDDING_MODEL = "gemini-embedding-2"
EMBEDDING_DIMENSION = 768

print("Loading Gemini embedding system...")

print(
    f"Model: {EMBEDDING_MODEL}"
)

print(
    f"Dimension: {EMBEDDING_DIMENSION}"
)


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


print(
    f"Loaded {index.ntotal} vectors."
)


# ---------------------------------------
# SEARCH FUNCTION
# ---------------------------------------

def search(query, top_k=3):

    # -----------------------------------
    # CREATE GEMINI QUERY EMBEDDING
    # -----------------------------------

    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=[query],
        config=types.EmbedContentConfig(
            output_dimensionality=EMBEDDING_DIMENSION
        )
    )

    query_embedding = np.array(
        [
            result.embeddings[0].values
        ],
        dtype="float32"
    )

    # Normalize for cosine similarity
    # using FAISS Inner Product

    faiss.normalize_L2(
        query_embedding
    )


    # -----------------------------------
    # SEARCH FAISS
    # -----------------------------------

    scores, indices = index.search(
        query_embedding,
        top_k
    )


    # -----------------------------------
    # BUILD RESULTS
    # -----------------------------------

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


    print(
        "\n----- RETRIEVED RESULTS -----"
    )


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