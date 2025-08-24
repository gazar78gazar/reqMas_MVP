# test_fixed_completeness.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.state.simple_state import SimpleState, RequirementEntry
from src.agents.agent_factory import create_agents

# Create state with 6 requirements (like simulation)
state = SimpleState(session_id="test")
agents = create_agents("test")

# Add 6 requirements
for i in range(6):
    state.requirements.append(
        RequirementEntry(
            category="Test",
            question=f"Question {i}",
            answer=f"Answer {i}"
        )
    )

print(f"Requirements: {len(state.requirements)}")
print(f"State completeness before: {state.completeness_score:.1%}")

# Call completeness checker
score = agents['completeness'].check_completeness(state)

print(f"Returned score: {score:.1%}")
print(f"State completeness after: {state.completeness_score:.1%}")

if score == 0.0:
    print("\n❌ COMPLETENESS STILL BROKEN!")
    print("The fix was not applied correctly.")
else:
    print(f"\n✅ COMPLETENESS WORKING! ({score:.1%})")