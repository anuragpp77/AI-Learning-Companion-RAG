"""
backend/agents/planner.py
──────────────────────────
FIX (original bug #7):
  • Old code: planner was added to the Crew but assigned zero tasks —
              it consumed memory and did absolutely nothing.
  • New code: the planner receives a real task in crew.py that analyzes
              the query and outputs a structured teaching plan that all
              downstream agents use as context.

FIX (original bug #2):
  • Agent now receives llm=get_llm() explicitly.
"""

from crewai import Agent
from backend.core.llm import get_llm


planner = Agent(
    role="Adaptive Learning Planner",
    goal=(
        "Analyze each student query and design a personalised teaching "
        "plan that accounts for difficulty mode, preferred language, and "
        "the student's known weak topics."
    ),
    backstory=(
        "You are an experienced curriculum designer and academic coach. "
        "You understand how students learn and can quickly assess what "
        "approach will be most effective — whether that's a simple analogy, "
        "a step-by-step breakdown, an exam-style structured answer, or a "
        "quiz. You also know how to adapt content for different languages "
        "without losing academic rigour."
    ),
    llm=get_llm(),
    verbose=True,
    allow_delegation=False,
)
