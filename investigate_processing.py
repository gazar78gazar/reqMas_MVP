import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.agents.elicitor import RequirementsElicitor
from src.state.simple_state import SimpleState
from src.logging.decision_logger import DecisionLogger

logger = DecisionLogger("investigate")
elicitor = RequirementsElicitor(logger)
state = SimpleState(session_id="investigate")

print("=== ANSWER PROCESSING INVESTIGATION ===\n")

# First, get the questions that are being asked
questions = elicitor.get_next_questions(state)
print(f"Questions being asked ({len(questions)}):")
for q in questions:
    print(f"  - '{q}'")

print("\n" + "="*50 + "\n")

# Now try to answer them
test_answers = {
    "How many digital inputs do you need?": "8",
    "How many digital outputs do you need?": "4",
    "What is the operating temperature range?": "-10 to 50C",
    "What voltage?": "24V DC"
}

print(f"Attempting to process {len(test_answers)} answers:")
for q, a in test_answers.items():
    print(f"  Q: '{q}'")
    print(f"  A: '{a}'")

# Check if process_answers exists
if hasattr(elicitor, 'process_answers'):
    print("\n✓ process_answers method exists")
    
    print(f"\nBefore: {len(state.requirements)} requirements")
    
    new_state = elicitor.process_answers(test_answers, state)
    
    print(f"After: {len(new_state.requirements)} requirements")
    
    if new_state.requirements:
        print("\nStored requirements:")
        for req in new_state.requirements:
            print(f"  [{req.category}] {req.question} = {req.answer}")
    
    # Analyze the mismatch
    print("\n--- MISMATCH ANALYSIS ---")
    answered_questions = [r.question for r in new_state.requirements]
    for key in test_answers.keys():
        if key in questions:
            print(f"✓ '{key}' is in generated questions")
        else:
            print(f"✗ '{key}' NOT in generated questions")
            # Find close matches
            for q in questions:
                if key.lower()[:20] in q.lower():
                    print(f"  Possible match: '{q}'")
else:
    print("✗ No process_answers method found!")