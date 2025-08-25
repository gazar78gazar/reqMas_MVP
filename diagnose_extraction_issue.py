"""
Diagnostic script to identify why digital inputs aren't being extracted
Let's trace through the exact flow and find the root cause
"""

import re
import json
import asyncio
from typing import Dict, List

# Import our components
from src.agents.requirements_elicitor import RequirementsElicitorAgent
from src.state.crdt_state_manager import StateSnapshot

def diagnose_patterns():
    """Test the regex patterns directly"""
    print("=" * 60)
    print("1. TESTING REGEX PATTERNS DIRECTLY")
    print("=" * 60)
    
    # Test inputs that should match
    test_cases = [
        "I need 16 digital inputs for outdoor industrial monitoring",
        "I need 16 digital input for outdoor industrial monitoring",
        "16 digital inputs",
        "16 digital input",
        "need 16 digital inputs",
        "require 16 digital inputs please",
        "We need about 16 digital inputs",
        "System needs 16 digital inputs"
    ]
    
    # Test various patterns
    patterns_to_test = [
        (r'(\d+)\s*digital\s*input', 'Original pattern (singular)'),
        (r'(\d+)\s*digital\s*inputs', 'Plural pattern'),
        (r'(\d+)\s*digital\s*inputs?', 'Optional plural'),
        (r'(\d+)\s+digital\s+inputs?', 'With required spaces'),
        (r'.*(\d+)\s*digital\s*inputs?', 'With prefix wildcard'),
    ]
    
    print("\nTesting patterns against inputs:")
    print("-" * 40)
    
    for test_input in test_cases:
        print(f"\nInput: '{test_input}'")
        test_lower = test_input.lower()
        
        for pattern, description in patterns_to_test:
            match = re.search(pattern, test_lower)
            if match:
                print(f"  ✓ {description}: Matched! Group(1)={match.group(1)}")
            else:
                print(f"  ✗ {description}: No match")

def check_actual_patterns():
    """Check what patterns are actually in the agent"""
    print("\n" + "=" * 60)
    print("2. CHECKING ACTUAL AGENT PATTERNS")
    print("=" * 60)
    
    # Load config
    with open('data/useCase_phase1.json', 'r') as f:
        config = json.load(f)
    
    # Create agent
    agent = RequirementsElicitorAgent(config)
    
    print("\nPatterns defined in RequirementsElicitorAgent:")
    print("-" * 40)
    
    if hasattr(agent, 'io_patterns'):
        print("IO Patterns found:")
        for pattern in agent.io_patterns.keys():
            print(f"  - {pattern}")
    else:
        print("  ✗ No io_patterns attribute found!")
    
    # Test if the pattern is actually being used
    test_input = "I need 16 digital inputs"
    test_lower = test_input.lower()
    
    print(f"\nTesting against: '{test_input}'")
    matches_found = []
    
    for pattern, handler in agent.io_patterns.items():
        match = re.search(pattern, test_lower)
        if match:
            matches_found.append((pattern, match.group(1)))
            print(f"  ✓ Pattern '{pattern}' matches! Captured: {match.group(1)}")
        else:
            print(f"  ✗ Pattern '{pattern}' does not match")
    
    return matches_found

async def trace_full_extraction():
    """Trace through the full extraction process"""
    print("\n" + "=" * 60)
    print("3. TRACING FULL EXTRACTION FLOW")
    print("=" * 60)
    
    # Load config
    with open('data/useCase_phase1.json', 'r') as f:
        config = json.load(f)
    
    # Create agent
    agent = RequirementsElicitorAgent(config)
    
    # Create mock snapshot
    snapshot = StateSnapshot(
        use_cases={},
        constraints={},
        resolutions=[],
        timestamp=0,
        version=0
    )
    
    # Test input
    test_input = "I need 16 digital inputs for outdoor industrial monitoring"
    print(f"\nTest input: '{test_input}'")
    
    # Process through agent
    result = await agent.process_async(test_input, snapshot, {})
    
    print("\nAgent output:")
    print("-" * 40)
    print(json.dumps(result, indent=2, default=str))
    
    # Check specifically for digital I/O constraints
    constraints = result.get('state_updates', {}).get('constraints', [])
    
    digital_constraints = [c for c in constraints if 'DIGITAL' in c.get('id', '')]
    
    if digital_constraints:
        print(f"\n✓ Found {len(digital_constraints)} digital I/O constraints:")
        for c in digital_constraints:
            print(f"  - {c['id']}: {c.get('value', 'N/A')}")
    else:
        print("\n✗ No digital I/O constraints found!")
        print("\nOther constraints found:")
        for c in constraints:
            print(f"  - {c['id']}")

def test_extraction_method():
    """Test the extraction method directly"""
    print("\n" + "=" * 60)
    print("4. TESTING EXTRACTION METHOD")
    print("=" * 60)
    
    # Load config
    with open('data/useCase_phase1.json', 'r') as f:
        config = json.load(f)
    
    # Create agent
    agent = RequirementsElicitorAgent(config)
    
    # Simulate a match
    class MockMatch:
        def __init__(self, groups):
            self.groups_data = groups
        
        def group(self, n):
            return self.groups_data[n]
    
    test_values = [5, 16, 32, 64, 100]
    
    print("\nTesting _extract_digital_inputs method with different values:")
    print("-" * 40)
    
    for value in test_values:
        mock_match = MockMatch(['full_match', str(value)])
        
        if hasattr(agent, '_extract_digital_inputs'):
            result = agent._extract_digital_inputs(mock_match)
            if result:
                print(f"  Value {value} → {result[0]['id']} (confidence: {result[0].get('confidence', 'N/A')})")
            else:
                print(f"  Value {value} → No constraint (too small?)")
        else:
            print("  ✗ Method _extract_digital_inputs not found!")
            break

def check_pattern_execution_path():
    """Check if patterns are actually being executed"""
    print("\n" + "=" * 60)
    print("5. CHECKING PATTERN EXECUTION PATH")
    print("=" * 60)
    
    # Load config
    with open('data/useCase_phase1.json', 'r') as f:
        config = json.load(f)
    
    # Create agent
    agent = RequirementsElicitorAgent(config)
    
    test_input = "I need 16 digital inputs for outdoor monitoring"
    test_lower = test_input.lower()
    
    print(f"Input: '{test_input}'")
    print("\nStep-by-step pattern matching:")
    print("-" * 40)
    
    # Manually trace what should happen
    for pattern_str, handler in agent.io_patterns.items():
        print(f"\nTrying pattern: {pattern_str}")
        match = re.search(pattern_str, test_lower)
        
        if match:
            print(f"  ✓ MATCH! Groups: {match.groups()}")
            
            # Call the handler
            if callable(handler):
                result = handler(match)
                print(f"  Handler returned: {result}")
                
                if not result:
                    print("  ⚠️ Handler returned empty list!")
                    # Let's see why
                    if hasattr(agent, '_extract_digital_inputs') and 'digital_input' in pattern_str:
                        count = int(match.group(1))
                        print(f"  Extracted count: {count}")
                        if count <= 16:
                            print(f"  ⚠️ Count {count} might be below threshold for CNST_DIGITAL_IO_MIN_16")
        else:
            print(f"  ✗ No match")

async def main():
    """Run all diagnostics"""
    print("DIGITAL INPUT EXTRACTION DIAGNOSTICS")
    print("=" * 60)
    print()
    
    # Run diagnostics
    diagnose_patterns()
    matches = check_actual_patterns()
    await trace_full_extraction()
    test_extraction_method()
    check_pattern_execution_path()
    
    # Summary
    print("\n" + "=" * 60)
    print("DIAGNOSIS SUMMARY")
    print("=" * 60)
    
    if matches:
        print("✓ Patterns ARE matching the input")
        print("✗ But constraints aren't being generated")
        print("\nLikely causes:")
        print("1. The extraction method has a threshold issue")
        print("2. The handler returns empty list for value 16")
        print("3. The constraint ID doesn't exist for this range")
    else:
        print("✗ Patterns are NOT matching the input")
        print("\nLikely causes:")
        print("1. Pattern doesn't handle plural form")
        print("2. Pattern is too restrictive")
        print("3. Pattern isn't in io_patterns dict")

if __name__ == "__main__":
    asyncio.run(main())
