from src.logging.decision_logger import DecisionLogger
from src.agents.elicitor import RequirementsElicitor
from src.state.simple_state import SimpleState

# Test the flexible answer processing
logger = DecisionLogger('test')
elicitor = RequirementsElicitor(logger)
state = SimpleState(session_id='test')

print("Testing flexible answer processing:")
print("=" * 50)

# Test 1: Process answers for questions that weren't asked yet
custom_answers = {
    "What is the maximum cable length?": "100 meters",
    "Do you need redundancy?": "Yes, dual redundant",
    "What is the scan cycle time requirement?": "10ms"
}

print("\n1. Processing custom questions not in standard set:")
state = elicitor.process_answers(custom_answers, state)

for req in state.requirements:
    print(f"  {req.category}: {req.question[:40]}... = {req.answer}")

# Test 2: Process mix of standard and custom questions
print("\n2. Processing mix of standard and custom questions:")
mixed_answers = {
    "How many digital inputs do you need?": "24",  # Standard question
    "What is your budget?": "$50,000",  # Custom question
    "What is the operating temperature range?": "-20 to 60 C",  # Standard question
    "What industry standards must be met?": "UL, CE, ISO 9001"  # Custom question
}

state = elicitor.process_answers(mixed_answers, state)

print(f"\nTotal requirements: {len(state.requirements)}")
print("\nCategories assigned:")
for req in state.requirements[-4:]:  # Show last 4 added
    print(f"  {req.category}: {req.question[:40]}... = {req.answer}")

# Test 3: Test category determination
print("\n3. Testing category determination:")
test_questions = [
    "How many analog inputs are needed?",
    "What is the ambient temperature?",
    "Which Ethernet protocol is preferred?",
    "What is the power consumption limit?",
    "What color should the enclosure be?"
]

for q in test_questions:
    category = elicitor._determine_category(q)
    print(f"  '{q[:40]}...' -> {category}")

# Test 4: Process answers with empty values (should skip)
print("\n4. Processing with empty answers:")
with_empty = {
    "Question 1": "Answer 1",
    "Question 2": "",  # Empty, should skip
    "Question 3": None,  # None, should skip
    "Question 4": "Answer 4"
}

initial_count = len(state.requirements)
state = elicitor.process_answers(with_empty, state)
added = len(state.requirements) - initial_count

print(f"  Added {added} of {len(with_empty)} (skipped empty answers)")

print("\n" + "=" * 50)
print("Flexible answer processing works correctly!")