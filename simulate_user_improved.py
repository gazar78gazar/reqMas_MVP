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
    max_iterations = 5  # Increased to allow more rounds
    
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
            answered_count = 0
            for q in questions:  # Answer ALL questions that we have answers for
                if q in user_responses:
                    answers[q] = user_responses[q]
                    answered_count += 1
                    print(f"  Q{answered_count}: {q[:50]}...")
                    print(f"  A{answered_count}: {user_responses[q]}")
            
            if answered_count == 0:
                print(f"  [No answers available for these questions]")
            
            # Process answers
            state = agents['elicitor'].process_answers(answers, state)
            
        elif next_agent == "completeness":
            score = agents['completeness'].check_completeness(state)
            state.completeness_score = score
            print(f"Completeness: {score:.1%}")
            
            if score < 0.85:
                gaps = agents['completeness'].identify_gaps(state)
                print(f"Missing: {len(gaps)} fields - {', '.join(gaps[:3])}...")
        
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
    print(f"Answered requirements: {sum(1 for r in state.requirements if r.answer)}")
    print(f"Final completeness: {state.completeness_score:.1%}")
    print(f"Session log: logs/sessions/{session_id}/decisions.jsonl")
    
    return state

# SCENARIO 1: Warehouse Temperature Monitoring - Complete responses
warehouse_responses = {
    # I/O Questions (all 7)
    "How many digital inputs do you need?": "4",
    "How many digital outputs do you need?": "2",
    "Do you need analog inputs? If yes, how many and what type (0-10V, 4-20mA)?": "Yes, 4 temperature sensors 4-20mA",
    "Do you need analog outputs? If yes, how many and what type?": "No",
    "What is the maximum distance between I/O points and the controller?": "50 meters",
    "Do you need any special I/O like RTD, thermocouple, or high-speed counters?": "RTD for temperature",
    "What response time do you need for I/O updates (milliseconds)?": "100ms",
    
    # Environment Questions (all 5)
    "What is the operating temperature range?": "-10 to 40 Celsius",
    "Is this an indoor or outdoor installation?": "Indoor warehouse",
    "What is the humidity level (normal, high, condensing)?": "Normal, controlled environment",
    "Are there any vibration or shock requirements?": "No, stable environment",
    "Is there exposure to dust, chemicals, or corrosive materials?": "Light dust only",
    
    # Communication Questions (all 5)
    "What communication protocols do you need (Ethernet, Modbus, Profibus, etc.)?": "Modbus TCP and Ethernet",
    "Do you need remote access capability?": "Yes, for monitoring",
    "How many devices will communicate with the PLC?": "5 devices",
    "What is the required data update rate for communications?": "1 second",
    "Do you need redundant communication paths?": "No",
    
    # Power Questions (all 4)
    "What is your available power supply voltage (24VDC, 120VAC, 240VAC)?": "24VDC",
    "What is your maximum power budget in watts?": "50 watts",
    "Do you need battery backup or UPS support?": "No",
    "Do you need redundant power supplies?": "No"
}

# SCENARIO 2: Outdoor Industrial Control - Complete responses
outdoor_responses = {
    # I/O Questions (all 7)
    "How many digital inputs do you need?": "16",
    "How many digital outputs do you need?": "8",
    "Do you need analog inputs? If yes, how many and what type (0-10V, 4-20mA)?": "Yes, 8 channels 0-10V",
    "Do you need analog outputs? If yes, how many and what type?": "Yes, 4 channels 4-20mA",
    "What is the maximum distance between I/O points and the controller?": "200 meters",
    "Do you need any special I/O like RTD, thermocouple, or high-speed counters?": "High-speed counters, 2 channels",
    "What response time do you need for I/O updates (milliseconds)?": "10ms",
    
    # Environment Questions (all 5)
    "What is the operating temperature range?": "-40 to 85 Celsius",
    "Is this an indoor or outdoor installation?": "Outdoor, exposed to weather",
    "What is the humidity level (normal, high, condensing)?": "High, condensing possible",
    "Are there any vibration or shock requirements?": "Yes, heavy machinery nearby",
    "Is there exposure to dust, chemicals, or corrosive materials?": "Yes, industrial chemicals",
    
    # Communication Questions (all 5)
    "What communication protocols do you need (Ethernet, Modbus, Profibus, etc.)?": "EtherNet/IP and Profibus",
    "Do you need remote access capability?": "Yes, critical",
    "How many devices will communicate with the PLC?": "20 devices",
    "What is the required data update rate for communications?": "100ms",
    "Do you need redundant communication paths?": "Yes, required",
    
    # Power Questions (all 4)
    "What is your available power supply voltage (24VDC, 120VAC, 240VAC)?": "120VAC",
    "What is your maximum power budget in watts?": "200 watts",
    "Do you need battery backup or UPS support?": "Yes, 4 hours minimum",
    "Do you need redundant power supplies?": "Yes, dual redundant"
}

# Run simulations
if __name__ == "__main__":
    print("=== IMPROVED USER SIMULATION TEST ===")
    
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
    print(f"\n{'='*60}")
    print("SIMULATION SUMMARY")
    print('='*60)
    print(f"Warehouse: {warehouse_state.completeness_score:.1%} complete, {len(warehouse_state.requirements)} requirements")
    print(f"Outdoor: {outdoor_state.completeness_score:.1%} complete, {len(outdoor_state.requirements)} requirements")