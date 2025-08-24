import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.agents.elicitor import RequirementsElicitor
from src.logging.decision_logger import DecisionLogger
from src.state.simple_state import SimpleState
import inspect

logger = DecisionLogger("investigate")
elicitor = RequirementsElicitor(logger)

print("=== ELICITOR INVESTIGATION ===\n")

# Check what questions are defined
if hasattr(elicitor, 'IO_QUESTIONS'):
    print(f"I/O Questions: {len(elicitor.IO_QUESTIONS)}")
    for q in elicitor.IO_QUESTIONS[:3]:
        print(f"  - {q}")

if hasattr(elicitor, 'ENV_QUESTIONS'):
    print(f"\nEnvironment Questions: {len(elicitor.ENV_QUESTIONS)}")
    for q in elicitor.ENV_QUESTIONS[:3]:
        print(f"  - {q}")

if hasattr(elicitor, 'COMM_QUESTIONS'):
    print(f"\nCommunication Questions: {len(elicitor.COMM_QUESTIONS)}")
    
if hasattr(elicitor, 'POWER_QUESTIONS'):
    print(f"\nPower Questions: {len(elicitor.POWER_QUESTIONS)}")

# Test getting questions
print("\n--- Testing get_next_questions ---")
empty_state = SimpleState(session_id="test")
questions = elicitor.get_next_questions(empty_state)
print(f"Questions returned: {len(questions)}")
for i, q in enumerate(questions, 1):
    print(f"  {i}. {q}")

# Check the method implementation
print("\n--- get_next_questions method (first 30 lines) ---")
try:
    source = inspect.getsource(elicitor.get_next_questions)
    for i, line in enumerate(source.split('\n')[:30], 1):
        print(f"{i:3}: {line}")
except:
    print("Could not get source code")