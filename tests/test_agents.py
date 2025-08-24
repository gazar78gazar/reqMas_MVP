import sys
import os
from pathlib import Path
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.state.simple_state import SimpleState
from src.logging.decision_logger import DecisionLogger
from src.agents.elicitor import RequirementsElicitor
from src.agents.completeness import CompletenessChecker
from src.agents.validator import ConstraintValidator


class TestRequirementsElicitor:
    """Test the Requirements Elicitor agent"""
    
    def test_elicitor_initialization(self):
        """Test elicitor can be initialized"""
        logger = DecisionLogger("test-elicitor-001")
        elicitor = RequirementsElicitor(logger)
        
        assert elicitor is not None
        assert len(elicitor.IO_QUESTIONS) == 7
        assert len(elicitor.ENV_QUESTIONS) == 5
        assert len(elicitor.COMM_QUESTIONS) == 5
        assert len(elicitor.POWER_QUESTIONS) == 4
    
    def test_first_question(self):
        """Test elicitor asks first question correctly"""
        logger = DecisionLogger("test-elicitor-002")
        elicitor = RequirementsElicitor(logger)
        state = SimpleState(session_id="test-elicitor-002")
        
        result = elicitor.process(state)
        
        assert result["complete"] == False
        assert "question" in result
        assert result["question"] == elicitor.IO_QUESTIONS[0]
        assert result["category"] == "I/O"
        assert len(state.requirements) == 1
    
    def test_question_progression(self):
        """Test elicitor progresses through questions"""
        logger = DecisionLogger("test-elicitor-003")
        elicitor = RequirementsElicitor(logger)
        state = SimpleState(session_id="test-elicitor-003")
        
        # Ask first question
        result1 = elicitor.process(state)
        first_question = result1["question"]
        
        # Answer it
        elicitor.process_answer(state, "10")
        
        # Ask second question
        result2 = elicitor.process(state)
        second_question = result2["question"]
        
        assert first_question != second_question
        assert len(state.requirements) == 2
        assert state.requirements[0].answer == "10"
    
    def test_category_progression(self):
        """Test elicitor moves through categories"""
        logger = DecisionLogger("test-elicitor-004")
        elicitor = RequirementsElicitor(logger)
        state = SimpleState(session_id="test-elicitor-004")
        
        # Add all I/O questions as asked
        for q in elicitor.IO_QUESTIONS:
            state.add_requirement("I/O", q, "test answer")
        
        # Next question should be from Environment category
        result = elicitor.process(state)
        
        assert result["category"] == "Environment"
        assert result["question"] in elicitor.ENV_QUESTIONS
    
    def test_completion_detection(self):
        """Test elicitor detects when all questions asked"""
        logger = DecisionLogger("test-elicitor-005")
        elicitor = RequirementsElicitor(logger)
        state = SimpleState(session_id="test-elicitor-005")
        
        # Add all questions as asked
        for category, questions in elicitor.CATEGORY_QUESTIONS.items():
            for q in questions:
                state.add_requirement(category, q, "test answer")
        
        # Should return complete
        result = elicitor.process(state)
        
        assert result["complete"] == True
        assert "message" in result
    
    def test_progress_tracking(self):
        """Test progress tracking functionality"""
        logger = DecisionLogger("test-elicitor-006")
        elicitor = RequirementsElicitor(logger)
        state = SimpleState(session_id="test-elicitor-006")
        
        # Ask and answer some questions
        elicitor.process(state)
        elicitor.process_answer(state, "5 inputs")
        elicitor.process(state)
        elicitor.process_answer(state, "3 outputs")
        
        progress = elicitor.get_progress(state)
        
        assert progress["asked"] == 2
        assert progress["answered"] == 2
        assert progress["percentage_asked"] > 0
        assert "I/O" in progress["by_category"]
    
    def test_followup_suggestions(self):
        """Test follow-up question suggestions"""
        logger = DecisionLogger("test-elicitor-007")
        elicitor = RequirementsElicitor(logger)
        state = SimpleState(session_id="test-elicitor-007")
        
        # Add ambiguous answer
        state.add_requirement("I/O", "How many inputs?", "Maybe 10 or 15")
        
        followup = elicitor.suggest_followup(state)
        
        assert followup is not None
        assert "uncertain" in followup or "range" in followup


class TestCompletenessChecker:
    """Test the Completeness Checker agent"""
    
    def test_completeness_initialization(self):
        """Test completeness checker initialization"""
        logger = DecisionLogger("test-complete-001")
        checker = CompletenessChecker(logger)
        
        assert checker is not None
        assert len(checker.MIN_REQUIREMENTS) == 4
        assert len(checker.CRITICAL_QUESTIONS) == 6
    
    def test_empty_state_completeness(self):
        """Test completeness with no requirements"""
        logger = DecisionLogger("test-complete-002")
        checker = CompletenessChecker(logger)
        state = SimpleState(session_id="test-complete-002")
        
        result = checker.process(state)
        
        assert result["complete"] == False
        assert result["score"] == 0.0
        assert len(result["missing"]) > 0
    
    def test_partial_completeness(self):
        """Test completeness with some requirements"""
        logger = DecisionLogger("test-complete-003")
        checker = CompletenessChecker(logger)
        state = SimpleState(session_id="test-complete-003")
        
        # Add some answered requirements
        state.add_requirement("I/O", "How many digital inputs do you need?", "10")
        state.add_requirement("I/O", "How many digital outputs do you need?", "8")
        state.add_requirement("Power", "What is your available power supply voltage (24VDC, 120VAC, 240VAC)?", "24VDC")
        
        result = checker.process(state)
        
        assert result["complete"] == False
        assert 0 < result["score"] < 0.85
        assert len(result["missing"]) > 0
        assert state.completeness_score == result["score"]
    
    def test_critical_questions_impact(self):
        """Test that critical questions affect score"""
        logger = DecisionLogger("test-complete-004")
        checker = CompletenessChecker(logger)
        state = SimpleState(session_id="test-complete-004")
        
        # Add all critical questions
        for q in checker.CRITICAL_QUESTIONS:
            if "input" in q.lower():
                state.add_requirement("I/O", q, "10")
            elif "output" in q.lower():
                state.add_requirement("I/O", q, "8")
            elif "temperature" in q.lower():
                state.add_requirement("Environment", q, "-10 to 50")
            elif "indoor" in q.lower():
                state.add_requirement("Environment", q, "indoor")
            elif "communication" in q.lower():
                state.add_requirement("Communication", q, "Ethernet")
            elif "voltage" in q.lower():
                state.add_requirement("Power", q, "24VDC")
        
        result = checker.process(state)
        
        # Score should be higher with critical questions answered
        assert result["score"] > 0.3  # At least 30% from critical questions
    
    def test_category_summary(self):
        """Test category summary generation"""
        logger = DecisionLogger("test-complete-005")
        checker = CompletenessChecker(logger)
        state = SimpleState(session_id="test-complete-005")
        
        # Add mixed requirements
        state.add_requirement("I/O", "Q1", "A1")
        state.add_requirement("I/O", "Q2", "A2")
        state.add_requirement("I/O", "Q3", None)  # Asked but not answered
        state.add_requirement("Power", "Q4", "A4")
        
        summary = checker.get_category_summary(state)
        
        assert "I/O" in summary
        assert summary["I/O"]["asked"] == 3
        assert summary["I/O"]["answered"] == 2
        assert summary["Power"]["asked"] == 1
        assert summary["Power"]["answered"] == 1
    
    def test_recommendation_generation(self):
        """Test that recommendations are generated"""
        logger = DecisionLogger("test-complete-006")
        checker = CompletenessChecker(logger)
        state = SimpleState(session_id="test-complete-006")
        
        # Low completeness state
        state.add_requirement("I/O", "Input?", "5")
        
        result = checker.process(state)
        
        assert "recommendation" in result
        assert isinstance(result["recommendation"], str)
        assert len(result["recommendation"]) > 0


class TestConstraintValidator:
    """Test the Constraint Validator agent"""
    
    def test_validator_initialization(self):
        """Test validator initialization"""
        logger = DecisionLogger("test-valid-001")
        validator = ConstraintValidator(logger)
        
        assert validator is not None
        assert validator.constraints is not None
        assert "io_limits" in validator.constraints
    
    def test_valid_requirements(self):
        """Test validation with valid requirements"""
        logger = DecisionLogger("test-valid-002")
        validator = ConstraintValidator(logger)
        state = SimpleState(session_id="test-valid-002")
        
        # Add valid requirements
        state.add_requirement("I/O", "How many digital inputs do you need?", "10")
        state.add_requirement("I/O", "How many digital outputs do you need?", "8")
        state.add_requirement("Environment", "What is the operating temperature range?", "0 to 40")
        state.add_requirement("Environment", "Is this an indoor or outdoor installation?", "indoor")
        state.add_requirement("Power", "What is your available power supply voltage (24VDC, 120VAC, 240VAC)?", "24VDC")
        state.add_requirement("Power", "What is your maximum power budget in watts?", "100")
        
        result = validator.process(state)
        
        assert result["valid"] == True
        assert len(result["violations"]) == 0
    
    def test_io_limit_violations(self):
        """Test I/O limit constraint violations"""
        logger = DecisionLogger("test-valid-003")
        validator = ConstraintValidator(logger)
        state = SimpleState(session_id="test-valid-003")
        
        # Add requirements exceeding I/O limits
        state.add_requirement("I/O", "How many digital inputs do you need?", "500")  # Exceeds 256
        state.add_requirement("I/O", "How many digital outputs do you need?", "300")  # Exceeds 256
        
        result = validator.process(state)
        
        assert result["valid"] == False
        assert len(result["violations"]) >= 2
        assert any(v["type"] == "io_limit" for v in result["violations"])
    
    def test_temperature_violations(self):
        """Test temperature constraint violations"""
        logger = DecisionLogger("test-valid-004")
        validator = ConstraintValidator(logger)
        state = SimpleState(session_id="test-valid-004")
        
        # Add extreme temperature requirements
        state.add_requirement("Environment", "What is the operating temperature range?", "-50 to 100")
        state.add_requirement("Environment", "Is this an indoor or outdoor installation?", "outdoor")
        
        result = validator.process(state)
        
        assert result["valid"] == False
        violations = [v for v in result["violations"] if v["type"] == "temperature"]
        assert len(violations) > 0
    
    def test_power_violations(self):
        """Test power constraint violations"""
        logger = DecisionLogger("test-valid-005")
        validator = ConstraintValidator(logger)
        state = SimpleState(session_id="test-valid-005")
        
        # Add invalid power requirements
        state.add_requirement("Power", "What is your available power supply voltage (24VDC, 120VAC, 240VAC)?", "12VDC")  # Not available
        state.add_requirement("Power", "What is your maximum power budget in watts?", "5000")  # Exceeds max
        
        result = validator.process(state)
        
        assert result["valid"] == False
        power_violations = [v for v in result["violations"] if v["type"] == "power"]
        assert len(power_violations) >= 1
    
    def test_incompatibility_warnings(self):
        """Test incompatibility detection"""
        logger = DecisionLogger("test-valid-006")
        validator = ConstraintValidator(logger)
        state = SimpleState(session_id="test-valid-006")
        
        # Add requirements that trigger warnings
        state.add_requirement("Environment", "Is this an indoor or outdoor installation?", "outdoor")
        state.add_requirement("Environment", "What is the operating temperature range?", "0 to 70")
        
        result = validator.process(state)
        
        # Should have warnings about outdoor installation
        assert len(result["warnings"]) > 0
        assert any("outdoor" in str(w).lower() for w in result["warnings"])
    
    def test_recommendations(self):
        """Test recommendation generation"""
        logger = DecisionLogger("test-valid-007")
        validator = ConstraintValidator(logger)
        state = SimpleState(session_id="test-valid-007")
        
        # Add requirements with violations
        state.add_requirement("I/O", "How many digital inputs do you need?", "300")
        state.add_requirement("Communication", "How many devices will communicate with the PLC?", "100")
        
        result = validator.process(state)
        
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0
        # Should recommend distributed I/O for high I/O count
        assert any("distributed" in r.lower() or "multiple" in r.lower() for r in result["recommendations"])
    
    def test_value_extraction(self):
        """Test requirement value extraction"""
        logger = DecisionLogger("test-valid-008")
        validator = ConstraintValidator(logger)
        state = SimpleState(session_id="test-valid-008")
        
        # Add various formats of answers
        state.add_requirement("I/O", "How many digital inputs do you need?", "I need about 25 inputs")
        state.add_requirement("Environment", "What is the operating temperature range?", "From -10C to 50C")
        state.add_requirement("Communication", "What communication protocols do you need?", "Ethernet and Modbus")
        
        values = validator._extract_requirement_values(state)
        
        assert values["digital_inputs"] == 25
        assert values["temperature_min"] == -10
        assert values["temperature_max"] == 50
        assert "Ethernet" in values["protocols"]
        assert "Modbus" in values["protocols"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])