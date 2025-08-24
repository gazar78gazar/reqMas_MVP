import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.state.simple_state import SimpleState, RequirementEntry
from src.agents.agent_factory import create_agents

print("=== TEST LLM VALIDATION ===\n")

agents = create_agents("validation_test")

# Test different requirement sets
test_scenarios = [
    {
        "name": "Incompatible Requirements",
        "requirements": [
            RequirementEntry(category="Environment", question="Temperature?", answer="-40 to 85°C"),
            RequirementEntry(category="Environment", question="Enclosure?", answer="Standard plastic enclosure"),
            RequirementEntry(category="Power", question="Power?", answer="Solar powered, 5W max"),
            RequirementEntry(category="I/O", question="Outputs?", answer="50 high-power relays")
        ]
    },
    {
        "name": "Good Requirements",
        "requirements": [
            RequirementEntry(category="Environment", question="Temperature?", answer="0 to 50°C"),
            RequirementEntry(category="Environment", question="Installation?", answer="Indoor, climate controlled"),
            RequirementEntry(category="Power", question="Power?", answer="24VDC, 100W available"),
            RequirementEntry(category="I/O", question="Inputs?", answer="8 digital inputs")
        ]
    },
    {
        "name": "Vague Requirements",
        "requirements": [
            RequirementEntry(category="I/O", question="Inputs?", answer="Some sensors"),
            RequirementEntry(category="Communication", question="Protocol?", answer="Whatever works"),
            RequirementEntry(category="Power", question="Power?", answer="Normal power"),
        ]
    }
]

if hasattr(agents['elicitor'], 'llm') and agents['elicitor'].llm:
    for scenario in test_scenarios:
        print(f"Scenario: {scenario['name']}")
        print("-" * 50)
        
        # Convert to dict format for validation
        reqs_dict = [
            {"question": r.question, "answer": r.answer} 
            for r in scenario['requirements']
        ]
        
        # Get LLM validation
        validation = agents['elicitor'].llm.validate_requirements(reqs_dict)
        
        print(f"Valid: {validation['is_valid']}")
        print(f"Confidence: {validation['confidence']:.0%}")
        
        if validation['violations']:
            print(f"❌ Violations:")
            for v in validation['violations'][:2]:
                print(f"   - {v}")
        
        if validation['warnings']:
            print(f"⚠️ Warnings:")
            for w in validation['warnings'][:2]:
                print(f"   - {w}")
        
        if validation['suggestions']:
            print(f"💡 Suggestions:")
            for s in validation['suggestions'][:2]:
                print(f"   - {s}")
        
        print()
else:
    print("❌ LLM validation not available")

print("✅ Validation test complete!")