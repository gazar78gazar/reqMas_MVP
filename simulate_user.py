import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.state.simple_state import SimpleState
from src.agents.agent_factory import create_agents
from src.agents.orchestrator import Orchestrator
from src.logging.decision_logger import DecisionLogger
import uuid

def simulate_user_session(scenario_name, user_responses):
    """Simulate a complete user session"""
    
    print(f"\n{'='*60}")
    print(f"SCENARIO: {scenario_name}")
    print('='*60)
    
    # Initialize
    session_id = str(uuid.uuid4())
    state = SimpleState(session_id=session_id)
    agents = create_agents(session_id)
    logger = DecisionLogger(session_id)
    orchestrator = Orchestrator(logger)
    
    iteration = 0
    max_iterations = 3
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\n--- Iteration {iteration} ---")
        
        # Get next agent
        next_agent = orchestrator.route(state)
        print(f"Orchestrator routes to: {next_agent}")
        
        if next_agent == "END":
            break
        elif next_agent == "elicitor":
            # Get questions
            questions = agents['elicitor'].get_next_questions(state)
            print(f"System asks {len(questions)} questions:")
            
            # Simulate user answering
            answers = {}
            for q in questions[:4]:  # Answer first 4 questions each round
                if q in user_responses:
                    answers[q] = user_responses[q]
                    print(f"  Q: {q[:50]}...")
                    print(f"  A: {user_responses[q]}")
            
            # Process answers
            state = agents['elicitor'].process_answers(answers, state)
            
        elif next_agent == "completeness":
            score = agents['completeness'].check_completeness(state)
            state.completeness_score = score
            print(f"Completeness: {score:.1%}")
            
            if score < 0.85:
                gaps = agents['completeness'].identify_gaps(state)
                print(f"Missing: {len(gaps)} fields")
        
        elif next_agent == "validator":
            result = agents['validator'].validate(state)
            print(f"Validation: {'PASSED' if result.is_valid else 'FAILED'}")
            if not result.is_valid:
                print(f"Issues: {result.violations[:3]}")
            break
        
        state.iteration_count = iteration
    
    # Final summary
    print(f"\n--- Final Results ---")
    print(f"Total requirements collected: {len(state.requirements)}")
    print(f"Final completeness: {state.completeness_score:.1%}")
    print(f"Session log: logs/sessions/{session_id}/decisions.jsonl")
    
    return state

# SCENARIO 1: Warehouse Temperature Monitoring
warehouse_responses = {
    "How many digital inputs do you need?": "4",
    "How many digital outputs do you need?": "2",
    "What is the operating temperature range?": "-10 to 40 Celsius",
    "Is this an indoor or outdoor installation?": "Indoor warehouse",
    "What communication protocol do you need?": "Modbus TCP",
    "What voltage is available?": "24VDC",
    "Do you need analog inputs? If yes, how many and what type (0-10V, 4-20mA)?": "Yes, 4 temperature sensors 4-20mA",
    "What is the humidity level (normal, high, condensing)?": "Normal, controlled environment",
    "What type of network connection?": "Ethernet",
    "What is the maximum power consumption allowed?": "50W max"
}

# SCENARIO 2: Outdoor Industrial Control
outdoor_responses = {
    "How many digital inputs do you need?": "16",
    "How many digital outputs do you need?": "8",
    "What is the operating temperature range?": "-40 to 85 Celsius",
    "Is this an indoor or outdoor installation?": "Outdoor, exposed to weather",
    "What communication protocol do you need?": "EtherNet/IP",
    "What voltage is available?": "110VAC",
    "Do you need analog inputs? If yes, how many and what type (0-10V, 4-20mA)?": "Yes, 8 channels 0-10V",
    "What is the humidity level (normal, high, condensing)?": "High, condensing possible",
    "Are there vibration or shock requirements?": "Yes, heavy machinery nearby",
    "Do you need battery backup?": "Yes, 4 hours minimum"
}

# Run simulations
if __name__ == "__main__":
    print("=== USER SIMULATION TEST ===")
    
    # Test Scenario 1
    warehouse_state = simulate_user_session(
        "Warehouse Temperature Monitoring",
        warehouse_responses
    )
    
    # Test Scenario 2  
    outdoor_state = simulate_user_session(
        "Outdoor Industrial Control",
        outdoor_responses
    )
    
    # Summary
    print("\n" + "="*60)
    print("SIMULATION SUMMARY")
    print("="*60)
    print(f"Warehouse: {warehouse_state.completeness_score:.1%} complete, {len(warehouse_state.requirements)} requirements")
    print(f"Outdoor: {outdoor_state.completeness_score:.1%} complete, {len(outdoor_state.requirements)} requirements")