"""
Verification script to ensure Phase 1 is properly set up
Run this after removing old agents and fixing imports
"""

import sys
import os
import json
import asyncio
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_status(message, status='info'):
    """Print colored status messages"""
    if status == 'success':
        print(f"{GREEN}✓{RESET} {message}")
    elif status == 'error':
        print(f"{RED}✗{RESET} {message}")
    elif status == 'warning':
        print(f"{YELLOW}⚠{RESET} {message}")
    else:
        print(f"  {message}")

def check_file_exists(filepath, description):
    """Check if a critical file exists"""
    if Path(filepath).exists():
        print_status(f"{description} exists", 'success')
        return True
    else:
        print_status(f"{description} missing: {filepath}", 'error')
        return False

def check_old_files_removed():
    """Verify old MVP files are removed"""
    print("\n1. CHECKING OLD FILES REMOVED:")
    print("-" * 40)
    
    old_files = [
        ('src/agents/elicitor.py', 'Old RequirementsElicitor'),
        ('src/agents/completeness.py', 'Old CompletenessChecker'),
        ('src/agents/validator.py', 'Old ConstraintValidator'),
        ('src/agents/orchestrator.py', 'Old Orchestrator'),
        ('src/agents/agent_factory.py', 'Old Agent Factory')
    ]
    
    all_removed = True
    for filepath, description in old_files:
        if Path(filepath).exists():
            print_status(f"{description} still exists - should be deleted", 'warning')
            all_removed = False
        else:
            print_status(f"{description} removed", 'success')
    
    return all_removed

def check_new_files_exist():
    """Verify Phase 1 files are in place"""
    print("\n2. CHECKING PHASE 1 FILES:")
    print("-" * 40)
    
    required_files = [
        ('src/state/crdt_state_manager.py', 'CRDT State Manager'),
        ('src/orchestration/parallel_executor.py', 'Parallel Executor'),
        ('src/agents/requirements_elicitor.py', 'Requirements Elicitor Agent'),
        ('src/agents/specification_mapper.py', 'Specification Mapper Agent'),
        ('src/agents/constraint_validator.py', 'Constraint Validator Agent'),
        ('src/agents/resolution_agent.py', 'Resolution Agent'),
        ('data/useCase_phase1.json', 'Phase 1 Use Case Config')
    ]
    
    all_exist = True
    for filepath, description in required_files:
        if not check_file_exists(filepath, description):
            all_exist = False
    
    return all_exist

def check_imports():
    """Verify imports work correctly"""
    print("\n3. CHECKING IMPORTS:")
    print("-" * 40)
    
    try:
        # Check CRDT import
        from src.state.crdt_state_manager import CRDTStateManager, StateSnapshot
        print_status("CRDT State Manager imports", 'success')
    except ImportError as e:
        print_status(f"CRDT import failed: {e}", 'error')
        return False
    
    try:
        # Check Parallel Executor import
        from src.orchestration.parallel_executor import ParallelExecutor
        print_status("Parallel Executor imports", 'success')
    except ImportError as e:
        print_status(f"Parallel Executor import failed: {e}", 'error')
        return False
    
    try:
        # Check agent imports
        from src.agents.requirements_elicitor import RequirementsElicitorAgent
        from src.agents.specification_mapper import SpecificationMapperAgent
        from src.agents.constraint_validator import ConstraintValidatorAgent
        from src.agents.resolution_agent import ResolutionAgent
        print_status("All Phase 1 agents import", 'success')
    except ImportError as e:
        print_status(f"Agent import failed: {e}", 'error')
        return False
    
    return True

def check_agent_interfaces():
    """Verify agents have correct interface"""
    print("\n4. CHECKING AGENT INTERFACES:")
    print("-" * 40)
    
    try:
        from src.agents.requirements_elicitor import RequirementsElicitorAgent
        from src.agents.specification_mapper import SpecificationMapperAgent
        from src.agents.constraint_validator import ConstraintValidatorAgent
        from src.agents.resolution_agent import ResolutionAgent
        
        # Load config
        with open('data/useCase_phase1.json', 'r') as f:
            config = json.load(f)
        
        agents = [
            ('RequirementsElicitorAgent', RequirementsElicitorAgent),
            ('SpecificationMapperAgent', SpecificationMapperAgent),
            ('ConstraintValidatorAgent', ConstraintValidatorAgent),
            ('ResolutionAgent', ResolutionAgent)
        ]
        
        all_good = True
        for name, AgentClass in agents:
            try:
                # Check initialization
                agent = AgentClass(config)
                
                # Check for process_async method
                if hasattr(agent, 'process_async'):
                    print_status(f"{name} has process_async method", 'success')
                else:
                    print_status(f"{name} missing process_async method", 'error')
                    all_good = False
                    
            except Exception as e:
                print_status(f"{name} initialization failed: {e}", 'error')
                all_good = False
        
        return all_good
        
    except Exception as e:
        print_status(f"Interface check failed: {e}", 'error')
        return False

async def test_basic_execution():
    """Test basic parallel execution"""
    print("\n5. TESTING BASIC EXECUTION:")
    print("-" * 40)
    
    try:
        from src.state.crdt_state_manager import CRDTStateManager
        from src.orchestration.parallel_executor import ParallelExecutor
        
        # Load config
        with open('data/useCase_phase1.json', 'r') as f:
            config = json.load(f)
        
        # Create instances
        state_mgr = CRDTStateManager("verify-test", config.get('mutex_constraints', {}))
        executor = ParallelExecutor(state_mgr, config)
        
        # Test simple input
        test_input = "I need 16 digital inputs for outdoor monitoring"
        print(f"Test input: '{test_input}'")
        
        result = await executor.process_input(test_input)
        
        # Check results
        if result.success:
            print_status("Execution successful", 'success')
        else:
            print_status("Execution failed", 'error')
            return False
        
        # Check if constraints were extracted
        constraints = state_mgr.get_active_constraints()
        if constraints:
            print_status(f"Extracted {len(constraints)} constraints:", 'success')
            for c in constraints[:3]:
                print(f"    - {c.id}")
        else:
            print_status("No constraints extracted - check patterns", 'warning')
        
        # Check execution time
        if result.total_time > 0:
            print_status(f"Execution time: {result.total_time:.3f}s", 'success')
        else:
            print_status("Execution time is 0 - timing issue", 'warning')
        
        return True
        
    except Exception as e:
        print_status(f"Execution test failed: {e}", 'error')
        import traceback
        traceback.print_exc()
        return False

def check_parallel_executor_mocks():
    """Check if mock classes were removed from parallel_executor.py"""
    print("\n6. CHECKING MOCK CLASSES REMOVED:")
    print("-" * 40)
    
    try:
        with open('src/orchestration/parallel_executor.py', 'r') as f:
            content = f.read()
        
        # Check for mock class definitions
        if 'class RequirementsElicitorAgent:' in content and '# Mock' in content:
            print_status("Mock agents still present in parallel_executor.py", 'warning')
            print("  Remove the mock agent classes at the bottom of the file")
            return False
        else:
            print_status("Mock agents removed from parallel_executor.py", 'success')
            return True
            
    except Exception as e:
        print_status(f"Could not check parallel_executor.py: {e}", 'error')
        return False

def main():
    """Run all verification checks"""
    print("=" * 60)
    print("PHASE 1 SETUP VERIFICATION")
    print("=" * 60)
    
    results = {
        'old_removed': check_old_files_removed(),
        'new_exist': check_new_files_exist(),
        'imports': check_imports(),
        'interfaces': check_agent_interfaces(),
        'mocks_removed': check_parallel_executor_mocks()
    }
    
    # Run async test
    if all(results.values()):
        print("\nRunning execution test...")
        results['execution'] = asyncio.run(test_basic_execution())
    else:
        print("\n⚠️  Skipping execution test due to setup issues")
        results['execution'] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for check, passed_check in results.items():
        status = 'success' if passed_check else 'error'
        print_status(f"{check.replace('_', ' ').title()}: {'PASSED' if passed_check else 'FAILED'}", status)
    
    print("\n" + "-" * 40)
    if passed == total:
        print_status(f"ALL CHECKS PASSED ({passed}/{total}) 🎉", 'success')
        print("\nPhase 1 is properly set up! You can now run:")
        print("  python test_parallel_execution.py")
    else:
        print_status(f"Some checks failed ({passed}/{total})", 'error')
        print("\nPlease fix the issues above before running tests.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
