import sys
import os
# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Run this to see the full flow working
from src.state.simple_state import SimpleState
from src.agents.orchestrator import Orchestrator
from src.agents.elicitor import RequirementsElicitor
from src.agents.completeness import CompletenessChecker
from src.agents.validator import ConstraintValidator
from src.agents.agent_factory import create_agents
from src.logging.decision_logger import DecisionLogger
import uuid

def run_manual_test():
    """Manually test the complete flow"""
    
    # Initialize
    session_id = str(uuid.uuid4())
    print(f"\n=== Starting Manual Test Session: {session_id} ===\n")
    
    state = SimpleState(session_id=session_id)
    agents = create_agents(session_id)
    logger = DecisionLogger(session_id)
    
    # Simulate user scenario
    print("SCENARIO: User needs temperature monitoring in warehouse")
    print("-" * 50)
    
    # Step 1: Elicitor generates questions
    print("\n1. ELICITOR - Getting questions...")
    questions = agents['elicitor'].get_next_questions(state)
    print(f"   Generated {len(questions)} questions")
    for i, q in enumerate(questions[:3], 1):
        print(f"   Q{i}: {q}")
    
    # Simulate user answers
    answers = {
        "How many digital inputs do you need?": "8",
        "What is the operating temperature range?": "-10 to 50C",
        "What is the humidity level?": "Normal",
        "What voltage?": "24V DC"
    }
    
    print("\n2. PROCESSING ANSWERS...")
    state = agents['elicitor'].process_answers(answers, state)
    print(f"   Stored {len(state.requirements)} requirements")
    
    # Step 2: Check completeness
    print("\n3. COMPLETENESS CHECK...")
    score = agents['completeness'].check_completeness(state)
    print(f"   Completeness: {score:.1%}")
    
    gaps = agents['completeness'].identify_gaps(state)
    if gaps:
        print(f"   Missing: {', '.join(gaps[:3])}")
    
    # Step 3: Validate
    print("\n4. VALIDATION...")
    result = agents['validator'].validate(state)
    print(f"   Valid: {result.is_valid}")
    if result.violations:
        print(f"   Issues: {result.violations[0]}")
    
    # Check logs
    print(f"\n=== Check logs at: logs/sessions/{session_id}/decisions.jsonl ===")
    
    return state

if __name__ == "__main__":
    final_state = run_manual_test()
    print(f"\nFinal completeness: {final_state.completeness_score:.1%}")