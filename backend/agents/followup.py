"""
backend/agents/followup.py
───────────────────────────
NEW agent (recommended in the review).

After the teacher responds, this agent generates 3 follow-up questions
to guide the student deeper into the topic — simulating the "what should
I ask next?" nudge of a real tutor.
"""

from crewai import Agent
from backend.core.llm import get_llm


followup_agent = Agent(
    role="Socratic Follow-up Generator",
    goal=(
        "Generate 3 insightful follow-up questions that deepen the "
        "student's understanding of the topic they just asked about."
    ),
    backstory=(
        "You are a Socratic tutor who believes the best learning happens "
        "through guided inquiry. After a student receives an answer, you "
        "identify the natural next questions — filling gaps, exploring edge "
        "cases, and connecting this topic to related concepts. Your questions "
        "are specific, thought-provoking, and graded from easier to harder."
    ),
    llm=get_llm(),
    verbose=True,
    allow_delegation=False,
)
