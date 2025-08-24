import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.state.simple_state import SimpleState, RequirementEntry
from src.agents.agent_factory import create_agents
from src.agents.orchestrator import Orchestrator
from src.logging.decision_logger import DecisionLogger

print("=== TEST VALIDATOR LLM INTEGRATION ===\n")

# Initialize system
session_id = "validator_test"
state = SimpleState(session_id=session_id)
agents = create_agents(session_id)
logger = DecisionLogger(session_id)
orchestrator = Orchestrator(logger)

# Add some requirements to validate
print("Adding test requirements...")
state.requirements = [
    RequirementEntry(category="Environment", question="Temperature range?", answer="-40 to 85°C extreme conditions"),
    RequirementEntry(category="Environment", question="Enclosure type?", answer="Standard plastic enclosure"),
    RequirementEntry(category="Power", question="Power source?", answer="Solar powered, 5W maximum"),
    RequirementEntry(category="I/O", question="Outputs needed?", answer="50 high-power relay outputs"),
    RequirementEntry(category="Communication", question="Protocol?", answer="Ethernet and Modbus TCP"),
]

print(f"Created {len(state.requirements)} requirements\n")

# Test 1: Direct validator call
print("TEST 1: Direct Validator Call")
print("-" * 50)

validator = agents.get('validator')
if validator:
    result = validator.validate(state)
    
    print(f"Is Valid: {result.is_valid}")
    print(f"Violations: {len(result.violations)}")
    print(f"Warnings: {len(result.warnings)}")
    print(f"Suggestions: {len(result.suggestions)}")
    
    if result.violations:
        print("\n❌ Violations found:")
        for v in result.violations[:3]:
            print(f"  - {v}")
    
    if result.warnings:
        print("\n⚠️ Warnings:")
        for w in result.warnings[:3]:
            print(f"  - {w}")
    
    if result.suggestions:
        print("\n💡 Suggestions:")
        for s in result.suggestions[:3]:
            print(f"  - {s}")

# Test 2: Full orchestrator flow
print("\n\nTEST 2: Full Orchestrator Flow")
print("-" * 50)

# Set high completeness to trigger validation
state.completeness_score = 0.90
state.iteration_count = 1

# Route should go to validator
next_agent = orchestrator.route(state)
print(f"With 90% completeness, routes to: {next_agent}")

if next_agent == "validator":
    print("✅ Correctly routed to validator")
    
    # Execute validation
    result = agents['validator'].validate(state)
    
    if not result.is_valid:
        print("✅ Validation correctly identified issues")
    else:
        print("⚠️ Validation passed despite incompatible requirements")

# Test 3: Check if using LLM or rules
print("\n\nTEST 3: Validation Method Check")
print("-" * 50)

if hasattr(agents['validator'], 'use_llm'):
    if agents['validator'].use_llm:
        print("✅ Using LLM validation (GPT-4o)")
    else:
        print("⚠️ Using rule-based validation (fallback)")
else:
    print("❌ Validator doesn't have LLM integration")

# Check logs for reasoning
log_file = f"logs/sessions/{session_id}/decisions.jsonl"
if os.path.exists(log_file):
    print(f"\n📁 Decision log: {log_file}")
    
    # Read last validator decision
    with open(log_file, 'r') as f:
        lines = f.readlines()
        for line in reversed(lines):
            if '"agent": "validator"' in line or '"agent_name": "validator"' in line:
                import json
                entry = json.loads(line)
                print(f"Last validator decision: {entry.get('decision', entry.get('decision_made', 'N/A'))}")
                break

print("\n✅ Integration test complete!")