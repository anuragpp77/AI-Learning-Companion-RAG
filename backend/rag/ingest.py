"""
backend/rag/ingest.py
──────────────────────
FIX (original bug #4):
  • Old code: every new upload called FAISS.from_documents() and
              saved_local(), silently deleting ALL previously indexed docs.
  • New code: we load the existing index (if any), call merge_from() with
              the new chunks, then save — so knowledge accumulates.

IMPROVEMENT — multi-format support:
  Supports PDF, DOCX, TXT, MD, and PPTX.  Detected by file extension.

IMPROVEMENT — chunk metadata:
  Every chunk is tagged with {source, page, file_type, ingested_at} so
  answers can cite the exact document and page number.
"""

import os
from datetime import datetime
from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredPowerPointLoader,
)
from langchain_community.document_loaders import Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

from backend.rag.vectorstore import get_embeddings, VECTORSTORE_PATH

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".pptx"}


def _get_loader(path: str):
    """Return the appropriate LangChain loader for the given file."""
    ext = Path(path).suffix.lower()
    if ext == ".pdf":
        return PyPDFLoader(path)
    if ext == ".docx":
        return Docx2txtLoader(path)
    if ext in {".txt", ".md"}:
        return TextLoader(path, encoding="utf-8")
    if ext == ".pptx":
        return UnstructuredPowerPointLoader(path)
    raise ValueError(
        f"Unsupported file type '{ext}'. "
        f"Supported types: {', '.join(SUPPORTED_EXTENSIONS)}"
    )


def ingest_file(file_path: str, original_filename: str) -> int:
    """
    Load, chunk, embed, and merge a document into the FAISS vectorstore.

    Args:
        file_path:         Absolute path to the saved file on disk.
        original_filename: The user-facing filename (used in metadata).

    Returns:
        Number of chunks added to the vectorstore.

    Raises:
        ValueError: for unsupported file types.
        RuntimeError: if embedding or indexing fails.
    """
    ext = Path(file_path).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{ext}'. "
            f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    # 1. Load
    loader = _get_loader(file_path)
    docs   = loader.load()

    if not docs:
        raise RuntimeError(f"No content could be extracted from {original_filename}")

    # 2. Attach metadata to every document page
    for doc in docs:
        doc.metadata.update({
            "source":       original_filename,
            "file_type":    ext.lstrip("."),
            "ingested_at":  datetime.now().isoformat(),
        })

    # 3. Chunk
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    chunks = splitter.split_documents(docs)

    if not chunks:
        raise RuntimeError("Document produced no text chunks after splitting.")

    # 4. Embed
    embeddings = get_embeddings()
    new_db     = FAISS.from_documents(chunks, embeddings)

    # 5. Merge with existing store (FIX for bug #4)
    Path(VECTORSTORE_PATH).mkdir(parents=True, exist_ok=True)
    index_file = Path(VECTORSTORE_PATH) / "index.faiss"

    if index_file.exists():
        try:
            existing = FAISS.load_local(
                VECTORSTORE_PATH,
                embeddings,
                allow_dangerous_deserialization=True,
            )
            existing.merge_from(new_db)
            existing.save_local(VECTORSTORE_PATH)
        except Exception as e:
            # If the existing index is corrupt, start fresh rather than crash
            print(f"[WARNING] Could not merge with existing index ({e}). Starting fresh.")
            new_db.save_local(VECTORSTORE_PATH)
    else:
        new_db.save_local(VECTORSTORE_PATH)

    return len(chunks)
