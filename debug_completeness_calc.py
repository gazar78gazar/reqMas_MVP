# debug_completeness_calc.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.agents.completeness import CompletenessChecker
from src.state.simple_state import SimpleState, RequirementEntry
from src.logging.decision_logger import DecisionLogger

logger = DecisionLogger("debug")
checker = CompletenessChecker(logger)

state = SimpleState(session_id="debug")
state.requirements = [
    RequirementEntry(category="I/O", question="q1", answer="a1"),
    RequirementEntry(category="I/O", question="q2", answer="a2"),
    RequirementEntry(category="Environment", question="q3", answer="a3"),
    RequirementEntry(category="Environment", question="q4", answer="a4"),
]

print(f"Requirements: {len(state.requirements)}")

# Check what the calculation does
score = checker.check_completeness(state)
print(f"Completeness: {score:.1%}")

# Check if it's looking at CATEGORY_QUESTIONS
if hasattr(checker, 'CATEGORY_QUESTIONS'):
    total = sum(len(qs) for qs in checker.CATEGORY_QUESTIONS.values())
    print(f"Total questions available: {total}")
    simple_score = len(state.requirements) / total if total > 0 else 0
    print(f"Simple calculation would be: {simple_score:.1%}")