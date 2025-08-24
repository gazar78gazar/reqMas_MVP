import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.state.simple_state import SimpleState, RequirementEntry
from src.agents.agent_factory import create_agents
from src.agents.orchestrator import Orchestrator
from src.logging.decision_logger import DecisionLogger

print("=== VALIDATE 85% THRESHOLD ===\n")

session_id = "validate"
state = SimpleState(session_id=session_id)
agents = create_agents(session_id)
orchestrator = Orchestrator(DecisionLogger(session_id))

# Add enough requirements to test different percentages
test_requirements = []
for i in range(1, 12):  # Add up to 11 requirements
    test_requirements.append(
        RequirementEntry(
            category="Test",
            question=f"Question {i}",
            answer=f"Answer {i}"
        )
    )
    
    # Test with i requirements
    state.requirements = test_requirements[:i]
    
    # Check completeness
    score = agents['completeness'].check_completeness(state)
    state.completeness_score = score
    
    # Check routing
    state.iteration_count = 1  # Avoid hitting max iterations
    next_route = orchestrator.route(state)
    
    print(f"{i:2} requirements: {score:5.1%} → routes to '{next_route}'")
    
    if next_route == "validator":
        print(f"\n✅ REACHES VALIDATOR at {score:.1%} with {i} requirements!")
        break

if next_route != "validator":
    print(f"\n❌ NEVER reached validator even with {len(test_requirements)} requirements")
    print("Issue is NOT just hard-coded matching!")