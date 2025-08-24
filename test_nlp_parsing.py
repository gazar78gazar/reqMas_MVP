import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.state.simple_state import SimpleState
from src.agents.agent_factory import create_agents

print("=== TEST NATURAL LANGUAGE PARSING ===\n")

state = SimpleState(session_id="nlp_test")
agents = create_agents("nlp_test")

# Test various natural language answers
test_cases = [
    ("How many digital inputs?", "I think around 8 or maybe 10"),
    ("What's the temperature range?", "It gets pretty hot, like 50 degrees celsius in summer"),
    ("Power requirements?", "standard industrial power, you know, the usual 24 volts DC"),
    ("Installation environment?", "it's going to be outside but we'll put a roof over it"),
    ("Network protocol?", "We use ethernet for everything, sometimes modbus for old equipment"),
]

print("Testing natural language understanding:")
print("-" * 50)

for question, answer in test_cases:
    print(f"\nQ: {question}")
    print(f"User said: '{answer}'")
    
    # Process through LLM
    if hasattr(agents['elicitor'], 'llm') and agents['elicitor'].llm:
        parsed = agents['elicitor'].llm.parse_answer(question, answer)
        print(f"  Parsed: '{parsed.get('parsed_value')}'")
        print(f"  Category: {parsed.get('category')}")
        print(f"  Confidence: {parsed.get('confidence', 0):.0%}")
        if parsed.get('needs_clarification'):
            print(f"  ⚠️ Needs clarification: {parsed.get('clarification_question', '')}")
    else:
        print("  ❌ No LLM parser available")