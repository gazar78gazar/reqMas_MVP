import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.llm.openai_service import OpenAIService
from src.logging.decision_logger import DecisionLogger

print("=== TEST PARSER AFTER FIX ===\n")

logger = DecisionLogger("test_fix")
service = OpenAIService(logger)

test_cases = [
    ("How many digital inputs?", "I think about 8 or maybe 10"),
    ("Temperature range?", "from minus 20 to plus 45 celsius"),
    ("Power requirements?", "24 volts DC, might need battery"),
    ("Network protocol?", "ethernet and modbus"),
]

print("Testing parse_answer with natural language:\n")

for question, answer in test_cases:
    print(f"Question: {question}")
    print(f"User said: '{answer}'")
    
    try:
        result = service.parse_answer(question, answer)
        
        print(f"  ✅ Parsed: '{result['parsed_value']}'")
        print(f"     Category: {result['category']}")
        print(f"     Confidence: {result['confidence']:.0%}")
        print(f"     Needs clarification: {result.get('needs_clarification', False)}")
        
        # Check if it's actually parsing (not just returning input)
        if result['parsed_value'] != answer:
            print(f"     🎉 ACTUAL PARSING OCCURRED!")
        else:
            print(f"     ⚠️ Returned unchanged")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    print("-" * 40)

print("\n✅ Test complete!")