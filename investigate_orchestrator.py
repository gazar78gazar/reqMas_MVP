import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.agents.orchestrator import Orchestrator
from src.state.simple_state import SimpleState
from src.logging.decision_logger import DecisionLogger
import inspect

logger = DecisionLogger("investigate")
orch = Orchestrator(logger)

print("=== ORCHESTRATOR INVESTIGATION ===\n")

# Check the route method implementation
print("1. ROUTE METHOD SOURCE CODE:")
print("-" * 50)
try:
    source = inspect.getsource(orch.route)
    for i, line in enumerate(source.split('\n'), 1):
        print(f"{i:3}: {line}")
except:
    print("Could not get source")

print("\n2. ROUTING LOGIC TESTS:")
print("-" * 50)

test_cases = [
    {"requirements": [], "completeness": 0.0, "iteration": 0, "expected": "elicitor"},
    {"requirements": ["some"], "completeness": 0.36, "iteration": 1, "expected": "elicitor"},
    {"requirements": ["some"], "completeness": 0.36, "iteration": 2, "expected": "elicitor"},
    {"requirements": ["some"], "completeness": 0.85, "iteration": 1, "expected": "validator"},  # FIXED THIS LINE
    {"requirements": ["some"], "completeness": 0.36, "iteration": 3, "expected": "END"},
]

for i, test in enumerate(test_cases, 1):
    state = SimpleState(session_id=f"test{i}")
    if test["requirements"]:
        from src.state.simple_state import RequirementEntry
        state.requirements = [RequirementEntry(category="test", question="test", answer="test")]
    state.completeness_score = test["completeness"]
    state.iteration_count = test["iteration"]
    
    result = orch.route(state)
    status = "✅" if result == test["expected"] else "❌"
    print(f"Test {i}: iter={test['iteration']}, comp={test['completeness']:.0%}, reqs={len(state.requirements)}")
    print(f"         Expected: {test['expected']}, Got: {result} {status}")