"""
backend/rag/vectorstore.py
───────────────────────────
FIX (original bug #10):
  • Old code: load_db() crashed with an unhandled exception if the
              vectorstore directory didn't exist yet.
  • New code: raises a clean FileNotFoundError that callers can catch
              and surface as a helpful message to the student.
"""

import os
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

VECTORSTORE_PATH = os.getenv("VECTORSTORE_PATH", "data/vectorstore")
EMBEDDING_MODEL  = "all-MiniLM-L6-v2"

# Singleton so we don't reload embeddings on every request
_embeddings: HuggingFaceEmbeddings | None = None


def get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return _embeddings


def load_db() -> FAISS:
    """
    Load the FAISS vectorstore from disk.

    Raises:
        FileNotFoundError: if no documents have been ingested yet.
    """
    index_file = Path(VECTORSTORE_PATH) / "index.faiss"
    if not index_file.exists():
        raise FileNotFoundError(
            "No knowledge base found. Please upload at least one study document."
        )

    return FAISS.load_local(
        VECTORSTORE_PATH,
        get_embeddings(),
        # NOTE: allow_dangerous_deserialization is required for FAISS pickle.
        # This is safe here because we only load vectorstores WE created.
        allow_dangerous_deserialization=True,
    )


def db_exists() -> bool:
    """Check whether any documents have been ingested."""
    return (Path(VECTORSTORE_PATH) / "index.faiss").exists()
