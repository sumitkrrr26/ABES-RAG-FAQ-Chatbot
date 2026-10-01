from pathlib import Path
import json
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
# CONFIGURATION
# ==========================================

TOP_K = 3

MIN_SCORE = 0.30


# ==========================================
# RETRIEVAL
# ==========================================

def retrieve(query):

    query_embedding = embedding_model.encode(
        [query],
        normalize_embeddings=True
    )

    scores, indices = index.search(
        query_embedding,
        TOP_K
    )

    results = []

    for score, idx in zip(
        scores[0],
        indices[0]
    ):

        if idx == -1:
            continue

        score = float(score)

        if score < MIN_SCORE:
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
# FORMAT CONVERSATION HISTORY
# ==========================================

def build_history(history):

    if not history:
        return ""

    history_text = []

    for message in history[-6:]:

        role = message.get("role", "")
        content = message.get("content", "")

        if role == "user":

            history_text.append(
                f"Student: {content}"
            )

        elif role == "assistant":

            history_text.append(
                f"Assistant: {content}"
            )

    return "\n".join(history_text)


# ==========================================
# ASK GEMINI
# ==========================================

def ask_gemini(
    question,
    context,
    history=None
):

    if history is None:
        history = []

    system_instruction = """
You are an AI FAQ assistant for ABES Engineering College.

You answer student questions using ONLY the retrieved
ABES college documents provided to you.

IMPORTANT RULES:

1. Use the retrieved ABES documents as the source of truth.

2. Do NOT invent college-specific information.

3. Do NOT use outside knowledge for ABES-specific facts.

4. If the retrieved documents do not contain enough
information to answer the question, say exactly:

"I couldn't find this information in the available ABES documents."

5. If different documents contain conflicting information,
explicitly mention the disagreement.

6. Prefer the more recent or more applicable document
when dates are available.

7. Keep the answer concise and student-friendly.

8. Always provide the relevant source document and page
number when the answer is supported by the documents.

9. Never pretend that information exists in the documents
when it does not.

10. Conversation history can be used only to understand
the student's current question. College-specific facts
must still come from the retrieved documents.
"""

    history_text = build_history(history)

    prompt = f"""
You are answering a student's question about ABES Engineering College.

================ RETRIEVED ABES DOCUMENTS ================

{context}

================ CONVERSATION HISTORY =====================

{history_text}

================ CURRENT STUDENT QUESTION =================

{question}

================ INSTRUCTIONS =============================

Answer the current question using ONLY the retrieved
ABES documents.

Do not use outside knowledge.

Do not invent information.

If the documents do not contain enough information,
say exactly:

"I couldn't find this information in the available ABES documents."

If documents disagree, explicitly mention the disagreement.

Keep the answer concise and student-friendly.

At the end provide:

Source:
- Document name
- Page number
"""

    interaction = client.interactions.create(
        model=MODEL_NAME,
        input=prompt,
        system_instruction=system_instruction
    )

    return interaction.output_text


# ==========================================
# COMPLETE RAG QUESTION
# ==========================================

def answer_question(question, history=None):

    # -------------------------------------------------
    # Build a context-aware retrieval query
    # -------------------------------------------------

    retrieval_query = question

    if history:

        recent_history = history[-6:]

        history_text = []

        for message in recent_history:

            role = message.get("role", "")
            content = message.get("content", "")

            if content:
                history_text.append(
                    f"{role}: {content}"
                )

        if history_text:

            retrieval_query = (
                "Conversation context:\n"
                + "\n".join(history_text)
                + "\n\nCurrent question:\n"
                + question
            )


    # -------------------------------------------------
    # Retrieve relevant ABES documents
    # -------------------------------------------------

    results = retrieve(retrieval_query)


    # -------------------------------------------------
    # No relevant documents found
    # -------------------------------------------------

    if not results:

        return {
            "answer": (
                "I couldn't find this information in "
                "the available ABES documents."
            ),
            "sources": []
        }


    # -------------------------------------------------
    # Build RAG context
    # -------------------------------------------------

    context = build_context(results)


    # -------------------------------------------------
    # Generate answer with Gemini
    # -------------------------------------------------

    answer = ask_gemini(
        question,
        context,
        history
    )


    # -------------------------------------------------
    # Prepare source information
    # -------------------------------------------------

    sources = []

    for result in results:

        sources.append({
            "document": result["source"],
            "page": result["page"],
            "score": round(
                result["score"],
                4
            )
        })


    return {
        "answer": answer,
        "sources": sources
    }