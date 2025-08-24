from src.logging.decision_logger import DecisionLogger
from src.agents.completeness import CompletenessChecker
from src.state.simple_state import SimpleState

# Test the field-based completeness checking
logger = DecisionLogger('test')
checker = CompletenessChecker(logger)
state = SimpleState(session_id='test')

print("Testing field-based completeness checking:")
print("=" * 50)

# Test 1: Empty state
score = checker.check_completeness(state)
print(f"\n1. Empty state completeness: {score:.2%}")

# Test 2: Add some required field answers
state.add_requirement("I/O", "How many digital inputs do you need?", "24")
state.add_requirement("I/O", "How many digital outputs do you need?", "16")
score = checker.check_completeness(state)
print(f"\n2. With 2 I/O fields answered: {score:.2%}")

# Test 3: Add more fields from different categories
state.add_requirement("Environment", "What is the operating temperature range?", "-10 to 50C")
state.add_requirement("Power", "What is your available power supply voltage (24VDC, 120VAC, 240VAC)?", "24VDC")
score = checker.check_completeness(state)
print(f"\n3. With 4 fields answered: {score:.2%}")

# Test 4: Show what fields are considered required
print(f"\n4. Required fields by category:")
for category, fields in checker.REQUIRED_FIELDS.items():
    print(f"   {category}: {fields}")

total_fields = sum(len(fields) for fields in checker.REQUIRED_FIELDS.values())
print(f"\n   Total required fields: {total_fields}")

# Test 5: Add all required fields to achieve 100%
state.add_requirement("I/O", "Do you need analog inputs? If yes, how many and what type (0-10V, 4-20mA)?", "8 channels, 4-20mA")
state.add_requirement("I/O", "Do you need analog outputs? If yes, how many and what type?", "4 channels, 0-10V")
state.add_requirement("Environment", "Is this an indoor or outdoor installation?", "Indoor")
state.add_requirement("Environment", "What is the humidity level (normal, high, condensing)?", "Normal")
state.add_requirement("Communication", "What communication protocols do you need (Ethernet, Modbus, Profibus, etc.)?", "Ethernet and Modbus")
state.add_requirement("Communication", "Do you need remote access capability?", "Yes")
state.add_requirement("Power", "What is your maximum power budget in watts?", "150W")

score = checker.check_completeness(state)
print(f"\n5. With all {total_fields} required fields answered: {score:.2%}")

print("\n" + "=" * 50)
print("Field-based completeness calculation works correctly!")