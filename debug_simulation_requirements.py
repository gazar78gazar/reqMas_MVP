import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.state.simple_state import SimpleState, RequirementEntry
from src.agents.agent_factory import create_agents

print("=== DEBUG SIMULATION REQUIREMENTS ===\n")

# Simulate what happens in the simulation
session_id = "test"
state = SimpleState(session_id=session_id)
agents = create_agents(session_id)

# Get questions that would be asked
questions = agents['elicitor'].get_next_questions(state)
print("Questions asked:")
for i, q in enumerate(questions[:4], 1):
    print(f"  {i}. {q}")

print("\n" + "-"*50)

# Simulate the answers from the outdoor scenario
test_answers = {
    "How many digital inputs do you need?": "16",
    "How many digital outputs do you need?": "8",
    "What is the operating temperature range?": "-40 to 85 Celsius",
    "Is this an indoor or outdoor installation?": "Outdoor, exposed to weather"
}

print("\nAnswers provided:")
for q, a in test_answers.items():
    print(f"  Q: {q[:40]}...")
    print(f"  A: {a}")

# Process answers
state = agents['elicitor'].process_answers(test_answers, state)

print("\n" + "-"*50)
print(f"\nStored {len(state.requirements)} requirements:")
for req in state.requirements:
    print(f"  [{req.category}] '{req.question}' = '{req.answer}'")

# Check completeness
score = agents['completeness'].check_completeness(state)
print(f"\nCompleteness: {score:.1%}")

# Check what's not matching
print("\n" + "-"*50)
print("MATCHING ANALYSIS:")

for req in state.requirements:
    question_lower = req.question.lower()
    matched = False
    
    # Check against the patterns
    patterns = ["digital inputs", "digital outputs", "temperature", "indoor or outdoor"]
    for pattern in patterns:
        if pattern in question_lower:
            print(f"  ✓ '{req.question[:30]}...' matches '{pattern}'")
            matched = True
            break
    
    if not matched:
        print(f"  ✗ '{req.question[:30]}...' NO MATCH")