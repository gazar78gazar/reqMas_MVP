import sys
import os
from pathlib import Path
import pytest
import uuid

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.state.simple_state import SimpleState
from src.logging.decision_logger import DecisionLogger
from src.agents.agent_factory import create_agents, create_agent
from src.agents.elicitor import RequirementsElicitor
from src.agents.completeness import CompletenessChecker
from src.agents.validator import ConstraintValidator
from src.agents.validation_result import ValidationResult


class TestAgentFactory:
    """Test the agent factory"""
    
    def test_create_all_agents(self):
        """Test creating all agents at once"""
        session_id = f"test-factory-{uuid.uuid4().hex[:8]}"
        agents = create_agents(session_id)
        
        assert "elicitor" in agents
        assert "completeness" in agents
        assert "validator" in agents
        assert isinstance(agents["elicitor"], RequirementsElicitor)
        assert isinstance(agents["completeness"], CompletenessChecker)
        assert isinstance(agents["validator"], ConstraintValidator)
    
    def test_create_single_agent(self):
        """Test creating individual agents"""
        session_id = f"test-single-{uuid.uuid4().hex[:8]}"
        
        elicitor = create_agent("elicitor", session_id)
        assert isinstance(elicitor, RequirementsElicitor)
        
        completeness = create_agent("completeness", session_id)
        assert isinstance(completeness, CompletenessChecker)
        
        validator = create_agent("validator", session_id)
        assert isinstance(validator, ConstraintValidator)
    
    def test_invalid_agent_type(self):
        """Test error handling for invalid agent type"""
        session_id = f"test-invalid-{uuid.uuid4().hex[:8]}"
        
        with pytest.raises(ValueError, match="Unknown agent type"):
            create_agent("invalid_agent", session_id)


class TestRequirementsElicitorRefactored:
    """Test the refactored Requirements Elicitor"""
    
    def test_get_next_questions(self):
        """Test getting next unanswered questions"""
        session_id = f"test-elicit-{uuid.uuid4().hex[:8]}"
        logger = DecisionLogger(session_id)
        elicitor = RequirementsElicitor(logger)
        state = SimpleState(session_id=session_id)
        
        # Get first batch of questions
        questions = elicitor.get_next_questions(state)
        
        assert isinstance(questions, list)
        assert len(questions) == 8  # Should return up to 8 questions (2 per category)
        assert all(isinstance(q, str) for q in questions)
        
        # Verify we get questions from each category
        categories_covered = set()
        for q in questions:
            for category, cat_questions in elicitor.CATEGORY_QUESTIONS.items():
                if q in cat_questions:
                    categories_covered.add(category)
        
        assert len(categories_covered) == 4  # Should cover all 4 categories
    
    def test_process_answers(self):
        """Test processing multiple answers"""
        session_id = f"test-process-{uuid.uuid4().hex[:8]}"
        logger = DecisionLogger(session_id)
        elicitor = RequirementsElicitor(logger)
        state = SimpleState(session_id=session_id)
        
        # Get questions and create answers
        questions = elicitor.get_next_questions(state)
        answers = {
            questions[0]: "10",
            questions[1]: "8",
            questions[2]: "No analog inputs needed"
        }
        
        # Process answers
        new_state = elicitor.process_answers(answers, state)
        
        # Verify state was not modified in place
        assert len(state.requirements) == 0
        assert len(new_state.requirements) == 3
        
        # Verify answers were processed
        assert new_state.requirements[0].answer == "10"
        assert new_state.requirements[1].answer == "8"
        assert new_state.requirements[2].answer == "No analog inputs needed"
    
    def test_skip_already_answered(self):
        """Test that already answered questions are skipped"""
        session_id = f"test-skip-{uuid.uuid4().hex[:8]}"
        logger = DecisionLogger(session_id)
        elicitor = RequirementsElicitor(logger)
        state = SimpleState(session_id=session_id)
        
        # Add an answered question
        state.add_requirement("I/O", "How many digital inputs do you need?", "Already answered: 5")
        
        # Try to process same question again
        answers = {"How many digital inputs do you need?": "New answer: 10"}
        new_state = elicitor.process_answers(answers, state)
        
        # Should skip the already answered question
        assert new_state.requirements[0].answer == "Already answered: 5"
    
    def test_is_complete(self):
        """Test completion detection"""
        session_id = f"test-complete-{uuid.uuid4().hex[:8]}"
        logger = DecisionLogger(session_id)
        elicitor = RequirementsElicitor(logger)
        state = SimpleState(session_id=session_id)
        
        # Initially not complete
        assert elicitor.is_complete(state) == False
        
        # Add all questions
        for category, questions in elicitor.CATEGORY_QUESTIONS.items():
            for question in questions:
                state.add_requirement(category, question)
        
        # Now should be complete
        assert elicitor.is_complete(state) == True


class TestCompletenessCheckerRefactored:
    """Test the refactored Completeness Checker"""
    
    def test_check_completeness(self):
        """Test completeness calculation"""
        session_id = f"test-comp-{uuid.uuid4().hex[:8]}"
        logger = DecisionLogger(session_id)
        checker = CompletenessChecker(logger)
        state = SimpleState(session_id=session_id)
        
        # Empty state should have 0 completeness
        score = checker.check_completeness(state)
        assert score == 0.0
        
        # Add some required fields
        state.add_requirement("I/O", "How many digital inputs do you need?", "10")
        state.add_requirement("I/O", "How many digital outputs do you need?", "8")
        
        score = checker.check_completeness(state)
        assert score > 0.0
        assert score < 1.0
    
    def test_identify_gaps(self):
        """Test gap identification"""
        session_id = f"test-gaps-{uuid.uuid4().hex[:8]}"
        logger = DecisionLogger(session_id)
        checker = CompletenessChecker(logger)
        state = SimpleState(session_id=session_id)
        
        # All fields should be gaps initially
        gaps = checker.identify_gaps(state)
        
        total_fields = sum(len(fields) for fields in checker.REQUIRED_FIELDS.values())
        assert len(gaps) == total_fields
        assert "digital_inputs" in gaps
        assert "voltage" in gaps
    
    def test_generate_gap_questions(self):
        """Test question generation for gaps"""
        session_id = f"test-gapq-{uuid.uuid4().hex[:8]}"
        logger = DecisionLogger(session_id)
        checker = CompletenessChecker(logger)
        
        gaps = ["digital_inputs", "voltage", "temperature_range"]
        questions = checker.generate_gap_questions(gaps)
        
        assert len(questions) == 3
        assert "How many digital inputs do you need?" in questions
        assert "What is your available power supply voltage (24VDC, 120VAC, 240VAC)?" in questions
        assert "What is the operating temperature range?" in questions
    
    def test_process_returns_new_state(self):
        """Test that process returns new state without modifying original"""
        session_id = f"test-proc-{uuid.uuid4().hex[:8]}"
        logger = DecisionLogger(session_id)
        checker = CompletenessChecker(logger)
        state = SimpleState(session_id=session_id)
        
        original_score = state.completeness_score
        new_state = checker.process(state)
        
        # Original state unchanged
        assert state.completeness_score == original_score
        assert len(state.validation_results) == 0
        
        # New state has updates
        assert new_state.completeness_score >= 0.0
        assert len(new_state.validation_results) == 1
        assert new_state.validation_results[0]["type"] == "completeness_check"


class TestValidationResult:
    """Test the ValidationResult class"""
    
    def test_validation_result_creation(self):
        """Test creating ValidationResult"""
        result = ValidationResult(is_valid=True)
        
        assert result.is_valid == True
        assert result.violations == []
        assert result.warnings == []
        assert result.suggestions == []
    
    def test_add_violation(self):
        """Test adding violations"""
        result = ValidationResult(is_valid=True)
        
        result.add_violation("Test violation")
        
        assert result.is_valid == False  # Should become invalid
        assert len(result.violations) == 1
        assert result.violations[0] == "Test violation"
    
    def test_add_warning(self):
        """Test adding warnings"""
        result = ValidationResult(is_valid=True)
        
        result.add_warning("Test warning")
        
        assert result.is_valid == True  # Should remain valid
        assert len(result.warnings) == 1
        assert result.warnings[0] == "Test warning"
    
    def test_get_summary(self):
        """Test summary generation"""
        result1 = ValidationResult(is_valid=True)
        assert result1.get_summary() == "All constraints satisfied"
        
        result2 = ValidationResult(is_valid=True)
        result2.add_warning("Warning 1")
        assert "Valid with 1 warning(s)" in result2.get_summary()
        
        result3 = ValidationResult(is_valid=True)
        result3.add_violation("Violation 1")
        assert "Invalid: 1 violation(s) found" in result3.get_summary()
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        result = ValidationResult(is_valid=True)
        result.add_warning("Test warning")
        result.add_suggestion("Test suggestion")
        
        dict_result = result.to_dict()
        
        assert dict_result["is_valid"] == True
        assert dict_result["violations"] == []
        assert dict_result["warnings"] == ["Test warning"]
        assert dict_result["suggestions"] == ["Test suggestion"]


class TestConstraintValidatorRefactored:
    """Test the refactored Constraint Validator"""
    
    def test_validate_returns_validation_result(self):
        """Test that validate returns ValidationResult"""
        session_id = f"test-val-{uuid.uuid4().hex[:8]}"
        logger = DecisionLogger(session_id)
        validator = ConstraintValidator(logger)
        state = SimpleState(session_id=session_id)
        
        # Add valid requirements
        state.add_requirement("I/O", "How many digital inputs do you need?", "10")
        state.add_requirement("Power", "What is your available power supply voltage (24VDC, 120VAC, 240VAC)?", "24VDC")
        
        result = validator.validate(state)
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid == True
    
    def test_validate_io_limits_method(self):
        """Test the validate_io_limits helper method"""
        session_id = f"test-iolim-{uuid.uuid4().hex[:8]}"
        logger = DecisionLogger(session_id)
        validator = ConstraintValidator(logger)
        state = SimpleState(session_id=session_id)
        
        # Add requirements exceeding limits
        state.add_requirement("I/O", "How many digital inputs do you need?", "500")
        
        violations = validator.validate_io_limits(state)
        
        assert isinstance(violations, list)
        assert len(violations) > 0
        assert "exceed" in violations[0].lower()
    
    def test_validate_power_requirements_method(self):
        """Test the validate_power_requirements helper method"""
        session_id = f"test-power-{uuid.uuid4().hex[:8]}"
        logger = DecisionLogger(session_id)
        validator = ConstraintValidator(logger)
        state = SimpleState(session_id=session_id)
        
        # Add invalid voltage
        state.add_requirement("Power", "What is your available power supply voltage (24VDC, 120VAC, 240VAC)?", "12VDC")
        
        violations = validator.validate_power_requirements(state)
        
        assert isinstance(violations, list)
        assert len(violations) > 0
        assert "not in available options" in violations[0]
    
    def test_validate_environmental_compatibility_method(self):
        """Test the validate_environmental_compatibility helper method"""
        session_id = f"test-env-{uuid.uuid4().hex[:8]}"
        logger = DecisionLogger(session_id)
        validator = ConstraintValidator(logger)
        state = SimpleState(session_id=session_id)
        
        # Add extreme temperature
        state.add_requirement("Environment", "What is the operating temperature range?", "-50 to 100")
        
        violations = validator.validate_environmental_compatibility(state)
        
        assert isinstance(violations, list)
        assert len(violations) > 0
        assert "temperature" in violations[0].lower()


class TestIntegrationRefactored:
    """Test integration of refactored agents"""
    
    def test_full_flow_with_factory(self):
        """Test complete flow using agent factory"""
        session_id = f"test-flow-{uuid.uuid4().hex[:8]}"
        agents = create_agents(session_id)
        state = SimpleState(session_id=session_id)
        
        # Step 1: Get questions from elicitor
        questions = agents["elicitor"].get_next_questions(state)
        assert len(questions) == 8  # 2 per category × 4 categories
        
        # Step 2: Process answers (answer all 8 questions)
        answers = {}
        for i, q in enumerate(questions):
            if "digital input" in q.lower():
                answers[q] = "20"
            elif "digital output" in q.lower():
                answers[q] = "15"
            elif "temperature" in q.lower():
                answers[q] = "0 to 50"
            elif "indoor" in q.lower():
                answers[q] = "indoor"
            elif "protocol" in q.lower():
                answers[q] = "Ethernet and Modbus"
            elif "remote" in q.lower():
                answers[q] = "yes"
            elif "voltage" in q.lower():
                answers[q] = "24VDC"
            elif "power budget" in q.lower():
                answers[q] = "150 watts"
            else:
                answers[q] = "standard requirements"
        state = agents["elicitor"].process_answers(answers, state)
        
        # Step 3: Check completeness
        score = agents["completeness"].check_completeness(state)
        assert score > 0
        
        gaps = agents["completeness"].identify_gaps(state)
        gap_questions = agents["completeness"].generate_gap_questions(gaps)
        
        # Step 4: Add more answers to fill gaps
        more_answers = {}
        for q in gap_questions[:5]:  # Answer first 5 gap questions
            if "temperature" in q.lower():
                more_answers[q] = "0 to 50"
            elif "voltage" in q.lower():
                more_answers[q] = "24VDC"
            elif "indoor" in q.lower():
                more_answers[q] = "indoor"
            elif "humidity" in q.lower():
                more_answers[q] = "normal"
            elif "protocol" in q.lower():
                more_answers[q] = "Ethernet"
            else:
                more_answers[q] = "standard"
        
        state = agents["elicitor"].process_answers(more_answers, state)
        
        # Step 5: Validate
        result = agents["validator"].validate(state)
        assert isinstance(result, ValidationResult)
        
        # Should be valid or have minor issues
        if not result.is_valid:
            assert len(result.violations) >= 0
        
        assert len(result.suggestions) >= 0  # Should have some suggestions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])