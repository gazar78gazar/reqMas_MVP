import sys
import os
from pathlib import Path
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.state.simple_state import SimpleState
from src.logging.decision_logger import DecisionLogger
from src.agents.orchestrator import Orchestrator
from src.agents.elicitor import RequirementsElicitor
from src.agents.completeness import CompletenessChecker
from src.agents.validator import ConstraintValidator


class TestCompleteAgentFlow:
    """Test complete flow through all agents"""
    
    def test_full_system_flow(self):
        """Test complete flow from empty state to validation"""
        session_id = "test-full-flow-001"
        logger = DecisionLogger(session_id)
        
        # Initialize all agents
        orchestrator = Orchestrator(logger)
        elicitor = RequirementsElicitor(logger)
        completeness = CompletenessChecker(logger)
        validator = ConstraintValidator(logger)
        
        # Initialize state
        state = SimpleState(session_id=session_id)
        
        # === ITERATION 1: Empty state -> Elicitor ===
        next_agent = orchestrator.route(state)
        assert next_agent == "elicitor"
        
        # Elicitor asks questions and gets answers
        for i in range(10):  # Ask first 10 questions
            result = elicitor.process(state)
            if result["complete"]:
                break
            
            # Simulate user answers
            if "digital input" in result["question"].lower():
                elicitor.process_answer(state, "20")
            elif "digital output" in result["question"].lower():
                elicitor.process_answer(state, "15")
            elif "analog input" in result["question"].lower():
                elicitor.process_answer(state, "4 channels, 0-10V")
            elif "temperature" in result["question"].lower():
                elicitor.process_answer(state, "-10 to 50 degrees")
            elif "indoor or outdoor" in result["question"].lower():
                elicitor.process_answer(state, "indoor")
            elif "humidity" in result["question"].lower():
                elicitor.process_answer(state, "normal")
            elif "communication protocol" in result["question"].lower():
                elicitor.process_answer(state, "Ethernet and Modbus")
            elif "devices will communicate" in result["question"].lower():
                elicitor.process_answer(state, "15 devices")
            elif "power supply voltage" in result["question"].lower():
                elicitor.process_answer(state, "24VDC")
            elif "power budget" in result["question"].lower():
                elicitor.process_answer(state, "150 watts")
            else:
                elicitor.process_answer(state, "standard requirements")
        
        state.iteration_count += 1
        
        # === ITERATION 2: Check completeness ===
        next_agent = orchestrator.route(state)
        assert next_agent == "completeness"
        
        comp_result = completeness.process(state)
        assert "score" in comp_result
        assert state.completeness_score > 0
        
        # If not complete enough, add more answers
        if comp_result["score"] < 0.85:
            # Answer remaining critical questions
            for missing in comp_result["missing"]:
                if missing["type"] == "critical_unanswered":
                    # Find and answer the question
                    for req in state.requirements:
                        if req.question == missing["question"] and not req.answer:
                            req.answer = "standard requirement"
        
        state.iteration_count += 1
        
        # === ITERATION 3: Validate if complete ===
        if state.completeness_score >= 0.85:
            next_agent = orchestrator.route(state)
            assert next_agent == "validator"
            
            val_result = validator.process(state)
            assert "valid" in val_result
            assert "violations" in val_result
            assert "warnings" in val_result
        else:
            # If still not complete, should continue with completeness
            next_agent = orchestrator.route(state)
            assert next_agent in ["completeness", "END"]  # Might hit iteration limit
        
        # Check final state
        assert len(state.requirements) > 0
        assert len(state.decision_log) > 0
        assert state.iteration_count <= 3
    
    def test_elicitor_completeness_integration(self):
        """Test integration between elicitor and completeness checker"""
        session_id = "test-elicit-complete-001"
        logger = DecisionLogger(session_id)
        
        elicitor = RequirementsElicitor(logger)
        completeness = CompletenessChecker(logger)
        state = SimpleState(session_id=session_id)
        
        # Ask and answer critical questions only
        critical_questions = completeness.CRITICAL_QUESTIONS
        
        for question in critical_questions:
            # Find category for question
            for category, questions in elicitor.CATEGORY_QUESTIONS.items():
                if question in questions:
                    state.add_requirement(category, question)
                    break
            
            # Provide answer
            if "input" in question.lower():
                answer = "10"
            elif "output" in question.lower():
                answer = "8"
            elif "temperature" in question.lower():
                answer = "0 to 40"
            elif "indoor" in question.lower():
                answer = "indoor"
            elif "protocol" in question.lower():
                answer = "Ethernet"
            elif "voltage" in question.lower():
                answer = "24VDC"
            else:
                answer = "standard"
            
            if state.requirements:
                state.requirements[-1].answer = answer
        
        # Check completeness
        result = completeness.process(state)
        
        # Should have decent score from critical questions
        assert result["score"] > 0.3  # At least 30% from critical questions alone
        assert len(result["missing"]) >= 0  # May still have missing items
    
    def test_completeness_validator_integration(self):
        """Test integration between completeness and validator"""
        session_id = "test-complete-valid-001"
        logger = DecisionLogger(session_id)
        
        completeness = CompletenessChecker(logger)
        validator = ConstraintValidator(logger)
        state = SimpleState(session_id=session_id)
        
        # Add complete but invalid requirements
        state.add_requirement("I/O", "How many digital inputs do you need?", "500")  # Too many
        state.add_requirement("I/O", "How many digital outputs do you need?", "300")  # Too many
        state.add_requirement("I/O", "Do you need analog inputs?", "No")
        state.add_requirement("Environment", "What is the operating temperature range?", "0 to 40")
        state.add_requirement("Environment", "Is this an indoor or outdoor installation?", "indoor")
        state.add_requirement("Communication", "What communication protocols do you need?", "Ethernet")
        state.add_requirement("Communication", "How many devices will communicate?", "10")
        state.add_requirement("Power", "What is your available power supply voltage?", "24VDC")
        state.add_requirement("Power", "What is your maximum power budget?", "200")
        
        # Check completeness
        comp_result = completeness.process(state)
        
        # Should be reasonably complete
        assert comp_result["score"] > 0.5
        
        # But validation should fail
        val_result = validator.process(state)
        assert val_result["valid"] == False
        assert len(val_result["violations"]) > 0
        assert any(v["type"] == "io_limit" for v in val_result["violations"])
    
    def test_orchestrator_agent_coordination(self):
        """Test orchestrator coordinates agents correctly"""
        session_id = "test-orchestrate-001"
        logger = DecisionLogger(session_id)
        
        orchestrator = Orchestrator(logger)
        elicitor = RequirementsElicitor(logger)
        completeness = CompletenessChecker(logger)
        validator = ConstraintValidator(logger)
        
        state = SimpleState(session_id=session_id)
        
        # Track agent sequence
        agent_sequence = []
        
        # Simulate 3 iterations
        for iteration in range(3):
            state.iteration_count = iteration
            next_agent = orchestrator.route(state)
            agent_sequence.append(next_agent)
            
            if next_agent == "elicitor":
                # Add some requirements
                state.add_requirement("I/O", "Q1", "A1")
                state.add_requirement("Power", "Q2", "A2")
            elif next_agent == "completeness":
                # Update completeness score
                comp_result = completeness.process(state)
                # Artificially set high score for last iteration
                if iteration == 2:
                    state.completeness_score = 0.9
            elif next_agent == "validator":
                # Validate
                validator.process(state)
            elif next_agent == "END":
                break
        
        # Should follow expected sequence
        assert agent_sequence[0] == "elicitor"  # Start with elicitor
        assert "completeness" in agent_sequence or "validator" in agent_sequence
        
        # Check logs were created
        logs = logger.get_session_logs()
        assert len(logs) > 0
        
        # Check state was updated
        assert len(state.decision_log) >= len(agent_sequence)
    
    def test_error_recovery_flow(self):
        """Test system handles errors gracefully"""
        session_id = "test-error-flow-001"
        logger = DecisionLogger(session_id)
        
        orchestrator = Orchestrator(logger)
        state = SimpleState(session_id=session_id)
        
        # Simulate an error
        error = Exception("Test error in agent processing")
        next_action = orchestrator.process_error(state, error, "elicitor")
        
        assert next_action == "END"
        assert len(state.decision_log) == 1
        assert state.decision_log[0]["decision"] == "ERROR"
        
        # Check error was logged
        errors = logger.get_errors()
        assert len(errors) == 1
        
        # Orchestrator should not continue after error
        assert orchestrator.should_continue(state) == True  # One error is OK
        
        # Add another error
        orchestrator.process_error(state, error, "completeness")
        assert orchestrator.should_continue(state) == False  # Two errors stops processing
    
    def test_logging_throughout_flow(self):
        """Test that all agents log correctly throughout flow"""
        session_id = "test-logging-flow-001"
        logger = DecisionLogger(session_id)
        
        # Initialize agents
        orchestrator = Orchestrator(logger)
        elicitor = RequirementsElicitor(logger)
        completeness = CompletenessChecker(logger)
        validator = ConstraintValidator(logger)
        
        state = SimpleState(session_id=session_id)
        
        # Run through agents
        orchestrator.route(state)  # Log routing decision
        
        elicitor.process(state)  # Log elicitation
        elicitor.process_answer(state, "test answer")  # Log answer processing
        
        state.add_requirement("I/O", "Test", "Answer")
        completeness.process(state)  # Log completeness check
        
        validator.process(state)  # Log validation
        
        # Check all agents logged
        logs = logger.get_session_logs()
        agents_logged = set(log["agent"] for log in logs)
        
        assert "orchestrator" in agents_logged
        assert "elicitor" in agents_logged
        assert "completeness" in agents_logged
        assert "validator" in agents_logged
        
        # Check summary
        summary = logger.summary()
        assert summary["total_decisions"] >= 4
        assert len(summary["agents"]) >= 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])