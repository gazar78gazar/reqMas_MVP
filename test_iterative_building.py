"""
Test iterative state building - how the system accumulates knowledge
over multiple user inputs in a conversation
"""

import asyncio
import json
import time
from typing import Dict, List
from src.state.crdt_state_manager import CRDTStateManager
from src.orchestration.parallel_executor import ParallelExecutor


async def test_progressive_refinement():
    """Test how system builds understanding progressively"""
    print("=" * 60)
    print("TEST 1: PROGRESSIVE REFINEMENT")
    print("=" * 60)
    print("User gradually provides more details about their system\n")
    
    with open('data/useCase_phase1.json', 'r') as f:
        config = json.load(f)
    
    state_mgr = CRDTStateManager("iterative-1", config['mutex_constraints'])
    executor = ParallelExecutor(state_mgr, config)
    
    # Simulate a real conversation flow
    conversation = [
        "I need a control system",
        "It's for industrial automation",
        "We have 24 digital inputs from sensors",
        "Also 8 analog inputs for temperature",
        "It needs to communicate via Modbus TCP",
        "The environment is outdoor installation",
        "Temperature range is -20 to 60 celsius",
        "We need remote monitoring capability"
    ]
    
    for i, user_input in enumerate(conversation, 1):
        print(f"User Input {i}: \"{user_input}\"")
        
        result = await executor.process_input(user_input)
        
        # Show incremental state building
        constraints = state_mgr.get_active_constraints()
        use_cases = state_mgr.get_top_use_cases(1)
        
        print(f"  State after input {i}:")
        print(f"    - Constraints: {len(constraints)} total")
        if constraints:
            latest = constraints[:2]  # Show latest 2
            for c in latest:
                print(f"      • {c.id}")
        
        if use_cases:
            print(f"    - Top UC: {use_cases[0][0]} ({use_cases[0][1]:.2f} confidence)")
        
        print(f"    - Completeness: {result.completeness_score:.1%}")
        print()
    
    # Final summary
    print("-" * 40)
    print("FINAL STATE SUMMARY:")
    print(f"  Total constraints collected: {len(state_mgr.get_active_constraints())}")
    print(f"  Final completeness: {result.completeness_score:.1%}")
    print(f"  State version: {state_mgr.version}")
    
    # List all constraints
    print("\n  All constraints identified:")
    for c in state_mgr.get_active_constraints():
        print(f"    - {c.id}: {c.value if hasattr(c, 'value') else 'defined'}")


async def test_correction_flow():
    """Test how system handles user corrections/changes"""
    print("\n" + "=" * 60)
    print("TEST 2: USER CORRECTIONS")
    print("=" * 60)
    print("User changes their mind or corrects previous inputs\n")
    
    with open('data/useCase_phase1.json', 'r') as f:
        config = json.load(f)
    
    state_mgr = CRDTStateManager("iterative-2", config['mutex_constraints'])
    executor = ParallelExecutor(state_mgr, config)
    
    corrections = [
        ("I need 8 digital inputs", "Actually, I need 32 digital inputs"),
        ("System will be indoor", "Sorry, it needs to be outdoor rated"),
        ("Standard temperature range", "Needs extended temperature -40 to 85C"),
        ("Basic processing is fine", "We need real-time processing under 1ms")
    ]
    
    for original, correction in corrections:
        print(f"Original: \"{original}\"")
        result1 = await executor.process_input(original)
        constraints_before = [c.id for c in state_mgr.get_active_constraints()]
        print(f"  Constraints: {constraints_before}")
        
        # Small delay to test recency
        await asyncio.sleep(0.1)
        
        print(f"Correction: \"{correction}\"")
        result2 = await executor.process_input(correction)
        constraints_after = [c.id for c in state_mgr.get_active_constraints()]
        print(f"  Constraints: {constraints_after}")
        
        # Check if correction was applied
        if constraints_before != constraints_after:
            print("  ✓ Correction applied successfully")
        else:
            print("  ⚠ No change detected")
        
        # Check for auto-resolutions
        if state_mgr.resolutions:
            latest_resolution = state_mgr.resolutions[-1]
            if latest_resolution.auto_resolved:
                print(f"  Auto-resolved: {latest_resolution.reason}")
        print()


async def test_context_accumulation():
    """Test how context affects subsequent interpretations"""
    print("\n" + "=" * 60)
    print("TEST 3: CONTEXT ACCUMULATION")
    print("=" * 60)
    print("How established context affects interpretation of ambiguous inputs\n")
    
    with open('data/useCase_phase1.json', 'r') as f:
        config = json.load(f)
    
    # Scenario A: Water treatment context
    print("Scenario A: Water Treatment Context")
    print("-" * 40)
    state_mgr_a = CRDTStateManager("iterative-3a", config['mutex_constraints'])
    executor_a = ParallelExecutor(state_mgr_a, config)
    
    await executor_a.process_input("Water treatment plant control")
    await executor_a.process_input("Need pump control")  # Ambiguous
    
    uc_a = state_mgr_a.get_top_use_cases(1)
    constraints_a = [c.id for c in state_mgr_a.get_active_constraints()]
    print(f"  Use case detected: {uc_a[0] if uc_a else 'None'}")
    print(f"  'Pump control' interpreted as: {constraints_a}")
    
    # Scenario B: Oil & Gas context
    print("\nScenario B: Oil & Gas Context")
    print("-" * 40)
    state_mgr_b = CRDTStateManager("iterative-3b", config['mutex_constraints'])
    executor_b = ParallelExecutor(state_mgr_b, config)
    
    await executor_b.process_input("Oil refinery automation")
    await executor_b.process_input("Need pump control")  # Same input, different context
    
    uc_b = state_mgr_b.get_top_use_cases(1)
    constraints_b = [c.id for c in state_mgr_b.get_active_constraints()]
    print(f"  Use case detected: {uc_b[0] if uc_b else 'None'}")
    print(f"  'Pump control' interpreted as: {constraints_b}")
    
    # Compare interpretations
    print("\n  Interpretation differences based on context:")
    if constraints_a != constraints_b:
        print("  ✓ Context affected interpretation (good!)")
        unique_a = set(constraints_a) - set(constraints_b)
        unique_b = set(constraints_b) - set(constraints_a)
        if unique_a:
            print(f"    Water context added: {unique_a}")
        if unique_b:
            print(f"    Oil context added: {unique_b}")
    else:
        print("  ⚠ Same interpretation regardless of context")


async def test_incremental_conflict_detection():
    """Test how conflicts emerge as requirements accumulate"""
    print("\n" + "=" * 60)
    print("TEST 4: INCREMENTAL CONFLICT DETECTION")
    print("=" * 60)
    print("Conflicts that only appear as requirements accumulate\n")
    
    with open('data/useCase_phase1.json', 'r') as f:
        config = json.load(f)
    
    state_mgr = CRDTStateManager("iterative-4", config['mutex_constraints'])
    executor = ParallelExecutor(state_mgr, config)
    
    # Start with compatible requirements
    requirements = [
        "Solar powered installation",      # CNST_POWER_MAX_10W
        "Remote monitoring needed",         # CNST_LTE
        "Outdoor environment",             # CNST_IP54
        "Small sensor network",            # Compatible so far
        "Temperature monitoring",          # Still OK
        "Actually need video analytics",  # GPU required - CONFLICT!
    ]
    
    print("Adding requirements incrementally:")
    print("-" * 40)
    
    for i, req in enumerate(requirements, 1):
        print(f"\n{i}. Adding: \"{req}\"")
        
        result = await executor.process_input(req)
        
        # Check for conflicts
        if result.conflicts:
            print("  🚨 CONFLICT DETECTED!")
            for conflict in result.conflicts:
                print(f"     {conflict}")
        
        # Check for auto-resolutions
        if state_mgr.resolutions:
            for resolution in state_mgr.resolutions:
                if resolution.timestamp > time.time() - 1:  # Recent
                    print(f"  ⚡ Auto-resolution: {resolution.chosen}")
                    print(f"     Reason: {resolution.reason}")
        
        # Show current valid constraints
        active = [c.id for c in state_mgr.get_active_constraints()]
        print(f"  Active constraints: {len(active)}")
        if len(active) <= 5:
            for constraint_id in active:
                print(f"    • {constraint_id}")


async def test_completeness_evolution():
    """Test how completeness score evolves with inputs"""
    print("\n" + "=" * 60)
    print("TEST 5: COMPLETENESS EVOLUTION")
    print("=" * 60)
    print("Track how completeness score changes with each input\n")
    
    with open('data/useCase_phase1.json', 'r') as f:
        config = json.load(f)
    
    state_mgr = CRDTStateManager("iterative-5", config['mutex_constraints'])
    executor = ParallelExecutor(state_mgr, config)
    
    # Inputs that should progressively increase completeness
    inputs = [
        "Industrial automation system",           # Use case hint
        "Need 48 digital inputs",                # I/O specification
        "16 analog inputs for sensors",          # More I/O
        "Modbus TCP and OPC-UA protocols",       # Communication
        "Outdoor installation IP65",             # Environment
        "Temperature -20 to 70 celsius",         # Environment detail
        "24VDC power supply",                    # Power
        "100W power budget",                     # Power detail
        "Redundant power supplies needed",       # Reliability
        "Real-time response under 10ms"         # Performance
    ]
    
    scores = []
    constraint_counts = []
    
    print("Input # | Completeness | Constraints | Input Summary")
    print("-" * 60)
    
    for i, user_input in enumerate(inputs, 1):
        result = await executor.process_input(user_input)
        
        scores.append(result.completeness_score)
        constraint_counts.append(len(state_mgr.get_active_constraints()))
        
        # Show first 30 chars of input
        input_summary = user_input[:30] + "..." if len(user_input) > 30 else user_input
        
        print(f"  {i:2d}    |    {result.completeness_score:5.1%}    |      {constraint_counts[-1]:2d}      | {input_summary}")
    
    # Analysis
    print("\n" + "-" * 40)
    print("COMPLETENESS ANALYSIS:")
    
    # Check if completeness increased monotonically
    increasing = all(scores[i] <= scores[i+1] for i in range(len(scores)-1))
    
    if increasing:
        print("  ✓ Completeness consistently increased")
    else:
        print("  ⚠ Completeness had some decreases:")
        for i in range(1, len(scores)):
            if scores[i] < scores[i-1]:
                print(f"    - After input {i+1}: {scores[i-1]:.1%} → {scores[i]:.1%}")
    
    print(f"\n  Final metrics:")
    print(f"    - Starting completeness: {scores[0]:.1%}")
    print(f"    - Final completeness: {scores[-1]:.1%}")
    print(f"    - Total improvement: {(scores[-1] - scores[0]):.1%}")
    print(f"    - Constraints collected: {constraint_counts[-1]}")
    print(f"    - State version: {state_mgr.version}")


async def main():
    """Run all iterative state building tests"""
    print("ITERATIVE STATE BUILDING TEST SUITE")
    print("=" * 60)
    print("Testing how the system accumulates and refines state over multiple inputs\n")
    
    start_time = time.time()
    
    # Run all tests
    await test_progressive_refinement()
    await test_correction_flow()
    await test_context_accumulation()
    await test_incremental_conflict_detection()
    await test_completeness_evolution()
    
    # Summary
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("ITERATIVE TESTING COMPLETE")
    print("=" * 60)
    print(f"Total execution time: {elapsed:.2f} seconds")
    print("\nKey areas tested:")
    print("  ✓ Progressive refinement")
    print("  ✓ User corrections")
    print("  ✓ Context accumulation")
    print("  ✓ Incremental conflicts")
    print("  ✓ Completeness evolution")


if __name__ == "__main__":
    asyncio.run(main())
