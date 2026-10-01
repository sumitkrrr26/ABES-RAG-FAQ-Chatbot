from pathlib import Path
import json
import os
import time

import faiss
import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import types


# --------------------------------------------------
# LOAD ENVIRONMENT
# --------------------------------------------------

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found in environment variables."
    )


client = genai.Client(
    api_key=API_KEY
)


# --------------------------------------------------
# PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).parent

CHUNKS_DIR = BASE_DIR / "chunks"
VECTOR_DIR = BASE_DIR / "vector_db"

VECTOR_DIR.mkdir(exist_ok=True)


# --------------------------------------------------
# EMBEDDING MODEL
# --------------------------------------------------

EMBEDDING_MODEL = "gemini-embedding-2"

EMBEDDING_DIMENSION = 768

print("\nLoading Gemini embedding system...")

print(
    f"Model: {EMBEDDING_MODEL}"
)

print(
    f"Dimension: {EMBEDDING_DIMENSION}"
)


# --------------------------------------------------
# LOAD ALL CHUNKS
# --------------------------------------------------

all_chunks = []

json_files = list(
    CHUNKS_DIR.rglob("*_chunks.json")
)

print(
    f"\nFound {len(json_files)} chunk files.\n"
)


for json_file in json_files:

    print(
        f"Reading: {json_file}"
    )

    with open(
        json_file,
        "r",
        encoding="utf-8"
    ) as f:

        chunks = json.load(f)

    for chunk in chunks:

        all_chunks.append({
            "chunk_id": chunk["chunk_id"],
            "source": chunk["source"],
            "page": chunk["page"],
            "text": chunk["text"]
        })


print(
    f"\nTotal chunks loaded: {len(all_chunks)}"
)


# --------------------------------------------------
# GET TEXT
# --------------------------------------------------

texts = [
    chunk["text"]
    for chunk in all_chunks
]


# --------------------------------------------------
# CREATE EMBEDDINGS
# --------------------------------------------------

print(
    "\nCreating Gemini embeddings..."
)

all_embeddings = []


for i, text in enumerate(
    texts,
    start=1
):

    print(
        f"Embedding {i}/{len(texts)}..."
    )

    try:

        result = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
            config=types.EmbedContentConfig(
                output_dimensionality=EMBEDDING_DIMENSION
            )
        )

        embedding = result.embeddings[0].values

        all_embeddings.append(
            embedding
        )

    except Exception as e:

        print(
            f"\nERROR while embedding chunk {i}:"
        )

        print(e)

        raise

    # Small delay to reduce the chance
    # of hitting API rate limits.

    if i < len(texts):
        time.sleep(0.2)


# --------------------------------------------------
# CONVERT TO NUMPY
# --------------------------------------------------

embeddings = np.array(
    all_embeddings,
    dtype="float32"
)


# --------------------------------------------------
# VALIDATE EMBEDDINGS
# --------------------------------------------------

print(
    f"\nEmbedding shape: {embeddings.shape}"
)


if len(embeddings) != len(all_chunks):

    raise ValueError(
        f"Embedding count mismatch: "
        f"{len(embeddings)} embeddings "
        f"for {len(all_chunks)} chunks."
    )


if embeddings.shape[1] != EMBEDDING_DIMENSION:

    raise ValueError(
        f"Unexpected embedding dimension: "
        f"{embeddings.shape[1]}"
    )


# --------------------------------------------------
# NORMALIZE EMBEDDINGS
# --------------------------------------------------

faiss.normalize_L2(
    embeddings
)


# --------------------------------------------------
# CREATE FAISS INDEX
# --------------------------------------------------

dimension = embeddings.shape[1]

print(
    f"\nVector dimension: {dimension}"
)


index = faiss.IndexFlatIP(
    dimension
)


index.add(
    embeddings
)


# --------------------------------------------------
# VALIDATE FAISS INDEX
# --------------------------------------------------

if index.ntotal != len(all_chunks):

    raise ValueError(
        f"FAISS index mismatch: "
        f"{index.ntotal} vectors "
        f"for {len(all_chunks)} chunks."
    )


# --------------------------------------------------
# SAVE FAISS INDEX
# --------------------------------------------------

index_path = (
    VECTOR_DIR / "abes_faq.index"
)


faiss.write_index(
    index,
    str(index_path)
)


# --------------------------------------------------
# SAVE METADATA
# --------------------------------------------------

metadata_path = (
    VECTOR_DIR / "metadata.json"
)


with open(
    metadata_path,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        all_chunks,
        f,
        indent=2,
        ensure_ascii=False
    )


# --------------------------------------------------
# COMPLETION
# --------------------------------------------------

print("\n================================")
print("Gemini embedding creation completed!")
print("================================")

print(
    f"\nFAISS index saved at:"
    f"\n{index_path}"
)

print(
    f"\nMetadata saved at:"
    f"\n{metadata_path}"
)

print(
    f"\nTotal chunks: {len(all_chunks)}"
)

print(
    f"Total vectors: {index.ntotal}"
)

print(
    f"Vector dimension: {dimension}"
)