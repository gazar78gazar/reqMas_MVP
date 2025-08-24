import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.state.simple_state import SimpleState, RequirementEntry
from src.agents.agent_factory import create_agents
from src.agents.orchestrator import Orchestrator
from src.logging.decision_logger import DecisionLogger

print("=== SIMULATION FLOW INVESTIGATION ===\n")

# Recreate what happens in simulation
session_id = "test"
state = SimpleState(session_id=session_id)
agents = create_agents(session_id)
logger = DecisionLogger(session_id)
orchestrator = Orchestrator(logger)

print("ITERATION 1:")
print("-" * 40)
print("Starting with empty state...")

# What does orchestrator say with empty state?
next_agent = orchestrator.route(state)
print(f"Empty state → Orchestrator routes to: {next_agent}")

# After first round of questions (simulate what happens)
state.requirements = [
    RequirementEntry(category="I/O", question="q1", answer="a1"),
    RequirementEntry(category="I/O", question="q2", answer="a2"),
    RequirementEntry(category="Environment", question="q3", answer="a3"),
    RequirementEntry(category="Environment", question="q4", answer="a4"),
]
print(f"After answering: {len(state.requirements)} requirements")

# Check completeness
score = agents['completeness'].check_completeness(state)
state.completeness_score = score
print(f"Completeness: {score:.1%}")

# What does orchestrator say now?
state.iteration_count = 1
next_agent = orchestrator.route(state)
print(f"With {score:.1%} complete → Orchestrator routes to: {next_agent}")

print("\nITERATION 2:")
print("-" * 40)
state.iteration_count = 2
print(f"State: {len(state.requirements)} reqs, {state.completeness_score:.1%} complete, iter {state.iteration_count}")
next_agent = orchestrator.route(state)
print(f"Orchestrator routes to: {next_agent}")

# If it routes to completeness, what happens?
if next_agent == "completeness":
    print("\nSimulating completeness agent...")
    score = agents['completeness'].check_completeness(state)
    print(f"Completeness still: {score:.1%}")
    print("But then what? Does it go back to elicitor?")

print("\nITERATION 3:")
print("-" * 40)  
state.iteration_count = 3
print(f"State: {len(state.requirements)} reqs, {state.completeness_score:.1%} complete, iter {state.iteration_count}")
next_agent = orchestrator.route(state)
print(f"Orchestrator routes to: {next_agent}")

print("\n" + "="*50)
print("ANALYSIS:")
print("If stuck at 'completeness', the orchestrator routing logic is wrong.")
print("It should route back to 'elicitor' when < 85% complete.")