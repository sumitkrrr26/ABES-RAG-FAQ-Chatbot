from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from rag_engine import answer_question


app = FastAPI(
    title="ABES LLM FAQ Chatbot API",
    description="RAG-based FAQ chatbot for ABES Engineering College",
    version="1.0.0"
)


# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/api/chat")
def chat(request: dict):

    question = request.get("question", "").strip()
    history = request.get("history", [])

    if not question:
        return {
            "success": False,
            "answer": "Please enter a question.",
            "sources": []
        }

    try:

        result = answer_question(
            question,
            history
        )

        return {
            "success": True,
            "answer": result["answer"],
            "sources": result["sources"]
        }

    except Exception as e:

        print("ERROR:", e)

        return {
            "success": False,
            "answer": "Sorry, something went wrong while processing your question.",
            "sources": []
        }


# Serve frontend
app.mount(
    "/",
    StaticFiles(
        directory="frontend",
        html=True
    ),
    name="frontend"
)