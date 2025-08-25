"""
Diagnostic script to identify why certain patterns aren't matching
and constraints aren't being extracted
"""

import re
import json
import asyncio
from typing import Dict, List, Tuple
from src.agents.requirements_elicitor import RequirementsElicitorAgent
from src.state.crdt_state_manager import StateSnapshot

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def test_individual_patterns():
    """Test each pattern category to see what's defined and what works"""
    print("=" * 60)
    print("1. TESTING INDIVIDUAL PATTERN CATEGORIES")
    print("=" * 60)
    
    with open('data/useCase_phase1.json', 'r') as f:
        config = json.load(f)
    
    agent = RequirementsElicitorAgent(config)
    
    # Test inputs that failed in the conflict tests
    failing_inputs = [
        ("Must be fanless for reliability", "CNST_FANLESS"),
        ("Need Core i7 processor", "CNST_PROCESSOR_MIN_I7"),
        ("Require Core i7 processor", "CNST_PROCESSOR_MIN_I7"),
        ("Need Core i5 processor", "CNST_PROCESSOR_MIN_I5"),
        ("Must fit in compact DIN rail enclosure", "CNST_COMPACT_FORM"),
        ("Compact form factor required", "CNST_COMPACT_FORM"),
        ("Need GPU acceleration", "CNST_GPU_REQUIRED"),
        ("80 digital I/O points", "CNST_DIGITAL_IO_MIN_64"),
    ]
    
    print("\nTesting problematic inputs:")
    print("-" * 40)
    
    for test_input, expected_constraint in failing_inputs:
        print(f"\nInput: '{test_input}'")
        print(f"Expected: {expected_constraint}")
        
        test_lower = test_input.lower()
        matched = False
        
        # Check all pattern categories
        pattern_categories = [
            ('io_patterns', agent.io_patterns if hasattr(agent, 'io_patterns') else {}),
            ('env_patterns', agent.env_patterns if hasattr(agent, 'env_patterns') else {}),
            ('power_patterns', agent.power_patterns if hasattr(agent, 'power_patterns') else {}),
            ('comm_patterns', agent.comm_patterns if hasattr(agent, 'comm_patterns') else {}),
            ('performance_patterns', agent.performance_patterns if hasattr(agent, 'performance_patterns') else {})
        ]
        
        for category_name, patterns in pattern_categories:
            for pattern, handler in patterns.items():
                if re.search(pattern, test_lower):
                    matched = True
                    print(f"  {GREEN}✓ Matched in {category_name}: pattern '{pattern}'{RESET}")
                    
                    # Check what the handler returns
                    if callable(handler):
                        # For functions, we need to create a mock match
                        match = re.search(pattern, test_lower)
                        if match:
                            try:
                                result = handler(match)
                                if result:
                                    print(f"    Handler returned: {result}")
                                else:
                                    print(f"    {YELLOW}Handler returned empty!{RESET}")
                            except Exception as e:
                                print(f"    {RED}Handler error: {e}{RESET}")
                    else:
                        # For lists of constraint IDs
                        print(f"    Would add constraints: {handler}")
                        if expected_constraint in handler:
                            print(f"    {GREEN}✓ Contains expected constraint{RESET}")
                        else:
                            print(f"    {RED}✗ Missing expected constraint{RESET}")
        
        if not matched:
            print(f"  {RED}✗ NO PATTERN MATCHES THIS INPUT!{RESET}")


def check_missing_patterns():
    """Identify which patterns are completely missing"""
    print("\n" + "=" * 60)
    print("2. CHECKING FOR MISSING PATTERNS")
    print("=" * 60)
    
    with open('data/useCase_phase1.json', 'r') as f:
        config = json.load(f)
    
    agent = RequirementsElicitorAgent(config)
    
    # Keywords that should have patterns but might not
    keywords_to_check = [
        # Performance
        ('fanless', 'CNST_FANLESS'),
        ('fan-less', 'CNST_FANLESS'),
        ('no fan', 'CNST_FANLESS'),
        ('passive cooling', 'CNST_FANLESS'),
        ('i7', 'CNST_PROCESSOR_MIN_I7'),
        ('core i7', 'CNST_PROCESSOR_MIN_I7'),
        ('i5', 'CNST_PROCESSOR_MIN_I5'),
        ('core i5', 'CNST_PROCESSOR_MIN_I5'),
        ('gpu', 'CNST_GPU_REQUIRED'),
        ('graphics', 'CNST_GPU_REQUIRED'),
        
        # Form factor
        ('compact', 'CNST_COMPACT_FORM'),
        ('din rail', 'CNST_COMPACT_FORM'),
        ('din-rail', 'CNST_COMPACT_FORM'),
        ('small form', 'CNST_COMPACT_FORM'),
        
        # I/O specific values
        ('64 digital', 'CNST_DIGITAL_IO_MIN_64'),
        ('80 digital', 'CNST_DIGITAL_IO_MIN_64'),
        ('100 digital', 'CNST_DIGITAL_IO_MIN_64'),
        ('128 i/o', 'CNST_DIGITAL_IO_MIN_64'),
    ]
    
    print("\nChecking if keywords have patterns:")
    print("-" * 40)
    
    missing_patterns = []
    
    for keyword, expected_constraint in keywords_to_check:
        found = False
        
        # Check all patterns
        all_patterns = []
        if hasattr(agent, 'io_patterns'):
            all_patterns.extend(agent.io_patterns.keys())
        if hasattr(agent, 'env_patterns'):
            all_patterns.extend(agent.env_patterns.keys())
        if hasattr(agent, 'power_patterns'):
            all_patterns.extend(agent.power_patterns.keys())
        if hasattr(agent, 'performance_patterns'):
            all_patterns.extend(agent.performance_patterns.keys())
        
        for pattern in all_patterns:
            if re.search(pattern, keyword):
                found = True
                break
        
        if found:
            print(f"  {GREEN}✓{RESET} '{keyword}' has a pattern")
        else:
            print(f"  {RED}✗{RESET} '{keyword}' - NO PATTERN FOUND")
            missing_patterns.append((keyword, expected_constraint))
    
    if missing_patterns:
        print(f"\n{YELLOW}Missing patterns for:{RESET}")
        for keyword, constraint in missing_patterns:
            print(f"  - '{keyword}' → should map to {constraint}")


async def trace_extraction_flow():
    """Trace the full extraction flow for problematic inputs"""
    print("\n" + "=" * 60)
    print("3. TRACING FULL EXTRACTION FLOW")
    print("=" * 60)
    
    with open('data/useCase_phase1.json', 'r') as f:
        config = json.load(f)
    
    agent = RequirementsElicitorAgent(config)
    
    # Create mock snapshot
    snapshot = StateSnapshot(
        use_cases={},
        constraints={},
        resolutions=[],
        timestamp=0,
        version=0
    )
    
    # Test problematic inputs
    test_cases = [
        "Must be fanless for reliability",
        "Need Core i7 processor",
        "Must fit in compact DIN rail enclosure",
        "Need 80 digital I/O points"
    ]
    
    for test_input in test_cases:
        print(f"\nInput: '{test_input}'")
        print("-" * 40)
        
        # Process through agent
        result = await agent.process_async(test_input, snapshot, {})
        
        # Check what was extracted
        constraints = result.get('state_updates', {}).get('constraints', [])
        
        if constraints:
            print(f"  {GREEN}Extracted {len(constraints)} constraints:{RESET}")
            for c in constraints:
                print(f"    - {c['id']} (strength: {c.get('strength', 'N/A')})")
        else:
            print(f"  {RED}NO CONSTRAINTS EXTRACTED!{RESET}")
        
        # Check use cases
        use_cases = result.get('state_updates', {}).get('use_cases', {})
        if use_cases:
            print(f"  Use cases detected: {use_cases}")


def analyze_pattern_structure():
    """Analyze the structure of patterns to understand the issue"""
    print("\n" + "=" * 60)
    print("4. ANALYZING PATTERN STRUCTURE")
    print("=" * 60)
    
    with open('data/useCase_phase1.json', 'r') as f:
        config = json.load(f)
    
    agent = RequirementsElicitorAgent(config)
    
    # Count patterns by category
    categories = {
        'io_patterns': agent.io_patterns if hasattr(agent, 'io_patterns') else {},
        'env_patterns': agent.env_patterns if hasattr(agent, 'env_patterns') else {},
        'power_patterns': agent.power_patterns if hasattr(agent, 'power_patterns') else {},
        'comm_patterns': agent.comm_patterns if hasattr(agent, 'comm_patterns') else {},
        'performance_patterns': agent.performance_patterns if hasattr(agent, 'performance_patterns') else {}
    }
    
    print("\nPattern inventory:")
    print("-" * 40)
    
    for category_name, patterns in categories.items():
        print(f"\n{BLUE}{category_name}:{RESET} ({len(patterns)} patterns)")
        
        for i, (pattern, handler) in enumerate(patterns.items(), 1):
            # Show pattern
            print(f"  {i}. Pattern: '{pattern}'")
            
            # Check handler type
            if callable(handler):
                print(f"     Type: Function handler")
            elif isinstance(handler, list):
                print(f"     Type: Direct mapping to {handler}")
            else:
                print(f"     Type: Unknown ({type(handler)})")
            
            # Test with a simple match
            test_strings = {
                'io_patterns': '16 digital inputs',
                'env_patterns': 'outdoor harsh',
                'power_patterns': 'solar battery',
                'comm_patterns': 'ethernet modbus',
                'performance_patterns': 'real-time fast'
            }
            
            test_str = test_strings.get(category_name, 'test')
            if re.search(pattern, test_str):
                print(f"     {GREEN}✓ Pattern is valid regex{RESET}")
            
            if i >= 3:  # Show first 3 of each category
                remaining = len(patterns) - i
                if remaining > 0:
                    print(f"  ... and {remaining} more patterns")
                break


def suggest_fixes():
    """Suggest specific fixes based on analysis"""
    print("\n" + "=" * 60)
    print("5. SUGGESTED FIXES")
    print("=" * 60)
    
    print("\nAdd these patterns to requirements_elicitor.py:")
    print("-" * 40)
    
    # Missing patterns that should be added
    missing_patterns = {
        'env_patterns': [
            (r'fanless|fan-less|no\s*fan|passive\s*cooling', "['CNST_FANLESS']"),
            (r'compact|din\s*rail|din-rail|small\s*form', "['CNST_COMPACT_FORM']"),
        ],
        'performance_patterns': [
            (r'(?:core\s*)?i7(?:\s*processor)?', "['CNST_PROCESSOR_MIN_I7']"),
            (r'(?:core\s*)?i5(?:\s*processor)?', "['CNST_PROCESSOR_MIN_I5']"),
            (r'gpu|graphics\s*processing|graphics\s*acceleration', "['CNST_GPU_REQUIRED']"),
        ]
    }
    
    for category, patterns in missing_patterns.items():
        print(f"\n{BLUE}In {category}, add:{RESET}")
        for pattern, mapping in patterns:
            print(f"    r'{pattern}': {mapping},")
    
    print("\n" + YELLOW + "Fix extraction thresholds:" + RESET)
    print("In _extract_digital_inputs and _extract_digital_outputs:")
    print("  - For 64+ I/Os: Use CNST_DIGITAL_IO_MIN_64")
    print("  - For 80+ I/Os: Still use CNST_DIGITAL_IO_MIN_64")
    print("  - Consider adding CNST_DIGITAL_IO_MIN_128 if needed")


def test_specific_pattern():
    """Test a specific pattern in detail"""
    print("\n" + "=" * 60)
    print("6. TESTING SPECIFIC PATTERN IN DETAIL")
    print("=" * 60)
    
    # Test the "compact" issue specifically
    test_input = "Must fit in compact DIN rail enclosure"
    test_lower = test_input.lower()
    
    print(f"Testing: '{test_input}'")
    print("-" * 40)
    
    # Test different pattern variations
    pattern_tests = [
        r'compact',
        r'din\s*rail',
        r'din-rail',
        r'compact.*din.*rail',
        r'(?:compact|small|mini)',
    ]
    
    print("\nTrying different patterns:")
    for pattern in pattern_tests:
        match = re.search(pattern, test_lower)
        if match:
            print(f"  {GREEN}✓ '{pattern}' matches{RESET}")
            print(f"    Matched: '{match.group()}'")
        else:
            print(f"  {RED}✗ '{pattern}' doesn't match{RESET}")
    
    # Check what's currently happening
    print("\n" + YELLOW + "Current behavior:" + RESET)
    print("The input 'compact DIN rail' is incorrectly returning:")
    print("  - CNST_PROCESSOR_MIN_I5")
    print("  - CNST_GPU_REQUIRED")
    print("  - CNST_MEMORY_32GB")
    print("\nThis suggests a pattern is matching 'compact' but mapping to wrong constraints!")


async def main():
    """Run all diagnostic tests"""
    print(f"{BLUE}PATTERN MATCHING DIAGNOSTICS{RESET}")
    print("=" * 60)
    print("Diagnosing why certain constraints aren't being extracted\n")
    
    # Run all diagnostics
    test_individual_patterns()
    check_missing_patterns()
    await trace_extraction_flow()
    analyze_pattern_structure()
    suggest_fixes()
    test_specific_pattern()
    
    print("\n" + "=" * 60)
    print(f"{BLUE}DIAGNOSIS COMPLETE{RESET}")
    print("=" * 60)
    
    print("\n" + RED + "Key Findings:" + RESET)
    print("1. Missing patterns for: fanless, i7, i5, compact, DIN rail")
    print("2. Some patterns may be matching but returning wrong constraints")
    print("3. Need to add specific patterns for common phrases")
    print("\nCheck the SUGGESTED FIXES section above for specific code to add!")


if __name__ == "__main__":
    asyncio.run(main())
