"""
Test script for Phase 1 Parallel Execution Framework
Run this from project root: python test_parallel_execution.py
"""

import asyncio
import json
import time
from typing import Dict, List

# Import from src directories
from src.state.crdt_state_manager import CRDTStateManager, Constraint, ConstraintStrength
from src.orchestration.parallel_executor import ParallelExecutor


def load_test_config():
    """Load configuration from cleaned useCase.json"""
    # In production, this loads from data/useCase_phase1.json
    config = {
        "use_cases": {
            "UC1": {"name": "Power Substation Management"},
            "UC2": {"name": "PV/Solar Array Monitoring"},
            "UC3": {"name": "Motion Control Systems"},
            "UC6": {"name": "Water Treatment Monitoring"}
        },
        "mutex_constraints": {
            "power_performance": [
                {"constraint_a": "CNST_POWER_MAX_10W", "constraint_b": "CNST_PROCESSOR_MIN_I7"},
                {"constraint_a": "CNST_POWER_MAX_10W", "constraint_b": "CNST_GPU_REQUIRED"},
                {"constraint_a": "CNST_FANLESS", "constraint_b": "CNST_PROCESSOR_MIN_I7"}
            ],
            "latency_connectivity": [
                {"constraint_a": "CNST_LATENCY_MAX_1MS", "constraint_b": "CNST_WIFI"},
                {"constraint_a": "CNST_LATENCY_MAX_1MS", "constraint_b": "CNST_LTE"}
            ],
            "form_factor": [
                {"constraint_a": "CNST_COMPACT_FORM", "constraint_b": "CNST_DIGITAL_IO_MIN_64"}
            ]
        }
    }
    return config


def get_test_scenarios() -> List[Dict]:
    """Get the 15 test scenarios for Phase 1"""
    return [
        # Scenario 1: Compatible (Happy Path)
        {
            "id": "test_001",
            "scenario": "compatible_happy",
            "input": "Need pH monitoring and flow meters for water treatment",
            "expected_constraints": ["CNST_ANALOG_IO_MIN_8"],
            "expected_uc": "UC6"
        },
        {
            "id": "test_002",
            "scenario": "compatible_happy",
            "input": "I need 16 digital inputs for outdoor industrial monitoring",
            "expected_constraints": ["CNST_DIGITAL_IO_MIN_16", "CNST_IP54", "CNST_TEMP_EXTENDED"],
            "expected_uc": None
        },
        
        # Scenario 2: MUTEX Conflicts
        {
            "id": "test_003",
            "scenario": "mutex_conflict",
            "inputs": [
                "System needs to run on solar power with 10W maximum",
                "Actually need Core i7 processor for AI processing"
            ],
            "expected_conflict": True,
            "expected_resolution": "auto or user choice"
        },
        {
            "id": "test_004",
            "scenario": "mutex_conflict", 
            "inputs": [
                "Need deterministic 1ms latency for safety",
                "Connect via WiFi for remote access"
            ],
            "expected_conflict": True,
            "expected_resolution": "auto-resolve to wired"
        },
        
        # Scenario 3: UC Conflicts
        {
            "id": "test_005",
            "scenario": "uc_conflict",
            "inputs": [
                "Setting up solar panel monitoring system",
                "Actually this is for motion control with 6 axes"
            ],
            "expected_uc_change": ("UC2", "UC3")
        },
        
        # Edge Cases
        {
            "id": "test_006",
            "scenario": "edge_high_io",
            "input": "Need 300 digital inputs and 200 analog outputs",
            "expected_constraints": ["CNST_DIGITAL_IO_MIN_64"],
            "expected_warning": "exceeds single controller limits"
        }
    ]


async def run_single_test(executor: ParallelExecutor, test_case: Dict) -> Dict:
    """Run a single test scenario"""
    print(f"\n{'='*60}")
    print(f"Test {test_case['id']}: {test_case['scenario']}")
    print(f"{'='*60}")
    
    results = {}
    
    if 'input' in test_case:
        # Single input test
        print(f"Input: {test_case['input']}")
        result = await executor.process_input(test_case['input'])
        
        print(f"\nExecution time: {result.total_time:.3f}s")
        print(f"Completeness: {result.completeness_score:.1%}")
        
        # Show detected use cases
        top_ucs = executor.state_manager.get_top_use_cases(3)
        if top_ucs:
            print(f"\nDetected Use Cases:")
            for uc_id, confidence in top_ucs:
                print(f"  - {uc_id}: {confidence:.2f}")
        
        # Show active constraints
        constraints = executor.state_manager.get_active_constraints()
        if constraints:
            print(f"\nActive Constraints:")
            for c in constraints[:5]:  # Show top 5
                print(f"  - {c.id} (strength: {c.strength.value}, confidence: {c.confidence:.2f})")
        
        # Check conflicts
        if result.conflicts:
            print(f"\nConflicts detected: {len(result.conflicts)}")
            for conflict in result.conflicts:
                print(f"  - {conflict['type']}: {conflict['constraint']}")
        
        results['single'] = result
        
    elif 'inputs' in test_case:
        # Multiple input test (for conflict scenarios)
        for i, input_text in enumerate(test_case['inputs'], 1):
            print(f"\nInput {i}: {input_text}")
            result = await executor.process_input(input_text)
            
            if result.conflicts:
                print(f"  ⚠️  Conflict detected: {result.conflicts[0]['message']}")
            
            constraints = executor.state_manager.get_active_constraints()
            print(f"  Active constraints: {[c.id for c in constraints]}")
            
            results[f'step_{i}'] = result
    
    # Show final state metrics
    metrics = executor.state_manager.get_metrics()
    print(f"\nState Metrics:")
    print(f"  - Version: {metrics['version']}")
    print(f"  - Total constraints: {metrics['total_constraints']}")
    print(f"  - Auto-resolution rate: {metrics['auto_resolution_rate']:.1%}")
    print(f"  - Conflicts encountered: {metrics['conflict_count']}")
    
    return results


async def run_performance_test(executor: ParallelExecutor):
    """Test parallel execution performance"""
    print(f"\n{'='*60}")
    print("PERFORMANCE TEST")
    print(f"{'='*60}")
    
    test_inputs = [
        "Simple requirement with 10 digital inputs",
        "Complex requirement with motion control, 6 axes, deterministic timing, safety integration",
        "Need outdoor system with solar power, remote monitoring, water treatment"
    ]
    
    for input_text in test_inputs:
        print(f"\nInput: {input_text[:50]}...")
        
        # Measure execution time
        times = []
        for _ in range(3):
            start = time.time()
            result = await executor.process_input(input_text)
            times.append(time.time() - start)
        
        avg_time = sum(times) / len(times)
        print(f"  Average execution time: {avg_time:.3f}s")
        print(f"  Agent results:")
        for agent_result in result.agent_results:
            print(f"    - {agent_result.agent_type.value}: {agent_result.execution_time:.3f}s")


async def main():
    """Main test execution"""
    print("Phase 1 Parallel Execution Framework Test")
    print("==========================================")
    
    # Load configuration
    config = load_test_config()
    
    # Initialize state manager
    state_manager = CRDTStateManager(
        session_id="test-session-001",
        mutex_config=config['mutex_constraints']
    )
    
    # Initialize parallel executor
    executor = ParallelExecutor(
        state_manager=state_manager,
        use_case_config=config,
        timeout_seconds=3.0
    )
    
    # Run test scenarios
    test_scenarios = get_test_scenarios()
    
    # Run first 3 tests as examples
    for test_case in test_scenarios:
        await run_single_test(executor, test_case)
        
        # Reset state for next test
        if test_case != test_scenarios[-1]:
            state_manager = CRDTStateManager(
                session_id=f"test-{test_case['id']}",
                mutex_config=config['mutex_constraints']
            )
            executor.state_manager = state_manager
    
    # Run performance test
    await run_performance_test(executor)
    
    # Final summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    final_metrics = executor.get_metrics()
    print(f"Total executions: {final_metrics['execution_count']}")
    print(f"Average time: {final_metrics['average_execution_time']:.3f}s")
    print(f"State version: {final_metrics['state_metrics']['version']}")
    print(f"Auto-resolution rate: {final_metrics['state_metrics']['auto_resolution_rate']:.1%}")


if __name__ == "__main__":
    # Run async main
    asyncio.run(main())
