import sys
import os
from pathlib import Path
import json
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.state.simple_state import SimpleState
from src.logging.decision_logger import DecisionLogger
from src.agents.orchestrator import Orchestrator


class TestOrchestratorIntegration:
    """Test orchestrator with state and logging"""
    
    def test_initial_routing(self):
        """Test routing with empty state"""
        logger = DecisionLogger("test-orch-001")
        orchestrator = Orchestrator(logger)
        state = SimpleState(session_id="test-orch-001")
        
        # Should route to elicitor for empty state
        next_agent = orchestrator.route(state)
        assert next_agent == "elicitor"
        
        # Check that decision was logged
        assert len(state.decision_log) == 1
        assert state.decision_log[0]["agent"] == "orchestrator"
        assert "route_to_elicitor" in state.decision_log[0]["decision"]
        
        # Check logger file
        logs = logger.get_session_logs()
        assert len(logs) == 1
        assert logs[0]["agent"] == "orchestrator"
    
    def test_completeness_routing(self):
        """Test routing based on completeness score"""
        logger = DecisionLogger("test-orch-002")
        orchestrator = Orchestrator(logger)
        state = SimpleState(session_id="test-orch-002")
        
        # Add some requirements but low completeness
        state.add_requirement("I/O", "Input?", "Keyboard")
        state.completeness_score = 0.5
        
        next_agent = orchestrator.route(state)
        assert next_agent == "completeness"
        
        # Check reasoning
        decision = state.decision_log[0]
        assert any("0.50" in r or "0.5" in r for r in decision["reasoning"])
        assert any("threshold" in r.lower() for r in decision["reasoning"])
    
    def test_validation_routing(self):
        """Test routing when ready for validation"""
        logger = DecisionLogger("test-orch-003")
        orchestrator = Orchestrator(logger)
        state = SimpleState(session_id="test-orch-003")
        
        # Set up complete state
        state.add_requirement("I/O", "Input?", "Keyboard")
        state.add_requirement("Power", "Power?", "500W")
        state.completeness_score = 0.9
        
        next_agent = orchestrator.route(state)
        assert next_agent == "validator"
        
        # Check state updates
        assert state.current_agent == "validator"
    
    def test_iteration_limit(self):
        """Test that iteration limit prevents infinite loops"""
        logger = DecisionLogger("test-orch-004")
        orchestrator = Orchestrator(logger)
        state = SimpleState(session_id="test-orch-004")
        
        # Set iteration count at limit
        state.iteration_count = 3
        state.add_requirement("I/O", "Input?", "Keyboard")
        
        next_agent = orchestrator.route(state)
        assert next_agent == "END"
        
        # Check reasoning mentions iteration limit
        decision = state.decision_log[0]
        assert any("maximum" in r.lower() for r in decision["reasoning"])
    
    def test_error_handling(self):
        """Test error processing"""
        logger = DecisionLogger("test-orch-005")
        orchestrator = Orchestrator(logger)
        state = SimpleState(session_id="test-orch-005")
        
        # Process an error
        error = Exception("Test error in elicitor")
        next_action = orchestrator.process_error(state, error, "elicitor")
        
        assert next_action == "END"
        
        # Check error was logged
        errors = logger.get_errors()
        assert len(errors) == 1
        assert "Test error" in errors[0]["error"]
        
        # Check state has error decision
        assert len(state.decision_log) == 1
        assert state.decision_log[0]["decision"] == "ERROR"
    
    def test_should_continue(self):
        """Test continuation logic"""
        logger = DecisionLogger("test-orch-006")
        orchestrator = Orchestrator(logger)
        
        # Test normal state - should continue
        state1 = SimpleState(session_id="test-1")
        state1.iteration_count = 1
        assert orchestrator.should_continue(state1) == True
        
        # Test at iteration limit - should stop
        state2 = SimpleState(session_id="test-2")
        state2.iteration_count = 3
        assert orchestrator.should_continue(state2) == False
        
        # Test with END agent - should stop
        state3 = SimpleState(session_id="test-3")
        state3.current_agent = "END"
        assert orchestrator.should_continue(state3) == False
        
        # Test with multiple errors - should stop
        state4 = SimpleState(session_id="test-4")
        state4.add_decision("agent1", "ERROR", ["error"])
        state4.add_decision("agent2", "ERROR", ["error"])
        assert orchestrator.should_continue(state4) == False
    
    def test_routing_summary(self):
        """Test getting routing summary"""
        logger = DecisionLogger("test-orch-007")
        orchestrator = Orchestrator(logger)
        state = SimpleState(session_id="test-orch-007")
        
        # Simulate multiple routing decisions
        orchestrator.route(state)  # Should route to elicitor
        
        state.add_requirement("I/O", "Input?", "Keyboard")
        state.iteration_count = 1
        orchestrator.route(state)  # Should route to completeness
        
        state.completeness_score = 0.9
        state.iteration_count = 2
        orchestrator.route(state)  # Should route to validator
        
        summary = orchestrator.get_routing_summary(state)
        
        assert summary["total_routes"] == 3
        assert "route_to_elicitor" in summary["routes"]
        assert "route_to_completeness" in summary["routes"]
        assert "route_to_validator" in summary["routes"]
        assert summary["final_completeness"] == 0.9
        assert summary["iterations"] == 2
    
    def test_log_file_creation(self):
        """Test that log files are created in correct location"""
        session_id = "test-logs-001"
        logger = DecisionLogger(session_id)
        orchestrator = Orchestrator(logger)
        state = SimpleState(session_id=session_id)
        
        # Make a routing decision
        orchestrator.route(state)
        
        # Check log file exists
        log_file = Path(f"logs/sessions/{session_id}/decisions.jsonl")
        assert log_file.exists()
        
        # Read and verify content
        with open(log_file, 'r', encoding='utf-8') as f:
            line = f.readline()
            log_entry = json.loads(line)
            assert log_entry["session_id"] == session_id
            assert log_entry["agent"] == "orchestrator"
    
    def test_state_persistence(self):
        """Test that state can be saved and loaded"""
        state = SimpleState(session_id="test-persist-001")
        
        # Add some data
        state.add_requirement("I/O", "Input devices?", "Keyboard, Mouse")
        state.add_requirement("Power", "Power requirements?", "500W")
        state.completeness_score = 0.75
        state.iteration_count = 2
        state.add_decision("orchestrator", "route_to_validator", ["Ready for validation"])
        
        # Save to JSON
        json_str = state.to_json()
        
        # Save to file
        test_file = Path("logs/test_state.json")
        test_file.parent.mkdir(exist_ok=True)
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(json_str)
        
        # Load from file
        with open(test_file, 'r', encoding='utf-8') as f:
            loaded_json = f.read()
        
        loaded_state = SimpleState.from_json(loaded_json)
        
        # Verify loaded state
        assert loaded_state.session_id == "test-persist-001"
        assert len(loaded_state.requirements) == 2
        assert loaded_state.completeness_score == 0.75
        assert loaded_state.iteration_count == 2
        assert len(loaded_state.decision_log) == 1
        
        # Clean up
        test_file.unlink()


class TestFullIntegration:
    """Test complete flow with all components"""
    
    def test_complete_flow(self):
        """Test a complete flow through multiple iterations"""
        session_id = "test-full-001"
        logger = DecisionLogger(session_id)
        orchestrator = Orchestrator(logger)
        state = SimpleState(session_id=session_id)
        
        # Iteration 1: Empty state
        next_agent = orchestrator.route(state)
        assert next_agent == "elicitor"
        
        # Simulate elicitor adding requirements
        state.add_requirement("I/O", "What input devices?", "Keyboard and mouse")
        state.add_requirement("Power", "Power budget?", "500W")
        state.iteration_count += 1
        
        # Iteration 2: Check completeness
        next_agent = orchestrator.route(state)
        assert next_agent == "completeness"
        
        # Simulate completeness checker
        state.completeness_score = 0.9
        state.iteration_count += 1
        
        # Iteration 3: Validate
        next_agent = orchestrator.route(state)
        assert next_agent == "validator"
        
        # Get summary
        summary = orchestrator.get_routing_summary(state)
        assert summary["total_routes"] == 3
        assert summary["final_completeness"] == 0.9
        
        # Check logs
        session_logs = logger.get_session_logs()
        assert len(session_logs) == 3  # Three routing decisions
        
        # Check all logs are for orchestrator
        for log in session_logs:
            assert log["agent"] == "orchestrator"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])