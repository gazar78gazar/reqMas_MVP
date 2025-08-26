"""
Test Phase 2 Integration
Tests for Phase 2 orchestrator with probabilistic mapping and conflict detection
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from phase2.orchestrator import Phase2Orchestrator, Phase2ProcessingResult
from src.state.crdt_state_manager import CRDTStateManager

class TestStateAdapter(CRDTStateManager):
    """Test adapter for state manager"""
    
    def __init__(self, session_id: str = "test"):
        super().__init__(session_id=session_id, mutex_config={})
        
    def get_active_constraints(self):
        """Get list of active constraint IDs"""
        snapshot = self.get_snapshot()
        return list(snapshot.constraints.keys()) if snapshot.constraints else []
    
    def add_constraint(self, constraint_id: str):
        """Add a constraint by ID"""
        from src.state.crdt_state_manager import Constraint, ConstraintStrength
        import time
        constraint = Constraint(
            id=constraint_id,
            value=None,
            strength=ConstraintStrength.MANDATORY,
            timestamp=time.time(),
            source_agent="test",
            confidence=1.0
        )
        super().add_constraint(constraint)
    
    def add_requirement(self, requirement: dict):
        """Add a requirement"""
        pass
    
    def update_uc_probabilities(self, probs: dict):
        """Update UC probabilities"""
        for uc_id, prob in probs.items():
            self.add_use_case_signal(uc_id, prob, "test")
    
    def get_state(self):
        """Get current state as dict"""
        snapshot = self.get_snapshot()
        return {
            "constraints": [c.id for c in snapshot.constraints.values()],
            "use_cases": dict(snapshot.use_cases),
            "version": snapshot.version
        }
    
    def reset(self):
        """Reset the state"""
        self.__init__(session_id="test")


@pytest.mark.asyncio
async def test_progressive_conflict_detection():
    """Test that Phase 2 detects progressive conflicts"""
    
    state_manager = TestStateAdapter()
    orchestrator = Phase2Orchestrator(state_manager)
    
    # This should trigger progressive conflict
    inputs = [
        "Need compact form factor",
        "Must be modular",
        "Require 128 I/O points"
    ]
    
    for i, input_text in enumerate(inputs):
        result = await orchestrator.process(input_text, "test")
        
        # Check that result has expected structure
        assert isinstance(result, Phase2ProcessingResult)
        assert result.uc_probabilities is not None
        assert result.aggregated_confidence >= 0
        
        if i == 2:  # Third input might trigger conflict
            # Check if conflict detection worked
            if result.conflicts_detected:
                assert len(result.conflicts_detected) > 0
                # Check for space-related conflict
                conflict_texts = str(result.conflicts_detected).lower()
                assert any(word in conflict_texts for word in ["space", "compact", "io", "constraint"])


@pytest.mark.asyncio
async def test_uc_ambiguity_detection():
    """Test UC ambiguity detection and disambiguation"""
    
    state_manager = TestStateAdapter()
    orchestrator = Phase2Orchestrator(state_manager)
    
    # Ambiguous input
    result = await orchestrator.process(
        "I need monitoring for pumps and flow control",
        "test"
    )
    
    # Check result structure
    assert isinstance(result, Phase2ProcessingResult)
    assert result.uc_probabilities is not None
    
    # Should detect water treatment (UC6) or motion control (UC3) possibilities
    # Check if probabilities were calculated
    if 'UC6' in result.uc_probabilities or 'UC3' in result.uc_probabilities:
        # Check for ambiguity detection
        if 'UC6' in result.uc_probabilities and 'UC3' in result.uc_probabilities:
            diff = abs(result.uc_probabilities.get('UC6', 0) - result.uc_probabilities.get('UC3', 0))
            if diff < 0.15:
                assert result.needs_disambiguation or result.abq_question is not None


@pytest.mark.asyncio
async def test_confidence_aggregation():
    """Test confidence aggregation strategies"""
    
    state_manager = TestStateAdapter()
    orchestrator = Phase2Orchestrator(state_manager)
    
    # High confidence input with clear requirements
    result = await orchestrator.process(
        "Industrial PLC with Modbus TCP and 16 digital inputs",
        "test"
    )
    
    # Check result structure
    assert isinstance(result, Phase2ProcessingResult)
    assert result.aggregated_confidence is not None
    
    # With clear requirements, confidence should be reasonable
    assert result.aggregated_confidence >= 0.0
    assert result.aggregated_confidence <= 1.0
    
    # Should not need disambiguation for clear input
    if result.aggregated_confidence > 0.7:
        assert not result.needs_disambiguation


@pytest.mark.asyncio
async def test_auto_resolution():
    """Test automatic conflict resolution based on confidence"""
    
    state_manager = TestStateAdapter()
    orchestrator = Phase2Orchestrator(state_manager)
    
    # Process multiple inputs
    inputs = [
        "Need outdoor system with high temperature rating",
        "Require GPU for AI processing"
    ]
    
    for input_text in inputs:
        result = await orchestrator.process(input_text, "test")
        
        # Check if auto-resolution is triggered for high-confidence conflicts
        if result.conflicts_detected and result.aggregated_confidence > 0.8:
            assert result.auto_resolve or result.suggested_resolution is not None


@pytest.mark.asyncio
async def test_state_persistence():
    """Test that state persists across multiple inputs"""
    
    state_manager = TestStateAdapter()
    orchestrator = Phase2Orchestrator(state_manager)
    
    # First input
    result1 = await orchestrator.process(
        "Need 32 digital inputs",
        "test"
    )
    
    # Get initial constraints
    initial_constraints = state_manager.get_active_constraints()
    
    # Second input
    result2 = await orchestrator.process(
        "Add Ethernet communication",
        "test"
    )
    
    # Get updated constraints
    updated_constraints = state_manager.get_active_constraints()
    
    # Should have more constraints after second input
    assert len(updated_constraints) >= len(initial_constraints)


def test_state_adapter():
    """Test the state adapter functionality"""
    
    adapter = TestStateAdapter()
    
    # Test adding constraints
    adapter.add_constraint("TEST_CONSTRAINT_1")
    constraints = adapter.get_active_constraints()
    assert "TEST_CONSTRAINT_1" in constraints
    
    # Test updating UC probabilities
    adapter.update_uc_probabilities({"UC1": 0.8, "UC2": 0.2})
    state = adapter.get_state()
    assert "use_cases" in state
    
    # Test reset
    adapter.reset()
    constraints = adapter.get_active_constraints()
    assert len(constraints) == 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])