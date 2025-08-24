import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

print("=== DEBUG OUTDOOR SCENARIO ===\n")

# Check what's in the outdoor_responses dictionary
outdoor_responses = {
    "How many digital inputs do you need?": "16",
    "How many digital outputs do you need?": "8",
    "What is the operating temperature range?": "-40 to 85 Celsius",
    "Is this an indoor or outdoor installation?": "Outdoor, exposed to weather",
    "What communication protocols do you need (Ethernet, Modbus, Profibus, etc.)?": "EtherNet/IP",
    "What is your available power supply voltage (24VDC, 120VAC, 240VAC)?": "110VAC",
    "Do you need analog inputs? If yes, how many and what type (0-10V, 4-20mA)?": "Yes, 8 channels 0-10V",
    "What is the humidity level (normal, high, condensing)?": "High, condensing possible",
    "Are there vibration or shock requirements?": "Yes, heavy machinery nearby",
    "Do you need battery backup or UPS support?": "Yes, 4 hours minimum"
}

print(f"Total answers available: {len(outdoor_responses)}\n")

# Simulate what happens
from src.state.simple_state import SimpleState
from src.agents.agent_factory import create_agents

state = SimpleState(session_id="outdoor_debug")
agents = create_agents("outdoor_debug")

# Get first batch of questions
questions_batch1 = agents['elicitor'].get_next_questions(state)
print("ITERATION 1 - Questions asked:")
for i, q in enumerate(questions_batch1, 1):
    print(f"  {i}. {q[:60]}...")

print("\nMatching with available answers:")
matched1 = 0
for q in questions_batch1:
    if q in outdoor_responses:
        print(f"  ✓ MATCH: {q[:40]}...")
        matched1 += 1
    else:
        print(f"  ✗ NO MATCH: {q[:40]}...")
        # Show why it doesn't match
        for key in outdoor_responses.keys():
            if q[:20].lower() in key.lower():
                print(f"     Close but different: '{key[:40]}...'")

print(f"\nIteration 1: {matched1} questions can be answered")

# Process first batch
answers1 = {q: outdoor_responses[q] for q in questions_batch1 if q in outdoor_responses}
state = agents['elicitor'].process_answers(answers1, state)

# Get second batch
questions_batch2 = agents['elicitor'].get_next_questions(state)
print("\nITERATION 3 - Questions asked:")
for i, q in enumerate(questions_batch2[:4], 1):
    print(f"  {i}. {q[:60]}...")

matched2 = 0
for q in questions_batch2[:4]:
    if q in outdoor_responses:
        print(f"  ✓ MATCH: {q[:40]}...")
        matched2 += 1
    else:
        print(f"  ✗ NO MATCH: {q[:40]}...")

print(f"\nIteration 3: {matched2} questions can be answered")
print(f"TOTAL: {matched1 + matched2} questions answered out of 10 available")