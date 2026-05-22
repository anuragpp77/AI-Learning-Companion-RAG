"""
backend/core/llm.py
───────────────────
"""

import os


def get_llm():
    """
    Return a LangChain-compatible chat model for the detected provider.

    Uses LangChain objects directly instead of crewai.LLM so this works
    across ALL CrewAI versions (older ones reject crewai.LLM and fall back
    to ChatOpenAI, causing the 'openai_api_key not found' crash).
    """
    groq_key   = os.getenv("GROQ_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "mistral")


    if groq_key:
        from langchain_groq import ChatGroq
        return ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=groq_key,
            temperature=0.3,
        )

    if openai_key:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="gpt-3.5-turbo",
            api_key=openai_key,
            temperature=0.3,
        )

    # ── Ollama (local, no API key needed) ─────────────────────────────────────
    from langchain_ollama import ChatOllama
    return ChatOllama(
        model=ollama_model,
        base_url=ollama_url,
        temperature=0.3,
    )


def get_provider_name() -> str:
    """Human-readable name of the active provider (used in logs/UI)."""
    if os.getenv("GROQ_API_KEY"):
        return "Groq (llama3-8b)"
    if os.getenv("OPENAI_API_KEY"):
        return "OpenAI (gpt-3.5-turbo)"
    return f"Ollama ({os.getenv('OLLAMA_MODEL', 'mistral')})"
