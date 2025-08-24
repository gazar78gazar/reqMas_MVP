import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if API key is loaded
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("ERROR: OPENAI_API_KEY not found in .env file")
    sys.exit(1)

print(f"[OK] API Key loaded (starts with: {api_key[:7]}...)")

from src.state.simple_state import SimpleState
from src.agents.agent_factory import create_agents

print("\n=== TESTING LLM INTEGRATION ===\n")

# Initialize
state = SimpleState(session_id="llm_test")
agents = create_agents("llm_test")

# Test 1: Generate questions with LLM
print("1. Testing LLM Question Generation:")
questions = agents['elicitor'].get_next_questions(state)
print(f"   Generated {len(questions)} questions")
for i, q in enumerate(questions[:3], 1):
    print(f"   {i}. {q}")

# Test 2: Parse natural language answer
if hasattr(agents['elicitor'], 'llm') and agents['elicitor'].llm:
    print("\n2. Testing Answer Parsing:")
    test_answer = "I think we need about 8 inputs, maybe 10 if we add the safety sensors"
    parsed = agents['elicitor'].llm.parse_answer(
        "How many digital inputs do you need?",
        test_answer
    )
    print(f"   Original: '{test_answer}'")
    print(f"   Parsed: '{parsed.get('parsed_value')}'")
    print(f"   Confidence: {parsed.get('confidence', 0):.1%}")
    print(f"   Needs clarification: {parsed.get('needs_clarification')}")

print("\n[SUCCESS] LLM Integration successful!")