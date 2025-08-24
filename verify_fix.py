import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.state.simple_state import SimpleState, RequirementEntry
from src.agents.orchestrator import Orchestrator
from src.logging.decision_logger import DecisionLogger

print("=== VERIFY ORCHESTRATOR FIX ===\n")

logger = DecisionLogger("verify")
orchestrator = Orchestrator(logger)

# Test the new routing logic
state = SimpleState(session_id="verify")

# Scenario 1: Empty state
print("1. Empty state:")
route = orchestrator.route(state)
print(f"   Routes to: {route} ✓" if route == "elicitor" else f"   Routes to: {route} ✗")

# Scenario 2: Has requirements but completeness = 0.0
state.requirements = [
    RequirementEntry(category="I/O", question="Q1", answer="A1"),
    RequirementEntry(category="I/O", question="Q2", answer="A2"),
]
state.completeness_score = 0.0
print("\n2. Has 2 requirements, completeness = 0.0:")
route = orchestrator.route(state)
print(f"   Routes to: {route} ✓" if route == "completeness" else f"   Routes to: {route} ✗")

# Scenario 3: Has requirements, completeness = 0.5
state.completeness_score = 0.5
print("\n3. Has requirements, completeness = 50%:")
route = orchestrator.route(state)
print(f"   Routes to: {route} ✓" if route == "elicitor" else f"   Routes to: {route} ✗")

print("\n✅ Fix is working!" if route == "elicitor" else "\n❌ Something's wrong")