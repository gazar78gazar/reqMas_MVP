import sys
import os
from pathlib import Path
import json
from datetime import datetime
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.state.simple_state import SimpleState, RequirementEntry
from src.logging.decision_logger import DecisionLogger


class TestSimpleState:
    """Test state management functionality"""
    
    def test_state_creation(self):
        """Test that state can be created with defaults"""
        state = SimpleState(session_id="test-001")
        
        assert state.session_id == "test-001"
        assert state.messages == []
        assert state.requirements == []
        assert state.completeness_score == 0.0
        assert state.current_agent == "orchestrator"
        assert state.iteration_count == 0
    
    def test_add_requirement(self):
        """Test adding requirements to state"""
        state = SimpleState(session_id="test-002")
        
        state.add_requirement(
            category="I/O",
            question="What input devices will you use?",
            answer="Keyboard and mouse"
        )
        
        assert len(state.requirements) == 1
        req = state.requirements[0]
        assert req.category == "I/O"
        assert req.question == "What input devices will you use?"
        assert req.answer == "Keyboard and mouse"
        assert isinstance(req.timestamp, datetime)
    
    def test_add_message(self):
        """Test adding messages to conversation history"""
        state = SimpleState(session_id="test-003")
        
        state.add_message("user", "I need a gaming PC")
        state.add_message("assistant", "Let me help you with that")
        
        assert len(state.messages) == 2
        assert state.messages[0]["role"] == "user"
        assert state.messages[0]["content"] == "I need a gaming PC"
        assert "timestamp" in state.messages[0]
    
    def test_json_serialization(self):
        """Test JSON round-trip serialization"""
        state = SimpleState(session_id="test-004")
        state.add_requirement("Power", "What's your power budget?", "500W")
        state.add_message("user", "Test message")
        state.completeness_score = 0.75
        state.iteration_count = 2
        
        # Serialize to JSON
        json_str = state.to_json()
        assert isinstance(json_str, str)
        
        # Parse JSON to verify structure
        data = json.loads(json_str)
        assert data["session_id"] == "test-004"
        assert data["completeness_score"] == 0.75
        assert data["iteration_count"] == 2
        
        # Deserialize from JSON
        state2 = SimpleState.from_json(json_str)
        assert state2.session_id == state.session_id
        assert state2.completeness_score == state.completeness_score
        assert len(state2.requirements) == 1
        assert state2.requirements[0].category == "Power"
    
    def test_get_categories_covered(self):
        """Test getting covered requirement categories"""
        state = SimpleState(session_id="test-005")
        
        state.add_requirement("I/O", "Input?", "Keyboard")
        state.add_requirement("Power", "Power?", "500W")
        state.add_requirement("Environment", "Temperature?", None)  # No answer
        state.add_requirement("I/O", "Output?", "Monitor")
        
        categories = state.get_categories_covered()
        assert "I/O" in categories
        assert "Power" in categories
        assert "Environment" not in categories  # Not answered
        assert len(categories) == 2  # Only unique categories
    
    def test_add_decision(self):
        """Test logging decisions in state"""
        state = SimpleState(session_id="test-006")
        
        state.add_decision(
            agent="orchestrator",
            decision="route_to_elicitor",
            reasoning=["No requirements collected", "Starting fresh"]
        )
        
        assert len(state.decision_log) == 1
        decision = state.decision_log[0]
        assert decision["agent"] == "orchestrator"
        assert decision["decision"] == "route_to_elicitor"
        assert len(decision["reasoning"]) == 2
        assert decision["iteration"] == 0


class TestDecisionLogger:
    """Test decision logging functionality"""
    
    def test_logger_creation(self):
        """Test that logger creates directories"""
        logger = DecisionLogger("test-session-001")
        
        assert logger.session_id == "test-session-001"
        assert logger.log_dir.exists()
        assert logger.log_dir.is_dir()
    
    def test_log_decision(self):
        """Test logging a decision"""
        logger = DecisionLogger("test-session-002")
        
        logger.log_decision(
            agent_name="elicitor",
            input_received={"state": "initial"},
            reasoning_steps=["Check categories", "Found I/O missing"],
            decision_made="ask_io_question",
            output_produced="What input devices do you need?"
        )
        
        # Verify log file exists
        assert logger.log_file.exists()
        
        # Read and verify log
        logs = logger.get_session_logs()
        assert len(logs) == 1
        log = logs[0]
        assert log["agent"] == "elicitor"
        assert log["decision"] == "ask_io_question"
        assert len(log["reasoning"]) == 2
    
    def test_log_routing(self):
        """Test logging routing decisions"""
        logger = DecisionLogger("test-session-003")
        
        state_dict = {"iteration_count": 1, "completeness_score": 0.5}
        logger.log_routing(
            current_state=state_dict,
            next_agent="completeness",
            reasoning=["Score below threshold", "Need more requirements"]
        )
        
        logs = logger.get_session_logs()
        assert len(logs) == 1
        assert logs[0]["agent"] == "orchestrator"
        assert "Route to completeness" in logs[0]["decision"]
    
    def test_log_error(self):
        """Test error logging"""
        logger = DecisionLogger("test-session-004")
        
        logger.log_error(
            agent_name="validator",
            error_message="Failed to load constraints",
            context={"file": "constraints.json"}
        )
        
        errors = logger.get_errors()
        assert len(errors) == 1
        assert errors[0]["error"] == "Failed to load constraints"
        assert errors[0]["decision"] == "ERROR"
    
    def test_truncation(self):
        """Test that large inputs/outputs are truncated"""
        logger = DecisionLogger("test-session-005")
        
        large_input = "x" * 2000  # 2000 chars
        large_output = "y" * 2000
        
        logger.log_decision(
            agent_name="test",
            input_received=large_input,
            reasoning_steps=["Process"],
            decision_made="truncate",
            output_produced=large_output
        )
        
        logs = logger.get_session_logs()
        assert len(logs[0]["input"]) == 1000  # Truncated
        assert len(logs[0]["output"]) == 1000  # Truncated
    
    def test_summary(self):
        """Test getting session summary"""
        logger = DecisionLogger("test-session-006")
        
        # Log various decisions
        logger.log_decision("agent1", "input", ["reason"], "decision", "output")
        logger.log_decision("agent2", "input", ["reason"], "decision", "output")
        logger.log_decision("agent1", "input", ["reason"], "decision", "output")
        logger.log_error("agent3", "Some error")
        
        summary = logger.summary()
        assert summary["session_id"] == "test-session-006"
        assert summary["total_decisions"] == 4
        assert summary["agents"]["agent1"] == 2
        assert summary["agents"]["agent2"] == 1
        assert summary["agents"]["agent3"] == 1
        assert summary["errors"] == 1


class TestImports:
    """Test that all imports work correctly"""
    
    def test_state_imports(self):
        """Test state module imports"""
        from src.state.simple_state import SimpleState, RequirementEntry
        assert SimpleState is not None
        assert RequirementEntry is not None
    
    def test_logging_imports(self):
        """Test logging module imports"""
        from src.logging.decision_logger import DecisionLogger
        assert DecisionLogger is not None
    
    def test_datetime_handling(self):
        """Test datetime serialization in requirements"""
        req = RequirementEntry(
            category="Test",
            question="Test question?",
            timestamp=datetime.now()
        )
        
        # Should be able to convert to dict
        req_dict = req.model_dump()
        assert "timestamp" in req_dict
        
        # Should be able to serialize to JSON
        req_json = req.model_dump_json()
        assert isinstance(req_json, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])