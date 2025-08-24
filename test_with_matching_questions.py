import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.state.simple_state import SimpleState, RequirementEntry
from src.agents.agent_factory import create_agents
from src.agents.orchestrator import Orchestrator
from src.logging.decision_logger import DecisionLogger

print("=== TEST WITH PROPERLY MATCHING QUESTIONS ===\n")

session_id = "test"
state = SimpleState(session_id=session_id)
agents = create_agents(session_id)
orchestrator = Orchestrator(DecisionLogger(session_id))

# Add requirements with questions that WILL match the key phrases
matching_requirements = [
    RequirementEntry(category="I/O", question="How many digital inputs do you need?", answer="16"),
    RequirementEntry(category="I/O", question="How many digital outputs required?", answer="8"),
    RequirementEntry(category="I/O", question="Do you need analog inputs?", answer="Yes, 4"),
    RequirementEntry(category="I/O", question="Need analog outputs?", answer="No"),
    RequirementEntry(category="Environment", question="What temperature range?", answer="-40 to 85C"),
    RequirementEntry(category="Environment", question="Is this indoor or outdoor?", answer="Outdoor"),
    RequirementEntry(category="Environment", question="What's the humidity level?", answer="High"),
    RequirementEntry(category="Communication", question="What communication protocol?", answer="Ethernet"),
    RequirementEntry(category="Communication", question="Need remote access?", answer="Yes"),
    RequirementEntry(category="Power", question="What's the power supply voltage?", answer="24VDC"),
    RequirementEntry(category="Power", question="What's your power budget?", answer="100W"),
]

# Test with increasing requirements
for i in range(1, len(matching_requirements) + 1):
    state.requirements = matching_requirements[:i]
    
    # Check completeness
    score = agents['completeness'].check_completeness(state)
    state.completeness_score = score
    
    # Check routing
    state.iteration_count = 1
    next_route = orchestrator.route(state)
    
    status = "→ VALIDATOR! ✅" if next_route == "validator" else f"→ {next_route}"
    print(f"{i:2} requirements: {score:6.1%} {status}")
    
    if score >= 0.85:
        print(f"\n🎉 REACHED 85% with {i} requirements!")
        break