"""
Test conflict detection, resolution, and ambiguity handling
Critical for production readiness
"""

import asyncio
import json
import time
from typing import Dict, List
from src.state.crdt_state_manager import CRDTStateManager
from src.orchestration.parallel_executor import ParallelExecutor


async def test_direct_mutex_conflicts():
    """Test direct MUTEX constraint conflicts"""
    print("=" * 60)
    print("TEST 1: DIRECT MUTEX CONFLICTS")
    print("=" * 60)
    print("Testing mutually exclusive constraints\n")
    
    with open('data/useCase_phase1.json', 'r') as f:
        config = json.load(f)
    
    # Test cases for known MUTEX pairs
    mutex_tests = [
        {
            "name": "Power vs Performance",
            "input1": "Need solar powered system with 10W max",
            "input2": "Require Core i7 processor",
            "expected_conflict": ("CNST_POWER_MAX_10W", "CNST_PROCESSOR_MIN_I7")
        },
        {
            "name": "Fanless vs High Performance",
            "input1": "Must be fanless for reliability",
            "input2": "Need Core i7 with GPU acceleration",
            "expected_conflict": ("CNST_FANLESS", "CNST_PROCESSOR_MIN_I7")
        },
        {
            "name": "Real-time vs Wireless",
            "input1": "Need 1ms deterministic response time",
            "input2": "Connect via WiFi for flexibility",
            "expected_conflict": ("CNST_LATENCY_MAX_1MS", "CNST_WIFI")
        },
        {
            "name": "Compact vs High I/O",
            "input1": "Must fit in compact DIN rail enclosure",
            "input2": "Need 80 digital I/O points",
            "expected_conflict": ("CNST_COMPACT_FORM", "CNST_DIGITAL_IO_MIN_64")
        }
    ]
    
    for test in mutex_tests:
        print(f"Testing: {test['name']}")
        print("-" * 40)
        
        state_mgr = CRDTStateManager(f"mutex-{test['name']}", config['mutex_constraints'])
        executor = ParallelExecutor(state_mgr, config)
        
        # First input
        print(f"Input 1: \"{test['input1']}\"")
        result1 = await executor.process_input(test['input1'])
        constraints1 = [c.id for c in state_mgr.get_active_constraints()]
        print(f"  Constraints: {constraints1}")
        
        # Second input (should conflict)
        print(f"Input 2: \"{test['input2']}\"")
        result2 = await executor.process_input(test['input2'])
        constraints2 = [c.id for c in state_mgr.get_active_constraints()]
        print(f"  Constraints: {constraints2}")
        
        # Check resolution
        if state_mgr.resolutions:
            resolution = state_mgr.resolutions[-1]
            print(f"\n  Resolution:")
            print(f"    - Chosen: {resolution.chosen}")
            print(f"    - Rejected: {resolution.constraint_a if resolution.chosen == resolution.constraint_b else resolution.constraint_b}")
            print(f"    - Reason: {resolution.reason}")
            print(f"    - Auto: {resolution.auto_resolved}")
            
            if resolution.auto_resolved:
                print("  ✓ Conflict auto-resolved")
            else:
                print("  ⚠ Required user intervention")
        else:
            print("  ❌ No resolution recorded - conflict may be undetected")
        
        print()


async def test_use_case_ambiguity():
    """Test ambiguous use case detection"""
    print("\n" + "=" * 60)
    print("TEST 2: USE CASE AMBIGUITY")
    print("=" * 60)
    print("Testing inputs that match multiple use cases\n")
    
    with open('data/useCase_phase1.json', 'r') as f:
        config = json.load(f)
    
    ambiguous_inputs = [
        {
            "input": "Industrial control with motion and machinery monitoring",
            "possible_ucs": ["UC3", "UC5"],  # Motion Control vs Industrial Automation
            "description": "Motion Control vs Industrial Automation"
        },
        {
            "input": "Outdoor monitoring with solar power and sensors",
            "possible_ucs": ["UC2", "UC6"],  # Solar vs Environmental Monitoring
            "description": "Solar Array vs Environmental Monitoring"
        },
        {
            "input": "High-speed data acquisition and testing",
            "possible_ucs": ["UC4", "UC12"],  # Quality Control vs Test Systems
            "description": "Quality Control vs Test & Measurement"
        },
        {
            "input": "Remote site monitoring with pumps and flow control",
            "possible_ucs": ["UC6", "UC10"],  # Water Treatment vs Mining
            "description": "Water Treatment vs Mining"
        }
    ]
    
    for test in ambiguous_inputs:
        print(f"Input: \"{test['input']}\"")
        print(f"Ambiguity: {test['description']}")
        print("-" * 40)
        
        state_mgr = CRDTStateManager(f"ambig-{test['description']}", config['mutex_constraints'])
        executor = ParallelExecutor(state_mgr, config)
        
        result = await executor.process_input(test['input'])
        
        # Get top use cases
        top_ucs = state_mgr.get_top_use_cases(3)
        
        if top_ucs:
            print("  Use cases detected:")
            for uc_id, confidence in top_ucs:
                marker = "→" if uc_id in test['possible_ucs'] else " "
                print(f"    {marker} {uc_id}: {confidence:.2f}")
        
        # Check if ambiguity was detected
        if len(top_ucs) > 1 and top_ucs[0][1] - top_ucs[1][1] < 0.3:
            print("  ⚠ Ambiguity detected - close confidence scores")
            
            # Check if resolution agent triggered
            if result.conflicts:
                for conflict in result.conflicts:
                    if 'use_case' in conflict.get('category', ''):
                        print("  ✓ Resolution agent triggered for UC selection")
                        break
                else:
                    print("  ❌ No UC resolution despite ambiguity")
        else:
            print("  ✓ Clear winner - no ambiguity")
        
        print()


async def test_progressive_conflict_buildup():
    """Test conflicts that emerge through accumulated requirements"""
    print("\n" + "=" * 60)
    print("TEST 3: PROGRESSIVE CONFLICT BUILD-UP")
    print("=" * 60)
    print("Conflicts that only appear as requirements accumulate\n")
    
    with open('data/useCase_phase1.json', 'r') as f:
        config = json.load(f)
    
    scenarios = [
        {
            "name": "Solar → Remote → AI Conflict",
            "steps": [
                ("Solar powered system", None),
                ("Remote monitoring capability", None),
                ("Low power consumption critical", None),
                ("Need AI-based anomaly detection", "GPU vs Low Power")
            ]
        },
        {
            "name": "Compact → Modular → High I/O Conflict",
            "steps": [
                ("Compact DIN rail mount", None),
                ("Modular expandable design", None),
                ("Start with 16 I/Os", None),
                ("Must support up to 128 I/Os", "Compact vs High I/O")
            ]
        },
        {
            "name": "Indoor → Precise → Harsh Environment",
            "steps": [
                ("Indoor installation", None),
                ("Precision temperature control", None),
                ("Standard operating environment", None),
                ("Actually needs to handle washdown", "Indoor vs IP69K")
            ]
        }
    ]
    
    for scenario in scenarios:
        print(f"Scenario: {scenario['name']}")
        print("-" * 40)
        
        state_mgr = CRDTStateManager(f"progressive-{scenario['name']}", config['mutex_constraints'])
        executor = ParallelExecutor(state_mgr, config)
        
        for i, (step_input, expected_conflict) in enumerate(scenario['steps'], 1):
            print(f"\nStep {i}: \"{step_input}\"")
            
            result = await executor.process_input(step_input)
            
            # Show current state
            constraints = [c.id for c in state_mgr.get_active_constraints()]
            print(f"  Active constraints: {len(constraints)}")
            if len(constraints) <= 5:
                for c_id in constraints:
                    print(f"    • {c_id}")
            
            # Check for conflicts
            if expected_conflict:
                print(f"  Expected conflict: {expected_conflict}")
                
                if result.conflicts or state_mgr.resolutions:
                    print("  ✓ Conflict detected!")
                    if state_mgr.resolutions:
                        latest = state_mgr.resolutions[-1]
                        print(f"    Resolution: {latest.reason}")
                else:
                    print("  ❌ Expected conflict not detected")
            elif result.conflicts:
                print("  ⚠ Unexpected conflict detected!")
        
        print()


async def test_recency_resolution():
    """Test recency-based auto-resolution"""
    print("\n" + "=" * 60)
    print("TEST 4: RECENCY-BASED AUTO-RESOLUTION")
    print("=" * 60)
    print("Testing 30-second recency window for corrections\n")
    
    with open('data/useCase_phase1.json', 'r') as f:
        config = json.load(f)
    
    state_mgr = CRDTStateManager("recency-test", config['mutex_constraints'])
    executor = ParallelExecutor(state_mgr, config)
    
    # Quick correction (within 30 seconds)
    print("Quick Correction Test:")
    print("-" * 40)
    
    print("User: \"Need low power 10W max\"")
    await executor.process_input("Need low power 10W max")
    
    await asyncio.sleep(0.5)  # Short delay
    
    print("User (0.5s later): \"Actually need i7 processor\"")
    result = await executor.process_input("Actually need i7 processor")
    
    if state_mgr.resolutions:
        resolution = state_mgr.resolutions[-1]
        if "recency" in resolution.reason.lower() or "correction" in resolution.reason.lower():
            print("  ✓ Recency rule applied - user correction detected")
            print(f"    Chose: {resolution.chosen}")
        else:
            print(f"  Different resolution: {resolution.reason}")
    
    # Delayed input (outside 30 seconds - simulated)
    print("\n\nDelayed Input Test (simulated >30s):")
    print("-" * 40)
    
    state_mgr2 = CRDTStateManager("recency-test-2", config['mutex_constraints'])
    executor2 = ParallelExecutor(state_mgr2, config)
    
    print("User: \"Must be fanless\"")
    await executor2.process_input("Must be fanless")
    
    # Simulate time passing by manipulating constraint timestamp
    # (In production this would be actual time delay)
    for constraint in state_mgr2.constraints.values():
        constraint.timestamp -= 35  # Make it seem 35 seconds old
    
    print("User (simulated 35s later): \"Need GPU processing\"")
    result2 = await executor2.process_input("Need GPU processing")
    
    if state_mgr2.resolutions:
        resolution2 = state_mgr2.resolutions[-1]
        if "recency" not in resolution2.reason.lower():
            print("  ✓ Recency rule NOT applied (too much time passed)")
            print(f"    Resolution: {resolution2.reason}")
        else:
            print("  ⚠ Recency rule incorrectly applied after 35s")


async def test_confidence_based_resolution():
    """Test confidence score impact on resolution"""
    print("\n" + "=" * 60)
    print("TEST 5: CONFIDENCE-BASED RESOLUTION")
    print("=" * 60)
    print("Testing how confidence scores affect conflict resolution\n")
    
    with open('data/useCase_phase1.json', 'r') as f:
        config = json.load(f)
    
    # Note: In current implementation, confidence differences > 0.3 trigger auto-resolution
    
    scenarios = [
        {
            "name": "High Confidence Difference",
            "input1": "Definitely need solar power",  # Should have high confidence
            "input2": "Maybe need high performance",  # Lower confidence from "maybe"
            "expected": "Solar should win (if confidence logic works)"
        },
        {
            "name": "Equal Confidence",
            "input1": "Need compact form factor",
            "input2": "Need 80 digital inputs",
            "expected": "Should require user resolution"
        }
    ]
    
    for scenario in scenarios:
        print(f"Scenario: {scenario['name']}")
        print("-" * 40)
        
        state_mgr = CRDTStateManager(f"confidence-{scenario['name']}", config['mutex_constraints'])
        executor = ParallelExecutor(state_mgr, config)
        
        print(f"Input 1: \"{scenario['input1']}\"")
        await executor.process_input(scenario['input1'])
        
        print(f"Input 2: \"{scenario['input2']}\"")
        await executor.process_input(scenario['input2'])
        
        if state_mgr.resolutions:
            resolution = state_mgr.resolutions[-1]
            print(f"\n  Resolution: {resolution.chosen}")
            print(f"  Reason: {resolution.reason}")
            print(f"  Auto: {resolution.auto_resolved}")
            
            if "confidence" in resolution.reason.lower():
                print("  ✓ Confidence-based resolution applied")
            else:
                print("  ℹ Different resolution logic used")
        else:
            print("  No resolution recorded")
        
        print(f"  Expected: {scenario['expected']}")
        print()


async def test_resolution_consistency():
    """Test that resolutions are consistent across similar scenarios"""
    print("\n" + "=" * 60)
    print("TEST 6: RESOLUTION CONSISTENCY")
    print("=" * 60)
    print("Testing if similar conflicts resolve consistently\n")
    
    with open('data/useCase_phase1.json', 'r') as f:
        config = json.load(f)
    
    # Run same conflict multiple times
    resolutions = []
    
    for run in range(3):
        print(f"Run {run + 1}:")
        
        state_mgr = CRDTStateManager(f"consistency-{run}", config['mutex_constraints'])
        executor = ParallelExecutor(state_mgr, config)
        
        # Same inputs each time
        await executor.process_input("Need fanless operation")
        await asyncio.sleep(0.1)  # Small delay to avoid recency rule
        await executor.process_input("Require i7 processor")
        
        if state_mgr.resolutions:
            chosen = state_mgr.resolutions[-1].chosen
            resolutions.append(chosen)
            print(f"  Resolved to: {chosen}")
        else:
            print("  No resolution")
    
    # Check consistency
    print("\nConsistency check:")
    if len(set(resolutions)) == 1:
        print("  ✓ Consistent - always chose:", resolutions[0])
    else:
        print("  ❌ Inconsistent resolutions:", resolutions)
        print("  This might indicate non-deterministic behavior")


async def test_mandatory_vs_recommended():
    """Test how strength levels affect conflict resolution"""
    print("\n" + "=" * 60)
    print("TEST 7: MANDATORY VS RECOMMENDED STRENGTH")
    print("=" * 60)
    print("Testing if mandatory constraints override recommended ones\n")
    
    with open('data/useCase_phase1.json', 'r') as f:
        config = json.load(f)
    
    state_mgr = CRDTStateManager("strength-test", config['mutex_constraints'])
    executor = ParallelExecutor(state_mgr, config)
    
    # First add a recommended constraint
    print("Step 1: Adding recommended constraint")
    # This would need to trigger a recommended constraint
    # In current implementation, most are mandatory (strength=10)
    await executor.process_input("IoT system with MQTT preferred")
    
    constraints_before = [c for c in state_mgr.get_active_constraints()]
    print(f"  Constraints: {[c.id for c in constraints_before]}")
    if constraints_before:
        print(f"  Strengths: {[c.strength.value for c in constraints_before]}")
    
    # Then add conflicting mandatory
    print("\nStep 2: Adding conflicting mandatory constraint")
    await executor.process_input("Actually need deterministic real-time control")
    
    constraints_after = [c for c in state_mgr.get_active_constraints()]
    print(f"  Constraints: {[c.id for c in constraints_after]}")
    
    # Check resolution
    if state_mgr.resolutions:
        resolution = state_mgr.resolutions[-1]
        if "mandatory" in resolution.reason.lower() or "strength" in resolution.reason.lower():
            print("\n  ✓ Strength-based resolution applied")
            print(f"    Reason: {resolution.reason}")
        else:
            print(f"\n  Resolution used different logic: {resolution.reason}")
    
    # Verify mandatory won
    mandatory_constraints = [c for c in constraints_after if c.strength.value == 10]
    if mandatory_constraints:
        print(f"  ✓ Mandatory constraints preserved: {[c.id for c in mandatory_constraints]}")


async def test_complex_multi_conflict():
    """Test handling multiple simultaneous conflicts"""
    print("\n" + "=" * 60)
    print("TEST 8: COMPLEX MULTI-CONFLICT SCENARIO")
    print("=" * 60)
    print("Testing multiple simultaneous conflicts\n")
    
    with open('data/useCase_phase1.json', 'r') as f:
        config = json.load(f)
    
    state_mgr = CRDTStateManager("multi-conflict", config['mutex_constraints'])
    executor = ParallelExecutor(state_mgr, config)
    
    # Build up multiple compatible constraints
    print("Building initial compatible state:")
    compatible_inputs = [
        "Industrial automation system",
        "Indoor installation",
        "Standard temperature range",
        "Modbus TCP communication"
    ]
    
    for inp in compatible_inputs:
        await executor.process_input(inp)
    
    initial_constraints = [c.id for c in state_mgr.get_active_constraints()]
    print(f"  Initial constraints: {initial_constraints}")
    
    # Now add multiple conflicting requirements at once
    print("\nAdding multiple conflicts simultaneously:")
    conflicting_input = "Actually need outdoor solar-powered compact system with 100 I/Os and GPU processing"
    
    result = await executor.process_input(conflicting_input)
    
    # This should trigger multiple conflicts:
    # - Indoor vs Outdoor
    # - Standard temp vs Extended temp
    # - Solar power vs GPU
    # - Compact vs 100 I/Os
    
    print(f"\n  Conflicts detected: {len(result.conflicts) if result.conflicts else 0}")
    if result.conflicts:
        for conflict in result.conflicts:
            print(f"    - {conflict}")
    
    print(f"\n  Resolutions made: {len(state_mgr.resolutions)}")
    for resolution in state_mgr.resolutions[-3:]:  # Show last 3
        print(f"    - {resolution.chosen} (rejected {resolution.constraint_a if resolution.chosen == resolution.constraint_b else resolution.constraint_b})")
        print(f"      Reason: {resolution.reason}")
    
    final_constraints = [c.id for c in state_mgr.get_active_constraints()]
    print(f"\n  Final constraints: {final_constraints}")
    
    # Analyze what changed
    removed = set(initial_constraints) - set(final_constraints)
    added = set(final_constraints) - set(initial_constraints)
    
    if removed:
        print(f"  Removed: {removed}")
    if added:
        print(f"  Added: {added}")


async def test_ambiguous_language_handling():
    """Test how system handles vague or ambiguous language"""
    print("\n" + "=" * 60)
    print("TEST 9: AMBIGUOUS LANGUAGE HANDLING")
    print("=" * 60)
    print("Testing vague requirements that could mean multiple things\n")
    
    with open('data/useCase_phase1.json', 'r') as f:
        config = json.load(f)
    
    ambiguous_phrases = [
        {
            "input": "Need fast processing",
            "interpretations": ["High CPU", "Low latency", "High sampling rate"],
            "description": "Fast could mean CPU speed or response time"
        },
        {
            "input": "System should be robust",
            "interpretations": ["Redundant power", "Extended temp", "Vibration resistant"],
            "description": "Robust could mean many things"
        },
        {
            "input": "Need good connectivity",
            "interpretations": ["Multiple protocols", "Wireless", "High bandwidth"],
            "description": "Good connectivity is subjective"
        },
        {
            "input": "Must handle extreme conditions",
            "interpretations": ["Temperature", "Humidity", "Hazardous area"],
            "description": "Extreme is context-dependent"
        }
    ]
    
    for test in ambiguous_phrases:
        print(f"Input: \"{test['input']}\"")
        print(f"Ambiguity: {test['description']}")
        print("-" * 40)
        
        state_mgr = CRDTStateManager(f"ambiguous-{test['input']}", config['mutex_constraints'])
        executor = ParallelExecutor(state_mgr, config)
        
        result = await executor.process_input(test['input'])
        
        # See what constraints were extracted
        constraints = [c.id for c in state_mgr.get_active_constraints()]
        
        if constraints:
            print(f"  System interpreted as:")
            for c_id in constraints:
                print(f"    - {c_id}")
        else:
            print("  ⚠ No constraints extracted from ambiguous input")
        
        print(f"  Possible interpretations: {test['interpretations']}")
        
        # Check if any expected interpretations matched
        matched = False
        for interp in test['interpretations']:
            if any(interp.upper().replace(' ', '_') in c_id for c_id in constraints):
                matched = True
                break
        
        if matched:
            print("  ✓ Matched at least one expected interpretation")
        else:
            print("  ℹ System chose different interpretation")
        
        print()


async def test_conflict_with_state_recovery():
    """Test if system maintains valid state after conflict resolution"""
    print("\n" + "=" * 60)
    print("TEST 10: STATE RECOVERY AFTER CONFLICTS")
    print("=" * 60)
    print("Testing if state remains valid after conflict resolution\n")
    
    with open('data/useCase_phase1.json', 'r') as f:
        config = json.load(f)
    
    state_mgr = CRDTStateManager("recovery-test", config['mutex_constraints'])
    executor = ParallelExecutor(state_mgr, config)
    
    # Build complex state
    print("Building complex initial state:")
    inputs = [
        "Water treatment plant",
        "Need 24 analog inputs for sensors",
        "8 digital outputs for pumps",
        "Outdoor installation IP65",
        "Temperature -20 to 60C",
        "Modbus TCP and MQTT protocols"
    ]
    
    for inp in inputs:
        await executor.process_input(inp)
    
    print(f"  Built state with {len(state_mgr.get_active_constraints())} constraints")
    print(f"  State hash: {state_mgr.get_state_hash()}")
    
    # Introduce conflict
    print("\nIntroducing conflict:")
    print("  Input: \"Actually needs to be solar powered 10W max\"")
    
    pre_conflict_state = state_mgr.export_state()
    await executor.process_input("Actually needs to be solar powered 10W max")
    post_conflict_state = state_mgr.export_state()
    
    # Check state validity
    print("\nState validation:")
    
    # 1. No duplicate constraints
    constraint_ids = [c.id for c in state_mgr.get_active_constraints()]
    if len(constraint_ids) == len(set(constraint_ids)):
        print("  ✓ No duplicate constraints")
    else:
        print("  ❌ Duplicate constraints found!")
    
    # 2. No conflicting constraints remain
    remaining_conflicts = []
    for category, rules in config['mutex_constraints'].items():
        for rule in rules:
            if rule['constraint_a'] in constraint_ids and rule['constraint_b'] in constraint_ids:
                remaining_conflicts.append((rule['constraint_a'], rule['constraint_b']))
    
    if not remaining_conflicts:
        print("  ✓ No MUTEX conflicts in final state")
    else:
        print(f"  ❌ Remaining conflicts: {remaining_conflicts}")
    
    # 3. State version incremented
    if post_conflict_state['version'] > pre_conflict_state['version']:
        print(f"  ✓ Version incremented: {pre_conflict_state['version']} → {post_conflict_state['version']}")
    else:
        print("  ❌ Version not incremented properly")
    
    # 4. Resolution recorded
    if state_mgr.resolutions:
        print(f"  ✓ {len(state_mgr.resolutions)} resolution(s) recorded")
    else:
        print("  ⚠ No resolutions recorded despite conflict")
    
    print(f"\nFinal state hash: {state_mgr.get_state_hash()}")
    print(f"Final constraints: {len(state_mgr.get_active_constraints())}")
    
    # Export for inspection if needed
    metrics = state_mgr.get_metrics()
    print(f"Auto-resolution rate: {metrics['auto_resolution_rate']:.1%}")
    print(f"Total conflicts encountered: {metrics['conflict_count']}")


async def main():
    """Run all conflict and ambiguity tests"""
    print("CONFLICT AND AMBIGUITY TEST SUITE")
    print("=" * 60)
    print("Testing conflict detection, resolution, and ambiguity handling\n")
    
    start_time = time.time()
    
    # Run all tests
    await test_direct_mutex_conflicts()
    await test_use_case_ambiguity()
    await test_progressive_conflict_buildup()
    await test_recency_resolution()
    await test_confidence_based_resolution()
    await test_resolution_consistency()
    
    # Summary
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("CONFLICT TESTING COMPLETE")
    print("=" * 60)
    print(f"Total execution time: {elapsed:.2f} seconds")
    print("\nKey areas tested:")
    print("  ✓ Direct MUTEX conflicts")
    print("  ✓ Use case ambiguity")
    print("  ✓ Progressive conflict build-up")
    print("  ✓ Recency-based resolution")
    print("  ✓ Confidence-based resolution")
    print("  ✓ Resolution consistency")
    print("\nCheck results above for any ❌ or ⚠ markers indicating issues")


if __name__ == "__main__":
    asyncio.run(main())
