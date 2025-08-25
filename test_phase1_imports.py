"""
Test script to verify Phase 1 agent imports work correctly
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all Phase 1 agents can be imported"""
    
    print("Testing Phase 1 agent imports...")
    
    try:
        # Test individual imports
        from src.agents.requirements_elicitor import RequirementsElicitorAgent
        print("✓ RequirementsElicitorAgent imported successfully")
        
        from src.agents.specification_mapper import SpecificationMapperAgent
        print("✓ SpecificationMapperAgent imported successfully")
        
        from src.agents.constraint_validator import ConstraintValidatorAgent
        print("✓ ConstraintValidatorAgent imported successfully")
        
        from src.agents.resolution_agent import ResolutionAgent
        print("✓ ResolutionAgent imported successfully")
        
        # Test imports from __init__.py
        from src.agents import (
            RequirementsElicitorAgent,
            SpecificationMapperAgent,
            ConstraintValidatorAgent,
            ResolutionAgent
        )
        print("\n✓ All Phase 1 agents imported successfully from __init__.py")
        
        # Test instantiation (will fail due to missing crdt_state_manager, but import should work)
        print("\nTesting agent class structure...")
        print(f"  RequirementsElicitorAgent methods: {[m for m in dir(RequirementsElicitorAgent) if not m.startswith('_')]}")
        print(f"  SpecificationMapperAgent methods: {[m for m in dir(SpecificationMapperAgent) if not m.startswith('_')]}")
        print(f"  ConstraintValidatorAgent methods: {[m for m in dir(ConstraintValidatorAgent) if not m.startswith('_')]}")
        print(f"  ResolutionAgent methods: {[m for m in dir(ResolutionAgent) if not m.startswith('_')]}")
        
        print("\n✓ All imports and class structures verified successfully!")
        return True
        
    except ImportError as e:
        print(f"\n✗ Import error: {e}")
        print("\nNote: The error about 'crdt_state_manager' is expected.")
        print("The agent files have been created but depend on crdt_state_manager.py")
        print("which needs to be in src/state/ directory.")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)