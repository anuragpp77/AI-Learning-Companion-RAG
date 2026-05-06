"""
backend/agents/evaluator.py
────────────────────────────
FIX (original bug #7):
  • Old code: evaluator was in the Crew but had no task — it did nothing.
  • New code: evaluator receives a structured quiz-generation task in
              crew.py and produces parseable MCQ output.

FIX (original bug #2):
  • Agent now receives llm=get_llm() explicitly.
"""

from crewai import Agent
from backend.core.llm import get_llm


evaluator = Agent(
    role="Exam Question Designer",
    goal=(
        "Generate high-quality multiple choice questions that test "
        "genuine conceptual understanding, and evaluate student "
        "written answers against a reference context."
    ),
    backstory=(
        "You are a rigorous academic examiner with years of experience "
        "designing university-level assessments. You craft MCQs that go "
        "beyond rote memorisation — testing application, analysis, and "
        "synthesis. Your distractors are plausible but clearly wrong to "
        "a student who understands the material. You also provide concise, "
        "constructive feedback on student answers."
    ),
    llm=get_llm(),
    verbose=True,
    allow_delegation=False,
)
