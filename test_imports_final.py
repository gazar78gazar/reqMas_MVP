"""
Final test to verify all imports are working correctly
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_all_imports():
    """Test that all Phase 1 components can be imported"""
    
    print("Testing all Phase 1 imports...\n")
    
    errors = []
    
    # Test Phase 1 agent imports
    try:
        from src.agents.requirements_elicitor import RequirementsElicitorAgent
        print("[OK] RequirementsElicitorAgent imported")
    except ImportError as e:
        errors.append(f"RequirementsElicitorAgent: {e}")
        print(f"[FAIL] RequirementsElicitorAgent: {e}")
    
    try:
        from src.agents.specification_mapper import SpecificationMapperAgent
        print("[OK] SpecificationMapperAgent imported")
    except ImportError as e:
        errors.append(f"SpecificationMapperAgent: {e}")
        print(f"[FAIL] SpecificationMapperAgent: {e}")
    
    try:
        from src.agents.constraint_validator import ConstraintValidatorAgent
        print("[OK] ConstraintValidatorAgent imported")
    except ImportError as e:
        errors.append(f"ConstraintValidatorAgent: {e}")
        print(f"[FAIL] ConstraintValidatorAgent: {e}")
    
    try:
        from src.agents.resolution_agent import ResolutionAgent
        print("[OK] ResolutionAgent imported")
    except ImportError as e:
        errors.append(f"ResolutionAgent: {e}")
        print(f"[FAIL] ResolutionAgent: {e}")
    
    # Test parallel executor import
    try:
        from src.orchestration.parallel_executor import ParallelExecutor
        print("[OK] ParallelExecutor imported")
    except ImportError as e:
        errors.append(f"ParallelExecutor: {e}")
        print(f"[FAIL] ParallelExecutor: {e}")
    
    # Test CRDT state manager import (this will likely fail but let's check)
    try:
        from src.state.crdt_state_manager import CRDTStateManager, StateSnapshot, ConstraintStrength
        print("[OK] CRDTStateManager imported")
    except ImportError as e:
        errors.append(f"CRDTStateManager: {e}")
        print(f"[FAIL] CRDTStateManager: {e}")
    
    # Test imports from __init__.py
    try:
        from src.agents import (
            RequirementsElicitorAgent,
            SpecificationMapperAgent,
            ConstraintValidatorAgent,
            ResolutionAgent
        )
        print("[OK] All Phase 1 agents imported from __init__.py")
    except ImportError as e:
        errors.append(f"__init__.py imports: {e}")
        print(f"[FAIL] __init__.py imports: {e}")
    
    print("\n" + "="*60)
    if errors:
        print(f"ERRORS FOUND ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")
        print("\nNOTE: The CRDTStateManager import error is expected")
        print("as the crdt_state_manager.py file needs to be created in src/state/")
    else:
        print("[SUCCESS] All imports successful!")
    
    return len(errors) == 0

if __name__ == "__main__":
    success = test_all_imports()
    sys.exit(0 if success else 1)