import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

print("=== PROVING THE HYPOTHESIS ===\n")
print("Hypothesis: Completeness is never calculated in the simulation flow\n")

# Analyze the simulation flow
with open("simulate_user.py", "r", encoding='utf-8') as f:
    lines = f.readlines()

print("1. CHECKING SIMULATION FLOW:")
print("-" * 50)

# Track the flow
in_iteration_loop = False
iteration_count = 0
indent_level = 0

for i, line in enumerate(lines, 1):
    # Track iteration loop
    if "while iteration < max_iterations:" in line:
        in_iteration_loop = True
        print(f"Line {i}: Iteration loop starts")
    
    if in_iteration_loop:
        # Track routing
        if "orchestrator.route" in line:
            print(f"Line {i}: {line.strip()}")
        
        # Track agent handlers
        if 'if next_agent == "' in line or 'elif next_agent == "' in line:
            print(f"Line {i}: {line.strip()}")
            
            # Check what happens in each handler
            for j in range(i, min(i+10, len(lines))):
                if "check_completeness" in lines[j]:
                    print(f"  Line {j+1}: ✓ Completeness IS checked here")
                    break
                if "elif" in lines[j] or ("if" in lines[j] and j != i):
                    print(f"  Line {j+1}: ✗ Completeness NOT checked in this branch")
                    break

print("\n2. CRITICAL QUESTION:")
print("-" * 50)
print("In Iteration 1, what is next_agent?")
print("Let's check what the orchestrator returns for empty state...")

from src.agents.orchestrator import Orchestrator
from src.state.simple_state import SimpleState
from src.logging.decision_logger import DecisionLogger

orchestrator = Orchestrator(DecisionLogger("test"))
empty_state = SimpleState(session_id="test")
first_route = orchestrator.route(empty_state)
print(f"  Empty state → orchestrator routes to: '{first_route}'")

print("\n3. FLOW ANALYSIS:")
print("-" * 50)
print("If first route is 'elicitor':")
print("  - Does the elicitor handler check completeness? ")
print("  - If NO, then state.completeness_score stays 0.0")
print("  - Next iteration: orchestrator sees 0.0 < 0.85")
print("  - Routes to elicitor AGAIN (not completeness!)")