import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.agents.validator import ConstraintValidator
from src.state.simple_state import SimpleState, RequirementEntry
from src.logging.decision_logger import DecisionLogger
import json

logger = DecisionLogger("investigate")
validator = ConstraintValidator(logger)

print("=== VALIDATOR INVESTIGATION ===\n")

# Check if it loads constraints from JSON
if hasattr(validator, 'constraints'):
    print(f"Constraints loaded: {len(validator.constraints)}")
else:
    print("No constraints attribute")

# Check if constraints.json exists
constraints_path = "data/constraints.json"
if os.path.exists(constraints_path):
    print(f"✓ constraints.json exists at {constraints_path}")
    with open(constraints_path, 'r') as f:
        data = json.load(f)
    print(f"  Contains {len(data)} entries")
    if isinstance(data, dict):
        print(f"  Keys: {list(data.keys())[:5]}...")
    elif isinstance(data, list) and len(data) > 0:
        print(f"  First entry: {data[0]}")
else:
    print("✗ No constraints.json found")

# Test validation with minimal requirements
print("\n--- Testing validation ---")
state = SimpleState(session_id="test")
state.requirements = [
    RequirementEntry(category="I/O", question="inputs", answer="1000")  # Unrealistic
]

result = validator.validate(state)
print(f"Validation result: {result.is_valid}")
if hasattr(result, 'violations') and result.violations:
    print(f"Violations: {result.violations}")
if hasattr(result, 'warnings') and result.warnings:
    print(f"Warnings: {result.warnings}")

# Test with normal values
state2 = SimpleState(session_id="test2")
state2.requirements = [
    RequirementEntry(category="I/O", question="digital_inputs", answer="8"),
    RequirementEntry(category="Environment", question="temperature", answer="-10 to 50C")
]
result2 = validator.validate(state2)
print(f"\nNormal values validation: {result2.is_valid}")