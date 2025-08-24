import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

print("=== STATE UPDATE INVESTIGATION ===\n")

# Check if the simulation is updating iteration_count correctly
print("1. Checking simulate_user.py for iteration handling:")
print("-" * 50)

if os.path.exists("simulate_user.py"):
    with open("simulate_user.py", "r") as f:
        lines = f.readlines()
    
    print("Lines with 'iteration' references:\n")
    for i, line in enumerate(lines, 1):
        if "iteration" in line.lower():
            print(f"Line {i}: {line.strip()}")
    
    print("\n2. Checking for state.iteration_count updates:")
    print("-" * 50)
    
    has_iteration_update = False
    for i, line in enumerate(lines, 1):
        if "state.iteration_count" in line and "=" in line:
            print(f"Line {i}: {line.strip()}")
            has_iteration_update = True
    
    if not has_iteration_update:
        print("⚠️ WARNING: No 'state.iteration_count =' found!")
        print("This might be why iterations aren't working properly.")
else:
    print("simulate_user.py not found!")

print("\n3. Checking interactive_test.py for comparison:")
print("-" * 50)

if os.path.exists("interactive_test.py"):
    with open("interactive_test.py", "r") as f:
        interactive_content = f.read()
    
    if "state.iteration_count" in interactive_content:
        print("✅ Interactive test updates state.iteration_count")
    else:
        print("❌ Interactive test does NOT update state.iteration_count")
    
    if "orchestrator.route" in interactive_content:
        print("✅ Interactive test uses orchestrator.route()")
    else:
        print("❌ Interactive test does NOT use orchestrator.route()")
        print("   (This explains why it works differently!)")

print("\n" + "="*50)
print("KEY FINDINGS:")
print("-" * 50)
print("1. Is iteration_count being set on the state object?")
print("2. Is the orchestrator being used for routing?")
print("3. Are both tests using the same flow?")