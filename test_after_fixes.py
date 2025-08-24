import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.state.simple_state import SimpleState
from src.agents.agent_factory import create_agents
import uuid

print("=== QUICK SMOKE TEST AFTER FIXES ===\n")

# Initialize
session_id = str(uuid.uuid4())
state = SimpleState(session_id=session_id)
agents = create_agents(session_id)

# Test 1: Questions from all categories?
print("1. QUESTION DIVERSITY TEST")
questions = agents['elicitor'].get_next_questions(state)
print(f"   Got {len(questions)} questions (should be 8)")

categories = {"I/O": 0, "Environment": 0, "Communication": 0, "Power": 0}
for q in questions:
    q_lower = q.lower()
    if 'input' in q_lower or 'output' in q_lower or 'i/o' in q_lower or 'distance' in q_lower:
        categories["I/O"] += 1
    elif 'temperature' in q_lower or 'humidity' in q_lower or 'indoor' in q_lower or 'outdoor' in q_lower or 'environment' in q_lower:
        categories["Environment"] += 1
    elif 'protocol' in q_lower or 'network' in q_lower or 'communication' in q_lower or 'ethernet' in q_lower:
        categories["Communication"] += 1
    elif 'voltage' in q_lower or 'power' in q_lower or 'consumption' in q_lower or 'battery' in q_lower:
        categories["Power"] += 1

print(f"   Categories covered: {[k for k,v in categories.items() if v > 0]}")
print(f"   Questions per category: {categories}")

# Test 2: Completeness calculation working?
print("\n2. COMPLETENESS CALCULATION TEST")
test_answers = {}
if len(questions) >= 4:
    test_answers = {
        questions[0]: "8",
        questions[1]: "4", 
        questions[2]: "-10 to 50C",
        questions[3]: "24V DC"
    }

state = agents['elicitor'].process_answers(test_answers, state)
score = agents['completeness'].check_completeness(state)  # <- FIXED LINE
print(f"   After 4 answers: {score:.1%} (should be ~19%)")

# Test 3: Can reach 85%?
print("\n3. HIGH COMPLETENESS TEST")
# Answer most questions
for i, q in enumerate(questions):
    if q not in test_answers:
        test_answers[q] = f"Answer {i}"

state2 = SimpleState(session_id="test2")
state2 = agents['elicitor'].process_answers(test_answers, state2)
score2 = agents['completeness'].check_completeness(state2)  # <- FIXED LINE
print(f"   After {len(test_answers)} answers: {score2:.1%}")

# Show what was stored
print(f"\n4. STORED REQUIREMENTS")
print(f"   Total stored: {len(state2.requirements)}")
for req in state2.requirements[:5]:
    print(f"   [{req.category}] {req.question[:40]}... = {req.answer}")

print("\n✅ Smoke test complete!")