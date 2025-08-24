import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.agents.completeness import CompletenessChecker
from src.state.simple_state import SimpleState, RequirementEntry
from src.logging.decision_logger import DecisionLogger

print("=== DEEP DEBUG COMPLETENESS ===\n")

logger = DecisionLogger("debug")
checker = CompletenessChecker(logger)

# Create test state
state = SimpleState(session_id="debug")
state.requirements = [
    RequirementEntry(category="I/O", question="How many digital inputs do you need?", answer="16"),
    RequirementEntry(category="I/O", question="How many digital outputs do you need?", answer="8"),
]

print("1. CHECK REQUIRED_FIELDS:")
print("-" * 40)
if hasattr(checker, 'REQUIRED_FIELDS'):
    print(f"REQUIRED_FIELDS exists: {checker.REQUIRED_FIELDS}")
    total = sum(len(fields) for fields in checker.REQUIRED_FIELDS.values())
    print(f"Total required fields: {total}")
else:
    print("NO REQUIRED_FIELDS!")

print("\n2. TEST MATCHING LOGIC:")
print("-" * 40)

# Test the matching manually
QUESTION_TO_FIELD = {
    "digital inputs": "digital_inputs",
    "digital outputs": "digital_outputs",
    "temperature": "temperature_range",
}

answered_fields = set()
for req in state.requirements:
    print(f"\nQuestion: '{req.question}'")
    print(f"Answer: '{req.answer}'")
    
    if req.answer:
        question_lower = req.question.lower()
        print(f"Lowercase: '{question_lower}'")
        
        for key_phrase, field in QUESTION_TO_FIELD.items():
            if key_phrase in question_lower:
                print(f"  ✓ Matched '{key_phrase}' → field '{field}'")
                answered_fields.add(field)
                break
        else:
            print(f"  ✗ No match found")

print(f"\nAnswered fields: {answered_fields}")
print(f"Count: {len(answered_fields)}")

print("\n3. CALL THE ACTUAL METHOD:")
print("-" * 40)

# Call the real method
score = checker.check_completeness(state)
print(f"Returned score: {score:.1%}")
print(f"State score: {state.completeness_score:.1%}")

print("\n4. CHECK THE LOG:")
print("-" * 40)
# Check what was logged
log_path = f"logs/sessions/debug/decisions.jsonl"
if os.path.exists(log_path):
    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        if lines:
            import json
            last_log = json.loads(lines[-1])
            print(f"Last log entry:")
            print(f"  Reasoning: {last_log.get('reasoning', 'N/A')}")