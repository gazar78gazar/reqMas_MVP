# check_interactive_orchestrator.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

print("=== CHECKING TEST FILE DIFFERENCES ===\n")

# Fix the Unicode error by specifying encoding
try:
    with open("interactive_test.py", "r", encoding='utf-8') as f:
        interactive_content = f.read()
    
    print("INTERACTIVE_TEST.PY:")
    print("-" * 40)
    
    if "orchestrator.route" in interactive_content:
        print("✅ Uses orchestrator for routing")
    else:
        print("❌ Does NOT use orchestrator for routing")
        print("   (This explains why it works!)")
    
    if "state.iteration_count" in interactive_content:
        print("✅ Updates iteration_count")
    else:
        print("❌ Does NOT update iteration_count")
        
except Exception as e:
    print(f"Error reading interactive_test.py: {e}")

try:
    with open("simulate_user.py", "r", encoding='utf-8') as f:
        simulate_content = f.read()
    
    print("\nSIMULATE_USER.PY:")
    print("-" * 40)
    
    if "orchestrator.route" in simulate_content:
        print("✅ Uses orchestrator for routing")
        
    if 'elif next_agent == "completeness"' in simulate_content:
        print("⚠️  Has handler for 'completeness' but doesn't route back!")
        
except Exception as e:
    print(f"Error reading simulate_user.py: {e}")