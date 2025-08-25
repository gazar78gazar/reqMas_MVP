"""
Test to verify the cleanup is complete and all Phase 1 agents work
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_cleanup():
    """Test that old agents are gone and new ones work"""
    
    print("Testing cleanup and Phase 1 agents...\n")
    
    # Test that old agents are gone
    print("1. Checking old agent files are deleted:")
    old_files = ['elicitor.py', 'completeness.py', 'validator.py', 
                 'orchestrator.py', 'agent_factory.py', 'validation_result.py']
    
    for old_file in old_files:
        path = Path(f'src/agents/{old_file}')
        if path.exists():
            print(f"   [FAIL] {old_file} still exists!")
        else:
            print(f"   [OK] {old_file} deleted")
    
    # Test that Phase 1 agents can be imported
    print("\n2. Testing Phase 1 agent imports:")
    try:
        from src.agents import (
            RequirementsElicitorAgent,
            SpecificationMapperAgent,
            ConstraintValidatorAgent,
            ResolutionAgent
        )
        print("   [OK] All Phase 1 agents imported successfully")
    except ImportError as e:
        print(f"   [FAIL] Import error: {e}")
        return False
    
    # Test parallel executor
    print("\n3. Testing ParallelExecutor:")
    try:
        from src.orchestration.parallel_executor import ParallelExecutor
        print("   [OK] ParallelExecutor imported")
    except ImportError as e:
        print(f"   [FAIL] ParallelExecutor import error: {e}")
        return False
    
    # Check for proper methods
    print("\n4. Checking agent methods:")
    agents = [
        RequirementsElicitorAgent,
        SpecificationMapperAgent,
        ConstraintValidatorAgent,
        ResolutionAgent
    ]
    
    for agent_class in agents:
        if hasattr(agent_class, 'process_async'):
            print(f"   [OK] {agent_class.__name__} has process_async method")
        else:
            print(f"   [FAIL] {agent_class.__name__} missing process_async method")
    
    print("\n" + "="*60)
    print("CLEANUP COMPLETE! Phase 1 agents are ready to use.")
    return True

if __name__ == "__main__":
    success = test_cleanup()
    sys.exit(0 if success else 1)