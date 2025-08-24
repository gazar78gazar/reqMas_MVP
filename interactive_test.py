import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.state.simple_state import SimpleState
from src.agents.agent_factory import create_agents
from src.agents.orchestrator import Orchestrator
from src.logging.decision_logger import DecisionLogger
import uuid

def interactive_session():
    """Interactive session where you play the user"""
    
    print("\n" + "="*60)
    print("INTERACTIVE REQUIREMENT ELICITATION SESSION")
    print("="*60)
    print("\nYou are a user needing an IoT solution.")
    print("Answer the questions as a real user would.")
    print("Type 'skip' to skip a question, 'quit' to end.\n")
    
    # Initialize
    session_id = str(uuid.uuid4())
    state = SimpleState(session_id=session_id)
    agents = create_agents(session_id)
    logger = DecisionLogger(session_id)
    orchestrator = Orchestrator(logger)
    
    iteration = 0
    
    while iteration < 3:
        iteration += 1
        
        # Get questions
        questions = agents['elicitor'].get_next_questions(state)
        
        if not questions:
            print("No more questions!")
            break
        
        print(f"\n--- Round {iteration} ({len(questions)} questions) ---\n")
        
        answers = {}
        for i, q in enumerate(questions, 1):
            print(f"Q{i}: {q}")
            answer = input("Your answer: ").strip()
            
            if answer.lower() == 'quit':
                print("Ending session...")
                return state
            elif answer.lower() == 'skip' or not answer:
                continue
            else:
                answers[q] = answer
        
        # Process answers
        if answers:
            state = agents['elicitor'].process_answers(answers, state)
            
            # Check completeness
            score = agents['completeness'].check_completeness(state)
            state.completeness_score = score
            
            print(f"\n📊 Completeness: {score:.1%}")
            
            if score >= 0.85:
                print("✅ Requirements complete!")
                
                # Validate
                result = agents['validator'].validate(state)
                print(f"🔍 Validation: {'PASSED' if result.is_valid else 'FAILED'}")
                break
            else:
                gaps = agents['completeness'].identify_gaps(state)
                print(f"📝 Still need info about: {', '.join(gaps[:3])}")
    
    # Final summary
    print(f"\n" + "="*60)
    print("SESSION SUMMARY")
    print("="*60)
    print(f"Requirements collected: {len(state.requirements)}")
    print(f"Final completeness: {state.completeness_score:.1%}")
    
    print("\nYour requirements:")
    for req in state.requirements:
        print(f"  [{req.category}] {req.answer}")
    
    print(f"\n📁 Full log: logs/sessions/{session_id}/decisions.jsonl")
    
    return state

if __name__ == "__main__":
    interactive_session()