from pathlib import Path
import json
import time
import faiss

from sentence_transformers import SentenceTransformer
from google import genai
from dotenv import load_dotenv


# ==========================================
# LOAD ENVIRONMENT VARIABLES
# ==========================================

load_dotenv()


# ==========================================
# GEMINI CONFIGURATION
# ==========================================

MODEL_NAME = "gemini-3.6-flash"

client = genai.Client()


# ==========================================
# RAG CONFIGURATION
# ==========================================

TOP_K = 3
MIN_SCORE = 0.30


# ==========================================
# PATHS
# ==========================================

BASE_DIR = Path(__file__).parent

VECTOR_DIR = BASE_DIR / "vector_db"

INDEX_PATH = VECTOR_DIR / "abes_faq.index"
METADATA_PATH = VECTOR_DIR / "metadata.json"


# ==========================================
# LOAD EMBEDDING MODEL
# ==========================================

print("Loading embedding model...")

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# ==========================================
# LOAD FAISS INDEX
# ==========================================

index = faiss.read_index(
    str(INDEX_PATH)
)


# ==========================================
# LOAD METADATA
# ==========================================

with open(
    METADATA_PATH,
    "r",
    encoding="utf-8"
) as f:

    metadata = json.load(f)


print(f"Loaded {index.ntotal} vectors.")


# ==========================================
# RETRIEVAL
# ==========================================

def retrieve(
    query,
    top_k=TOP_K,
    min_score=MIN_SCORE
):

    query_embedding = embedding_model.encode(
        [query],
        normalize_embeddings=True
    )

    scores, indices = index.search(
        query_embedding,
        top_k
    )

    results = []

    for score, idx in zip(
        scores[0],
        indices[0]
    ):

        # Skip invalid FAISS results
        if idx == -1:
            continue

        score = float(score)

        # Relevance threshold
        if score < min_score:
            continue

        result = metadata[idx].copy()

        result["score"] = score

        results.append(result)

    return results


# ==========================================
# BUILD CONTEXT
# ==========================================

def build_context(results):

    context_parts = []

    for i, result in enumerate(
        results,
        start=1
    ):

        context_parts.append(
            f"""
SOURCE {i}

Document: {result['source']}
Page: {result['page']}

Content:
{result['text']}
"""
        )

    return "\n".join(context_parts)


# ==========================================
# ASK GEMINI
# ==========================================

def ask_gemini(question, context):

    system_instruction = """
You are an AI FAQ assistant for ABES Engineering College.

Answer the student's question using ONLY the retrieved
ABES college documents.

Rules:

1. Do not use outside knowledge.
2. Do not invent missing information.
3. Do not assume information that is not present.
4. If the documents do not contain enough information,
   say exactly:

"I couldn't find this information in the available
ABES documents."

5. If documents contain conflicting information,
   explicitly mention the conflict.
6. Prefer the more recent or applicable document when
   dates are available.
7. Keep the answer concise and student-friendly.
8. Provide the relevant source document and page number.
"""

    # ==========================================
    # RAG PROMPT
    # ==========================================

    prompt = f"""
Retrieved ABES documents:

{context}

Student question:

{question}

Answer using ONLY the retrieved documents.

If the documents do not contain enough information,
say:

"I couldn't find this information in the available
ABES documents."

If documents disagree, mention the disagreement.

Keep the answer concise. Use a short list when the
question asks for multiple items.

At the end provide:

Source:
- Document name
- Page number
"""

    # ==========================================
    # GEMINI API REQUEST
    # ==========================================

    interaction = client.interactions.create(
        model=MODEL_NAME,
        input=prompt,
        system_instruction=system_instruction
    )

    return interaction.output_text


# ==========================================
# MAIN CHATBOT
# ==========================================

print("\n===================================")
print("ABES LLM RAG CHATBOT")
print("===================================")
print(f"Model: {MODEL_NAME}")
print(f"Top-K: {TOP_K}")
print(f"Minimum similarity score: {MIN_SCORE}")
print("===================================")


while True:

    question = input(
        "\nAsk a question (type 'exit' to stop): "
    ).strip()


    # ======================================
    # EXIT
    # ======================================

    if question.lower() == "exit":

        print("Goodbye!")

        break


    # ======================================
    # EMPTY QUESTION
    # ======================================

    if not question:

        print("\nPlease enter a question.")

        continue


    # ======================================
    # RETRIEVE DOCUMENTS
    # ======================================

    retrieval_start = time.perf_counter()

    results = retrieve(
        question,
        top_k=TOP_K,
        min_score=MIN_SCORE
    )

    retrieval_time = time.perf_counter() - retrieval_start


    print(
        f"\nRetrieval time: "
        f"{retrieval_time:.2f} seconds"
    )


    # ======================================
    # RELEVANCE CHECK
    # ======================================

    if not results:

        print("\n-----------------------------------")
        print("ANSWER")
        print("-----------------------------------")

        print(
            "I couldn't find this information in the "
            "available ABES documents."
        )

        print("-----------------------------------")

        continue


    # ======================================
    # OPTIONAL RETRIEVAL DEBUG INFO
    # ======================================

    print(
        f"Retrieved {len(results)} relevant "
        f"document chunk(s)."
    )


    # ======================================
    # BUILD CONTEXT
    # ======================================

    context = build_context(
        results
    )


    # ======================================
    # ASK GEMINI
    # ======================================

    gemini_start = time.perf_counter()

    try:

        answer = ask_gemini(
            question,
            context
        )

    except Exception as e:

        gemini_time = time.perf_counter() - gemini_start

        print(
            f"\nGemini request time: "
            f"{gemini_time:.2f} seconds"
        )

        print("\n-----------------------------------")
        print("Gemini API Error")
        print("-----------------------------------")
        print(e)
        print("-----------------------------------")

        continue


    gemini_time = time.perf_counter() - gemini_start


    # ======================================
    # DISPLAY TIMING
    # ======================================

    print(
        f"Gemini response time: "
        f"{gemini_time:.2f} seconds"
    )


    # ======================================
    # DISPLAY ANSWER
    # ======================================

    print("\n-----------------------------------")
    print("ANSWER")
    print("-----------------------------------")

    print(answer)

    print("-----------------------------------")