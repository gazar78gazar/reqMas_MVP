import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.state.simple_state import SimpleState
from src.agents.agent_factory import create_agents
from src.agents.orchestrator import Orchestrator
from src.logging.decision_logger import DecisionLogger

print("=== END-TO-END TEST WITH LLM ===\n")

def simulate_conversation():
    # Initialize
    session_id = "e2e_llm"
    state = SimpleState(session_id=session_id)
    agents = create_agents(session_id)
    logger = DecisionLogger(session_id)
    orchestrator = Orchestrator(logger)
    
    # Natural language responses (messy on purpose)
    user_responses = {
        "digital input": "we have about 12 sensors to monitor",
        "digital output": "probably 6 actuators, maybe 8 if we add the warning lights",
        "temperature": "It's pretty extreme, from minus 20 in winter to plus 45 celsius in summer",
        "environment": "outdoor installation near the ocean, so lots of salt and humidity",
        "power": "We have 24V DC available, but might need battery backup",
        "network": "ethernet is preferred, but we have some modbus devices too",
        "analog": "yes, 4-20mA signals from pressure sensors, about 4 of them",
    }
    
    iteration = 0
    max_iterations = 3
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\n{'='*60}")
        print(f"ITERATION {iteration}")
        print('='*60)
        
        # Route
        next_agent = orchestrator.route(state)
        print(f"→ Routing to: {next_agent}")
        
        if next_agent == "END":
            break
            
        elif next_agent == "elicitor":
            # Get dynamic questions
            questions = agents['elicitor'].get_next_questions(state)
            print(f"\n📝 Asking {len(questions)} questions:")
            
            # Answer with natural language
            answers = {}
            for i, q in enumerate(questions[:4], 1):  # Answer first 4
                print(f"\n  Q{i}: {q}")
                # Find matching response
                for key, response in user_responses.items():
                    if key.lower() in q.lower():
                        answers[q] = response
                        print(f"  A: '{response}'")
                        break
                else:
                    print(f"  A: [no response]")
            
            # Process answers
            if answers:
                state = agents['elicitor'].process_answers(answers, state)
                print(f"\n✅ Processed {len(answers)} answers")
                
        elif next_agent == "completeness":
            score = agents['completeness'].check_completeness(state)
            state.completeness_score = score
            print(f"\n📊 Completeness: {score:.1%}")
            
            if score < 0.85:
                gaps = agents['completeness'].identify_gaps(state)
                print(f"   Missing: {', '.join(gaps[:3])}")
                
        elif next_agent == "validator":
            # Test LLM validation
            if hasattr(agents['elicitor'], 'llm') and agents['elicitor'].llm:
                reqs_dict = [{"question": r.question, "answer": r.answer} for r in state.requirements]
                validation = agents['elicitor'].llm.validate_requirements(reqs_dict)
                print(f"\n🔍 Validation Result:")
                print(f"   Valid: {validation['is_valid']}")
                if validation['violations']:
                    print(f"   ❌ Violations: {validation['violations'][:2]}")
                if validation['warnings']:
                    print(f"   ⚠️ Warnings: {validation['warnings'][:2]}")
                if validation['suggestions']:
                    print(f"   💡 Suggestions: {validation['suggestions'][:2]}")
            break
        
        state.iteration_count = iteration
    
    # Summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print('='*60)
    print(f"Requirements collected: {len(state.requirements)}")
    print(f"Completeness: {state.completeness_score:.1%}")
    print(f"\nSample requirements:")
    for req in state.requirements[:3]:
        print(f"  [{req.category}] {req.answer}")
    
    return state

# Run the test
final_state = simulate_conversation()