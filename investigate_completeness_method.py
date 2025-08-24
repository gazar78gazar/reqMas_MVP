# investigate_completeness_method.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.agents.completeness import CompletenessChecker
from src.state.simple_state import SimpleState, RequirementEntry
from src.logging.decision_logger import DecisionLogger
import inspect

logger = DecisionLogger("debug")
checker = CompletenessChecker(logger)

print("=== COMPLETENESS METHOD INVESTIGATION ===\n")

# Show the check_completeness method source
print("1. CHECK_COMPLETENESS METHOD:")
print("-" * 50)
try:
    source = inspect.getsource(checker.check_completeness)
    for i, line in enumerate(source.split('\n')[:40], 1):
        print(f"{i:3}: {line}")
except:
    print("Could not get source")

print("\n2. TESTING WITH DIFFERENT REQUIREMENTS:")
print("-" * 50)

# Test 1: Requirements with matching questions
state1 = SimpleState(session_id="test1")
state1.requirements = [
    RequirementEntry(category="I/O", question="How many digital inputs do you need?", answer="8"),
    RequirementEntry(category="I/O", question="How many digital outputs do you need?", answer="4"),
]
score1 = checker.check_completeness(state1)
print(f"Test 1 - Real questions: {score1:.1%}")

# Test 2: Requirements with non-matching questions  
state2 = SimpleState(session_id="test2")
state2.requirements = [
    RequirementEntry(category="I/O", question="q1", answer="a1"),
    RequirementEntry(category="I/O", question="q2", answer="a2"),
]
score2 = checker.check_completeness(state2)
print(f"Test 2 - Fake questions: {score2:.1%}")

# Test 3: Check if it's looking for specific field names
print("\n3. CHECKING WHAT IT'S LOOKING FOR:")
print("-" * 50)

if hasattr(checker, 'REQUIRED_FIELDS'):
    print("Has REQUIRED_FIELDS:")
    print(checker.REQUIRED_FIELDS)
    
if hasattr(checker, 'QUESTION_TO_FIELD'):
    print("Has QUESTION_TO_FIELD mapping:")
    for q, f in list(checker.QUESTION_TO_FIELD.items())[:3]:
        print(f"  '{q}' -> '{f}'")