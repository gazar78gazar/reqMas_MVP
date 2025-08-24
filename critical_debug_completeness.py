import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.agents.completeness import CompletenessChecker
from src.state.simple_state import SimpleState, RequirementEntry
from src.logging.decision_logger import DecisionLogger
import inspect

print("=== CRITICAL COMPLETENESS DEBUG ===\n")

logger = DecisionLogger("debug")
checker = CompletenessChecker(logger)

# Create state with REAL questions that should match
state = SimpleState(session_id="debug")
state.requirements = [
    RequirementEntry(category="I/O", question="How many digital inputs do you need?", answer="8"),
    RequirementEntry(category="I/O", question="How many digital outputs do you need?", answer="4"),
    RequirementEntry(category="Environment", question="What is the operating temperature range?", answer="-10 to 50C"),
]

print("TEST 1: With real questions")
print("-" * 40)
print(f"Requirements: {len(state.requirements)}")
for req in state.requirements:
    print(f"  - {req.question[:50]}: {req.answer}")

score = checker.check_completeness(state)
print(f"\nCompleteness: {score:.1%}")
print(f"State score: {state.completeness_score:.1%}")

print("\n" + "="*50)

# Test with fake questions
state2 = SimpleState(session_id="debug2")
state2.requirements = [
    RequirementEntry(category="Test", question=f"Question {i}", answer=f"Answer {i}")
    for i in range(1, 6)
]

print("TEST 2: With fake questions")
print("-" * 40)
print(f"Requirements: {len(state2.requirements)}")

score2 = checker.check_completeness(state2)
print(f"Completeness: {score2:.1%}")

print("\n" + "="*50)
print("CHECKING THE METHOD:")
print("-" * 40)

# Show first 20 lines of the method
source = inspect.getsource(checker.check_completeness)
for i, line in enumerate(source.split('\n')[:20], 1):
    print(f"{i:3}: {line}")

# Check what REQUIRED_FIELDS contains
if hasattr(checker, 'REQUIRED_FIELDS'):
    print(f"\nREQUIRED_FIELDS: {checker.REQUIRED_FIELDS}")
    total = sum(len(fields) for fields in checker.REQUIRED_FIELDS.values())
    print(f"Total required fields: {total}")