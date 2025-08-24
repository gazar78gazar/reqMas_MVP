import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import json
from src.agents.completeness import CompletenessChecker
from src.logging.decision_logger import DecisionLogger

logger = DecisionLogger("investigate")
checker = CompletenessChecker(logger)

print("=== COMPLETENESS CHECKER INVESTIGATION ===\n")

# Check if REQUIRED_FIELDS exists
if hasattr(checker, 'REQUIRED_FIELDS'):
    print("Required fields structure:")
    print(json.dumps(checker.REQUIRED_FIELDS, indent=2))
    
    # Count total required fields
    total = sum(len(fields) for fields in checker.REQUIRED_FIELDS.values())
    print(f"\nTotal required fields: {total}")
else:
    print("No REQUIRED_FIELDS attribute found")

# Try with empty state to see baseline
from src.state.simple_state import SimpleState, RequirementEntry
empty_state = SimpleState(session_id="test")
empty_score = checker.check_completeness(empty_state)
print(f"\nEmpty state score: {empty_score:.1%}")

# Try with one requirement
state_one = SimpleState(session_id="test")
state_one.requirements = [
    RequirementEntry(category="I/O", question="test", answer="test")
]
one_score = checker.check_completeness(state_one)
print(f"One requirement score: {one_score:.1%}")

# Try with two requirements
state_two = SimpleState(session_id="test")
state_two.requirements = [
    RequirementEntry(category="I/O", question="digital_inputs", answer="8"),
    RequirementEntry(category="Environment", question="temperature_range", answer="-10 to 50C")
]
two_score = checker.check_completeness(state_two)
print(f"Two requirements score: {two_score:.1%}")