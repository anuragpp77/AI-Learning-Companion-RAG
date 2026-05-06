"""
backend/crew.py
"""

import json
import re

from crewai import Crew, Task, Process

from backend.agents.planner    import planner
from backend.agents.retriever  import retriever_agent
from backend.agents.summarizer import summarizer
from backend.agents.teacher    import teacher
from backend.agents.evaluator  import evaluator
from backend.agents.followup   import followup_agent
from backend.core.memory       import track_query, get_weak_topics


# ── Public entry points ───────────────────────────────────────────────────────

def run_crew(
    query:     str,
    mode:      str = "simple",
    language:  str = "English",
    task_type: str = "learn",
) -> dict:
    """
    Orchestrate the multi-agent pipeline for a student query.

    Args:
        query:      The student's question.
        mode:       "simple" (beginner) | "exam" (structured 10-mark answer).
        language:   "English" | "Malayalam" | any other language.
        task_type:  "learn" (explanation) | "quiz" (MCQ generation).

    Returns:
        {
          "response":      str,   # main answer or MCQs
          "followup":      list,  # 3 suggested next questions
          "sources":       list,  # source documents cited
          "weak_topics":   list,  # topics the student struggles with
        }
    """
    track_query(query)
    weak_topics = get_weak_topics(limit=3)
    weak_names  = [t["name"] for t in weak_topics]

    # ── Task 1: Plan ──────────────────────────────────────────────────────────
    plan_task = Task(
        description=f"""
        A student has asked the following question. Design a concise teaching plan.

        Question   : {query}
        Mode       : {mode}  (simple = beginner-friendly | exam = structured 10-mark answer)
        Language   : {language}
        Task type  : {task_type}  (learn = explain | quiz = generate MCQs)
        Weak topics: {', '.join(weak_names) if weak_names else 'None identified yet'}

        Output a 3-5 sentence teaching plan specifying:
        1. Which key sub-topics to cover
        2. The appropriate depth and complexity
        3. Whether to use analogies, diagrams descriptions, or worked examples
        4. Any language-specific considerations
        """,
        agent=planner,
        expected_output="A concise, actionable 3-5 sentence teaching plan.",
    )

    # ── Task 2: Retrieve ──────────────────────────────────────────────────────
    retrieve_task = Task(
        description=f"""
        Using the Search Knowledge Base tool, retrieve all relevant content
        for the following student query. Run multiple searches if needed to
        cover different angles of the topic.

        Query: {query}

        Return the raw retrieved passages with their source metadata intact.
        """,
        agent=retriever_agent,
        expected_output="Relevant text passages from the knowledge base, with source citations.",
        context=[plan_task],
    )

    # ── Task 3: Summarise ─────────────────────────────────────────────────────
    summarise_task = Task(
        description="""
        Synthesise the retrieved passages into a clean, coherent context block.

        - Remove duplicate or near-duplicate sentences
        - Preserve all key facts, definitions, and formulas
        - Organise logically (definitions → concepts → examples)
        - Keep a citation note for each piece of information (source + page)
        - Target length: 200-400 words
        """,
        agent=summarizer,
        expected_output="A well-structured 200-400 word summary with source notes.",
        context=[retrieve_task],
    )

    # ── Task 4a or 4b: Teach or Quiz ─────────────────────────────────────────
    lang_note = f" Respond entirely in {language}." if language != "English" else ""

    if task_type == "quiz":
        main_task = Task(
            description=f"""
            Generate exactly 5 multiple choice questions based on the summarised context.
            {lang_note}

            Each question MUST follow this exact format (no deviations):

            Q1: [Question text]
            A) [Option A]
            B) [Option B]
            C) [Option C]
            D) [Option D]
            Answer: [Letter only, e.g. B]
            Explanation: [One-sentence explanation of why this answer is correct]

            Requirements:
            - Questions should test understanding, not just recall
            - Distractors must be plausible
            - Vary difficulty: 2 easy, 2 medium, 1 hard
            - Topic: {query}
            """,
            agent=evaluator,
            expected_output="5 MCQs in the specified format.",
            context=[summarise_task, plan_task],
        )
        responding_agent = evaluator

    else:
        depth_instruction = (
            "Structure your answer with clear headings. Aim for 400-600 words, "
            "suitable for a 10-mark exam question. Include definitions, key points, "
            "and a conclusion."
            if mode == "exam"
            else
            "Explain in a friendly, conversational tone. Use a simple analogy "
            "to introduce the concept, then build up. Aim for 200-350 words."
        )

        main_task = Task(
            description=f"""
            Answer the student's question using the summarised context.{lang_note}

            Question   : {query}
            Instruction: {depth_instruction}

            Important rules:
            - Only use information from the summarised context
            - Cite sources inline like (Source: filename, p.N)
            - If the context lacks information, say so clearly and suggest
              what the student should look up
            - End with one key takeaway sentence
            """,
            agent=teacher,
            expected_output="A clear, well-structured educational answer with source citations.",
            context=[summarise_task, plan_task],
        )
        responding_agent = teacher

    # ── Task 5: Follow-up questions ───────────────────────────────────────────
    followup_task = Task(
        description=f"""
        Based on the answer just given about "{query}", generate exactly 3
        follow-up questions that will deepen the student's understanding.

        Rules:
        - Question 1: slightly easier (clarification or definition)
        - Question 2: same level (application or comparison)
        - Question 3: harder (analysis, synthesis, or edge case)
        - Each question must be a single sentence ending with "?"
        - Output ONLY a JSON array of 3 strings, e.g.:
          ["Question one?", "Question two?", "Question three?"]
        {lang_note}
        """,
        agent=followup_agent,
        expected_output='A JSON array of exactly 3 follow-up question strings.',
        context=[main_task],
    )

    # ── Assemble and run the Crew ─────────────────────────────────────────────
    # crew = Crew(
    #     agents=[planner, retriever_agent, summarizer, responding_agent, followup_agent],
    #     tasks=[plan_task, retrieve_task, summarise_task, main_task, followup_task],
    #     process=Process.sequential,
    #     verbose=True,
    # )

    ### To use the full crew with all agents, uncomment the above and comment out the simplified version below.
    
    crew = Crew(
    agents=[retriever_agent, responding_agent, followup_agent],
    tasks=[retrieve_task, main_task, followup_task],
    process=Process.sequential,
    verbose=True,
    )

    result = crew.kickoff()

    # Extract the last two task outputs
    main_output     = str(main_task.output.raw)     if main_task.output     else str(result)
    followup_output = str(followup_task.output.raw) if followup_task.output else "[]"

    # Parse follow-up questions (graceful fallback)
    followup_questions = _parse_followup(followup_output)

    # Extract source filenames mentioned in the answer
    sources = _extract_sources(main_output)

    return {
        "response":    main_output,
        "followup":    followup_questions,
        "sources":     sources,
        "weak_topics": weak_topics,
    }


def generate_flashcards(topic: str, context: str) -> list[dict]:
    """
    Standalone crew run that generates Anki-style flashcard pairs.

    Returns a list of {"question": ..., "answer": ...} dicts.
    """
    flash_task = Task(
        description=f"""
        Create 5 Anki-style flashcard pairs from the following context about "{topic}".

        Context:
        {context}

        Output ONLY a valid JSON array in this exact format:
        [
          {{"question": "...", "answer": "..."}},
          ...
        ]

        Rules:
        - Each question should be specific and unambiguous
        - Each answer should be 1-3 sentences
        - Cover different aspects of the topic
        - No markdown, no preamble — raw JSON only
        """,
        agent=evaluator,
        expected_output="A JSON array of 5 flashcard objects.",
    )

    crew   = Crew(agents=[evaluator], tasks=[flash_task], process=Process.sequential)
    result = crew.kickoff()
    raw    = str(flash_task.output.raw) if flash_task.output else str(result)

    return _parse_json_list(raw, default_key="question")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_followup(text: str) -> list[str]:
    """Try to parse a JSON array of strings; return a safe fallback on error."""
    # Strip markdown code fences if present
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return [str(q) for q in data[:3]]
    except (json.JSONDecodeError, ValueError):
        pass
    # Fallback: split by newline and grab lines that look like questions
    lines = [l.strip() for l in text.splitlines() if l.strip().endswith("?")]
    return lines[:3] if lines else []


def _parse_json_list(text: str, default_key: str = "question") -> list[dict]:
    """Parse a JSON list from LLM output, with fallback."""
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, ValueError):
        pass
    return []


def _extract_sources(text: str) -> list[str]:
    """Extract unique source filenames from inline citations like (Source: file.pdf, p.3)."""
    pattern = r"Source:\s*([^,\)]+)"
    matches = re.findall(pattern, text, re.IGNORECASE)
    return list(dict.fromkeys(m.strip() for m in matches))  # preserve order, deduplicate
