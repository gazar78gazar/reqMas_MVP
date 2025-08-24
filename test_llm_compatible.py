import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.state.simple_state import SimpleState
from src.agents.agent_factory import create_agents
from src.agents.orchestrator import Orchestrator
from src.logging.decision_logger import DecisionLogger

print("=== COMPATIBLE LLM TEST ===\n")

def run_compatible_test():
    # Initialize
    session_id = "compatible"
    state = SimpleState(session_id=session_id)
    agents = create_agents(session_id)
    logger = DecisionLogger(session_id)
    orchestrator = Orchestrator(logger)
    
    print("Round 1: Get initial LLM questions")
    print("-" * 50)
    
    # Get questions from LLM
    questions = agents['elicitor'].get_next_questions(state)
    print(f"LLM generated {len(questions)} questions\n")
    
    # Create answers that match LLM's actual questions
    # We'll answer based on keywords in the questions
    answers = {}
    
    for i, q in enumerate(questions[:4], 1):
        print(f"Q{i}: {q}")
        
        q_lower = q.lower()
        
        # Smart answer generation based on question content
        if 'sensor' in q_lower or 'input' in q_lower:
            answer = "We need 16 digital inputs for various sensors"
        elif 'actuator' in q_lower or 'output' in q_lower:
            answer = "8 digital outputs for controlling actuators"
        elif 'temperature' in q_lower or 'environmental' in q_lower:
            answer = "Operating range from -20°C to +50°C"
        elif 'humidity' in q_lower:
            answer = "Up to 95% humidity, non-condensing"
        elif 'protocol' in q_lower or 'communication' in q_lower:
            answer = "Ethernet and Modbus TCP required"
        elif 'power' in q_lower or 'voltage' in q_lower:
            answer = "24VDC standard industrial power"
        elif 'latency' in q_lower or 'bandwidth' in q_lower:
            answer = "100ms maximum latency, 1Mbps minimum bandwidth"
        elif 'security' in q_lower or 'cybersecurity' in q_lower:
            answer = "Need encryption and secure authentication"
        elif 'ip rating' in q_lower or 'enclosure' in q_lower:
            answer = "IP65 rating for outdoor installation"
        else:
            answer = "Standard industrial requirements"
        
        answers[q] = answer
        print(f"A: {answer}\n")
    
    # Process answers
    state = agents['elicitor'].process_answers(answers, state)
    
    # Check what was stored
    print("\nStored Requirements:")
    print("-" * 50)
    for req in state.requirements:
        print(f"[{req.category}] Q: {req.question[:50]}...")
        print(f"           A: {req.answer}")
    
    # Check completeness
    score = agents['completeness'].check_completeness(state)
    state.completeness_score = score
    
    print(f"\nCompleteness: {score:.1%}")
    
    # Round 2: Get follow-up questions
    print("\nRound 2: Follow-up questions based on context")
    print("-" * 50)
    
    questions2 = agents['elicitor'].get_next_questions(state)
    print(f"LLM generated {len(questions2)} follow-up questions\n")
    
    for i, q in enumerate(questions2[:2], 1):
        print(f"Q{i}: {q}")
    
    return state

# Run test
final_state = run_compatible_test()

# Summary
print("\n" + "="*60)
print("TEST SUMMARY")
print("="*60)
print(f"✅ Questions generated: Dynamic from LLM")
print(f"✅ Answers processed: {len(final_state.requirements)}")
print(f"📊 Completeness: {final_state.completeness_score:.1%}")

if final_state.completeness_score > 0:
    print("\n✅ SYSTEM WORKING WITH LLM!")
else:
    print("\n⚠️ Completeness still 0% - check field matching")