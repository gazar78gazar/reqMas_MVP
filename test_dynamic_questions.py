import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.state.simple_state import SimpleState, RequirementEntry
from src.agents.agent_factory import create_agents

print("=== TEST DYNAMIC QUESTION GENERATION ===\n")

# Initialize
state = SimpleState(session_id="dynamic_test")
agents = create_agents("dynamic_test")

print("ROUND 1 - Empty State:")
print("-" * 40)
questions1 = agents['elicitor'].get_next_questions(state)
print(f"Generated {len(questions1)} questions:")
for i, q in enumerate(questions1, 1):
    print(f"  {i}. {q}")

# Add some requirements
print("\nAdding requirements...")
state.requirements = [
    RequirementEntry(category="I/O", question="Digital inputs?", answer="16 inputs needed"),
    RequirementEntry(category="Environment", question="Temperature?", answer="Outdoor, -40 to 85C"),
]

print("\nROUND 2 - With Context:")
print("-" * 40)
questions2 = agents['elicitor'].get_next_questions(state)
print(f"Generated {len(questions2)} questions:")
for i, q in enumerate(questions2, 1):
    print(f"  {i}. {q}")

print("\nCOMPARISON:")
print("-" * 40)
# Check if questions changed based on context
overlap = set(questions1) & set(questions2)
print(f"Questions in both rounds: {len(overlap)}")
print(f"New contextual questions: {len(set(questions2) - set(questions1))}")

if len(overlap) < len(questions1):
    print("✅ Questions are DYNAMIC - they changed based on context!")
else:
    print("⚠️ Questions might be STATIC - same questions both times")