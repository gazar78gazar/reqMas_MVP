# check_simulation_completeness.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

print("=== CHECKING SIMULATION COMPLETENESS HANDLING ===\n")

with open("simulate_user.py", "r", encoding='utf-8') as f:
    lines = f.readlines()

print("Lines that handle completeness:")
print("-" * 50)

for i, line in enumerate(lines, 1):
    if "completeness" in line.lower() and "score" in line.lower():
        print(f"Line {i}: {line.strip()}")

print("\nKey question: After calling check_completeness(),")
print("does it UPDATE state.completeness_score?")