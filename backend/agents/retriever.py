"""
backend/agents/retriever.py
"""

from crewai import Agent

# crewai moved @tool across versions — try all known locations
try:
    from crewai.tools import tool
except ImportError:
    try:
        from crewai_tools import tool
    except ImportError:
        from langchain_core.tools import tool

from backend.core.llm import get_llm
from backend.rag.vectorstore import load_db


@tool("Search Knowledge Base")
def retrieve_tool(query: str) -> str:
    """
    Semantic search over the student's uploaded study materials.
    Returns the most relevant text chunks along with their source
    document and page number so answers can be properly cited.
    Use this tool whenever you need factual content about any topic.
    """
    try:
        db = load_db()
        docs = db.similarity_search(query, k=4)

        if not docs:
            return (
                "No relevant content found in the knowledge base for this query. "
                "Ask the student to upload study materials first."
            )

        results = []
        for doc in docs:
            source = doc.metadata.get("source", "Unknown document")
            page   = doc.metadata.get("page", "N/A")
            results.append(
                f"[Source: {source} | Page: {page}]\n{doc.page_content}"
            )

        return "\n\n" + ("─" * 60) + "\n\n".join(results)

    except FileNotFoundError:
        return (
            "The knowledge base is empty. Please upload at least one "
            "study document (PDF, DOCX, TXT, or PPTX) before asking questions."
        )
    except Exception as exc:
        return f"Knowledge base search failed: {exc}"


retriever_agent = Agent(
    role="Academic Knowledge Retriever",
    goal=(
        "Find the most relevant academic content from the student's "
        "uploaded study materials for any given query."
    ),
    backstory=(
        "You are a specialist academic librarian trained in semantic "
        "information retrieval. You excel at understanding student queries, "
        "decomposing complex questions, and surfacing the most pertinent "
        "passages from uploaded course materials."
    ),
    tools=[retrieve_tool],
    llm=get_llm(),
    verbose=True,
    allow_delegation=False,
    max_iter=30,             
    max_execution_time=120
)