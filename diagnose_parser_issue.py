import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import json
from dotenv import load_dotenv

print("=== SURGICAL DIAGNOSIS OF PARSER ISSUE ===\n")

# Load environment
load_dotenv()

# Step 1: Test raw OpenAI call
print("STEP 1: Test Raw OpenAI API Call")
print("-" * 50)

try:
    from openai import OpenAI
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Minimal test
    test_schema = {
        "type": "object",
        "properties": {
            "test": {"type": "string"}
        },
        "required": ["test"]
    }
    
    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[{"role": "user", "content": "Say hello"}],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "test",
                "strict": True,
                "schema": test_schema
            }
        }
    )
    
    result = json.loads(response.choices[0].message.content)
    print(f"✅ Raw API works: {result}")
    
except Exception as e:
    print(f"❌ Raw API failed: {e}")
    print(f"   Error type: {type(e).__name__}")

# Step 2: Test the parse_answer schema specifically
print("\nSTEP 2: Test Parser Schema")
print("-" * 50)

try:
    from src.llm.openai_service import OpenAIService
    from src.logging.decision_logger import DecisionLogger
    
    logger = DecisionLogger("diagnose")
    service = OpenAIService(logger)
    
    # Check what parse_answer actually does
    import inspect
    source = inspect.getsource(service.parse_answer)
    
    # Find the schema definition
    lines = source.split('\n')
    schema_start = None
    schema_end = None
    
    for i, line in enumerate(lines):
        if 'schema = {' in line:
            schema_start = i
        if schema_start and line.strip() == '}' and 'required' in lines[i-1]:
            schema_end = i
            break
    
    if schema_start:
        print("Found schema definition in parse_answer:")
        for i in range(schema_start, min(schema_start + 10, len(lines))):
            print(f"  {lines[i]}")
    
    # Now test the actual method
    print("\nCalling parse_answer method:")
    result = service.parse_answer("How many inputs?", "about 8")
    print(f"Result: {result}")
    print(f"Type: {type(result)}")
    
except Exception as e:
    print(f"❌ Service test failed: {e}")
    import traceback
    traceback.print_exc()

# Step 3: Check for fallback behavior
print("\nSTEP 3: Check Fallback Logic")
print("-" * 50)

try:
    # Look at the parse_answer method's exception handling
    source_lines = inspect.getsource(service.parse_answer).split('\n')
    
    for i, line in enumerate(source_lines):
        if 'except' in line:
            print(f"Line {i}: {line}")
            # Show the fallback logic
            for j in range(i+1, min(i+6, len(source_lines))):
                if source_lines[j].strip():
                    print(f"Line {j}: {source_lines[j]}")
                if 'return' in source_lines[j]:
                    break
    
    # Test if exception is being triggered
    print("\nTesting with debug logging:")
    
    # Monkey-patch to see exceptions
    original_parse = service.parse_answer
    
    def debug_parse(question, answer):
        try:
            print(f"  Calling original parse with: '{question}', '{answer}'")
            result = original_parse(question, answer)
            print(f"  Success: {result}")
            return result
        except Exception as e:
            print(f"  Exception caught: {e}")
            # Return fallback
            return {
                "parsed_value": answer,
                "confidence": 1.0,
                "category": "Other",
                "needs_clarification": False
            }
    
    service.parse_answer = debug_parse
    test_result = service.parse_answer("Test question", "Test answer")
    print(f"Final result: {test_result}")
    
except Exception as e:
    print(f"Error in fallback check: {e}")

# Step 4: Test with exact production parameters
print("\nSTEP 4: Production Parameters Test")
print("-" * 50)

try:
    # Test with the exact schema that should work
    test_messages = [
        {
            "role": "system",
            "content": "You are a technical requirements parser."
        },
        {
            "role": "user", 
            "content": """Parse this technical requirement answer.

Question: How many digital inputs do you need?
User Answer: I think about 8 or 10

Extract the technical value, categorize it, and assess if clarification is needed.
Examples:
- "I think about 8 or 10" → parsed_value: "8-10", needs_clarification: true
- "24VDC" → parsed_value: "24VDC", needs_clarification: false"""
        }
    ]
    
    schema = {
        "type": "object",
        "properties": {
            "parsed_value": {
                "type": "string",
                "description": "The extracted technical value"
            },
            "confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "description": "Confidence in parsing (0-1)"
            },
            "category": {
                "type": "string",
                "enum": ["I/O", "Environment", "Communication", "Power", "Other"],
                "description": "Category of the requirement"
            },
            "needs_clarification": {
                "type": "boolean",
                "description": "Whether answer needs clarification"
            },
            "clarification_question": {
                "type": "string",
                "description": "Follow-up question if needed"
            }
        },
        "required": ["parsed_value", "confidence", "category", "needs_clarification"],
        "additionalProperties": False
    }
    
    print("Making direct API call with production schema...")
    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=test_messages,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "answer_parsing",
                "strict": True,
                "schema": schema
            }
        }
    )
    
    result = json.loads(response.choices[0].message.content)
    print(f"✅ Direct call result: {result}")
    
except Exception as e:
    print(f"❌ Production test failed: {e}")
    import traceback
    traceback.print_exc()