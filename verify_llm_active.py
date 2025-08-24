import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from dotenv import load_dotenv

print("=== VERIFY LLM INTEGRATION STATUS ===\n")

# Check environment
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    print(f"✅ API Key found: {api_key[:10]}...")
else:
    print("❌ No API key found")

# Check if LLM service loads
try:
    from src.llm.openai_service import OpenAIService
    from src.logging.decision_logger import DecisionLogger
    
    logger = DecisionLogger("verify")
    service = OpenAIService(logger)
    print("✅ OpenAI service initialized")
    
    # Test a simple call
    test_state = {"requirements": [], "completeness_score": 0.0}
    questions = service.generate_questions(test_state)
    print(f"✅ Generated {len(questions)} questions dynamically")
    
except Exception as e:
    print(f"❌ LLM service error: {e}")

# Check if elicitor uses LLM
from src.agents.agent_factory import create_agents
from src.state.simple_state import SimpleState

state = SimpleState(session_id="verify")
agents = create_agents("verify")

if hasattr(agents['elicitor'], 'use_llm'):
    print(f"✅ Elicitor LLM mode: {agents['elicitor'].use_llm}")
else:
    print("❌ Elicitor doesn't have LLM integration")