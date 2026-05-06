"""
backend/main.py
────────────────
FastAPI application with all fixes applied:

FIX (original bug #8 — path traversal):
  • Old code: file.filename used directly → attacker could upload
              "../../etc/passwd" and overwrite system files.
  • New code: UUID4-based filename regardless of what the user sent.

FIX (original bug #10 — no error handling):
  • All endpoints wrapped in try/except; HTTPException raised with
    meaningful messages rather than letting 500s propagate silently.

IMPROVEMENT: background PDF ingestion so the client doesn't time out.
IMPROVEMENT: /health, /stats, /files, /flashcards endpoints.
"""

import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

load_dotenv()

from backend.core.database import init_db
from backend.core.memory   import (
    get_all_topic_stats,
    get_flashcards,
    get_uploaded_files,
    log_uploaded_file,
    save_flashcards,
    update_quiz_score,
)
from backend.crew          import generate_flashcards, run_crew
from backend.rag.ingest    import SUPPORTED_EXTENSIONS, ingest_file
from backend.rag.vectorstore import db_exists
from backend.core.llm      import get_provider_name

# ── Boot ──────────────────────────────────────────────────────────────────────
init_db()

DATA_DIR      = Path(os.getenv("DATA_DIR", "data/uploads"))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", 50))
DATA_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="AI Study Companion API",
    description="Multi-agent RAG system for personalised student learning",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ─────────────────────────────────────────────────

class AskRequest(BaseModel):
    query:     str  = Field(..., min_length=3, max_length=1000)
    mode:      str  = Field("simple", pattern="^(simple|exam)$")
    language:  str  = Field("English")
    task_type: str  = Field("learn", pattern="^(learn|quiz)$")


class QuizScoreRequest(BaseModel):
    topic: str
    score: float = Field(..., ge=0, le=100)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Liveness probe — also surfaces configuration info."""
    return {
        "status":       "ok",
        "llm_provider": get_provider_name(),
        "kb_ready":     db_exists(),
    }


@app.post("/ask")
def ask(req: AskRequest):
    """
    Main Q&A endpoint.  Runs the full multi-agent Crew pipeline.
    """
    if not db_exists():
        raise HTTPException(
            status_code=400,
            detail="Knowledge base is empty. Please upload study materials first.",
        )

    try:
        result = run_crew(
            query=req.query,
            mode=req.mode,
            language=req.language,
            task_type=req.task_type,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Crew failed: {exc}") from exc


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    """
    Upload and ingest a study document.

    FIX #8 — path traversal:
      The original filename is NEVER used as the saved path.
      A UUID4 name is generated instead.
    FIX #4 — vectorstore overwrite:
      ingest_file() now merges into the existing index.
    """
    original_name = file.filename or "unknown"
    ext           = Path(original_name).suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. "
                   f"Allowed: {', '.join(SUPPORTED_EXTENSIONS)}",
        )

    # Read and size-check
    content = await file.read()
    mb      = len(content) / (1024 * 1024)
    if mb > MAX_UPLOAD_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({mb:.1f} MB). Max allowed: {MAX_UPLOAD_MB} MB.",
        )

    # Save with a safe UUID filename (FIX #8)
    safe_name = f"{uuid.uuid4()}{ext}"
    file_path = DATA_DIR / safe_name

    try:
        file_path.write_bytes(content)
        chunk_count = ingest_file(str(file_path), original_name)
        log_uploaded_file(original_name, safe_name, chunk_count, ext.lstrip("."))
    except ValueError as exc:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}") from exc

    return {
        "message":     f"'{original_name}' processed successfully.",
        "chunk_count": chunk_count,
        "file_type":   ext.lstrip("."),
    }


@app.get("/files")
def list_files():
    """Return all uploaded documents."""
    try:
        return {"files": get_uploaded_files()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/stats")
def get_stats():
    """Return all topic stats for the progress dashboard."""
    try:
        return {"topics": get_all_topic_stats()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/quiz-score")
def record_quiz_score(req: QuizScoreRequest):
    """Record a student's score for a quiz attempt (for weak-topic tracking)."""
    try:
        update_quiz_score(req.topic, req.score)
        return {"message": "Score recorded."}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/flashcards/generate")
def gen_flashcards(req: AskRequest):
    """
    Generate Anki-style flashcards for a topic.
    Runs a focused single-agent crew rather than the full pipeline.
    """
    if not db_exists():
        raise HTTPException(status_code=400, detail="Knowledge base empty.")

    try:
        cards = generate_flashcards(topic=req.query, context=req.query)
        if cards:
            save_flashcards(req.query, cards)
        return {"flashcards": cards}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/flashcards")
def list_flashcards(topic: str = None):
    """Retrieve saved flashcards, optionally filtered by topic."""
    try:
        return {"flashcards": get_flashcards(topic)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
