from pathlib import Path
import json

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


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

print("Loading embedding model...")

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

print("Embedding model loaded!")


# --------------------------------------------------
# LOAD ALL CHUNKS
# --------------------------------------------------

all_chunks = []

json_files = list(
    CHUNKS_DIR.rglob("*_chunks.json")
)

print(f"\nFound {len(json_files)} chunk files.\n")


for json_file in json_files:

    print(f"Reading: {json_file}")

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

print("\nCreating embeddings...")

embeddings = model.encode(
    texts,
    show_progress_bar=True,
    normalize_embeddings=True
)

embeddings = np.array(
    embeddings,
    dtype="float32"
)

print(
    f"Embedding shape: {embeddings.shape}"
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

index.add(embeddings)


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


print("\n================================")
print("Embedding creation completed!")
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
    f"\nTotal vectors: {index.ntotal}"
)