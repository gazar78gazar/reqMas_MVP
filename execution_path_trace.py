import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.state.simple_state import SimpleState
from src.agents.agent_factory import create_agents
from src.agents.orchestrator import Orchestrator
from src.logging.decision_logger import DecisionLogger

print("=== ACTUAL EXECUTION PATH ===\n")

# Initialize exactly like simulation
session_id = "execution_trace"
state = SimpleState(session_id=session_id)
agents = create_agents(session_id)
logger = DecisionLogger(session_id)
orchestrator = Orchestrator(logger)

# Track execution
execution_log = []

# Iteration 1
state.iteration_count = 0
next_agent = orchestrator.route(state)
execution_log.append(f"Iter 0, Score {state.completeness_score:.1%} → Route to '{next_agent}'")

# Simulate elicitor processing
if next_agent == "elicitor":
    # Process some answers
    from src.state.simple_state import RequirementEntry
    state.requirements = [
        RequirementEntry(category="I/O", question="Q1", answer="A1"),
        RequirementEntry(category="I/O", question="Q2", answer="A2"),
    ]
    execution_log.append(f"  Elicitor: Added {len(state.requirements)} requirements")
    execution_log.append(f"  Completeness after elicitor: {state.completeness_score:.1%}")

# Iteration 2
state.iteration_count = 1
next_agent = orchestrator.route(state)
execution_log.append(f"Iter 1, Score {state.completeness_score:.1%} → Route to '{next_agent}'")

# What happens next?
if next_agent == "elicitor":
    execution_log.append("  → Goes to elicitor AGAIN (completeness never checked!)")
elif next_agent == "completeness":
    execution_log.append("  → Goes to completeness (will check score)")

# Print execution path
print("Execution Path:")
for entry in execution_log:
    print(entry)

print("\n" + "="*50)
print("CONCLUSION:")
if state.completeness_score == 0.0:
    print("❌ Completeness score is STILL 0.0!")
    print("   The score is never calculated in the normal flow!")
else:
    print("✅ Completeness score was updated")