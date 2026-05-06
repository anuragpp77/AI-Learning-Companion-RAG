"""
backend/agents/summarizer.py
─────────────────────────────
NEW agent (recommended in the review).

Purpose: sit between the retriever and the teacher/evaluator.
Raw FAISS chunks can be noisy — duplicate sentences, incomplete
paragraphs, garbled OCR text. The summarizer cleans and condenses
the retrieved context so the teacher gets a high-quality input.
"""

from crewai import Agent
from backend.core.llm import get_llm


summarizer = Agent(
    role="Context Summarizer",
    goal=(
        "Distil raw retrieved document chunks into a clean, coherent, "
        "and well-structured context block that another agent can use "
        "to answer a student's question accurately."
    ),
    backstory=(
        "You are a meticulous academic editor. Given messy, overlapping "
        "text chunks from different pages and documents, you synthesise "
        "them into a tight, logical summary — removing noise, resolving "
        "duplication, and preserving all key facts and definitions. "
        "You always keep track of where each piece of information came "
        "from so sources can be cited later."
    ),
    llm=get_llm(),
    verbose=True,
    allow_delegation=False,
)
