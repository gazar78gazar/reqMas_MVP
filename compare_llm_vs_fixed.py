import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.state.simple_state import SimpleState
from src.agents.agent_factory import create_agents

print("=== COMPARE LLM vs FIXED QUESTIONS ===\n")

# Test with LLM
print("WITH LLM:")
print("-" * 40)
state_llm = SimpleState(session_id="with_llm")
agents_llm = create_agents("with_llm")

if hasattr(agents_llm['elicitor'], 'use_llm'):
    agents_llm['elicitor'].use_llm = True
    
questions_llm = agents_llm['elicitor'].get_next_questions(state_llm)
print(f"Generated {len(questions_llm)} questions")
for i, q in enumerate(questions_llm[:3], 1):
    print(f"  {i}. {q}")

# Test without LLM (force fixed)
print("\nWITHOUT LLM (Fixed):")
print("-" * 40)
state_fixed = SimpleState(session_id="fixed")
agents_fixed = create_agents("fixed")

if hasattr(agents_fixed['elicitor'], 'use_llm'):
    agents_fixed['elicitor'].use_llm = False
    
questions_fixed = agents_fixed['elicitor'].get_next_questions(state_fixed)
print(f"Generated {len(questions_fixed)} questions")
for i, q in enumerate(questions_fixed[:3], 1):
    print(f"  {i}. {q}")

print("\nCOMPARISON:")
print("-" * 40)
if questions_llm != questions_fixed:
    print("✅ Questions are DIFFERENT - LLM is generating dynamic content!")
else:
    print("⚠️ Questions are IDENTICAL - might be falling back to fixed")