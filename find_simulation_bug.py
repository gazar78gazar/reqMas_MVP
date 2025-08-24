# find_simulation_bug.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

print("=== FINDING SIMULATION BUG ===\n")

with open("simulate_user.py", "r", encoding='utf-8') as f:
    lines = f.readlines()

print("1. Where completeness is checked:")
print("-" * 50)

for i, line in enumerate(lines, 1):
    if "check_completeness" in line:
        print(f"Line {i}: {line.strip()}")
        # Show context around it
        print("  Context:")
        for j in range(max(0, i-2), min(len(lines), i+3)):
            print(f"    {j+1}: {lines[j].rstrip()}")
        print()

print("\n2. Where completeness score is used:")
print("-" * 50)

for i, line in enumerate(lines, 1):
    if "completeness_score" in line and "print" in line:
        print(f"Line {i}: {line.strip()}")

print("\n3. The issue:")
print("-" * 50)
print("After calling check_completeness(), the code needs to:")
print("  score = agents['completeness'].check_completeness(state)")
print("  state.completeness_score = score  # <-- This might be missing!")