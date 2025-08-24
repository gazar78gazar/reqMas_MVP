from typing import Dict, List
from copy import deepcopy
from src.state.simple_state import SimpleState
from src.logging.decision_logger import DecisionLogger
from src.agents.elicitor import RequirementsElicitor


class CompletenessChecker:
    """Agent responsible for evaluating requirement completeness"""
    
    # Required fields for each category
    REQUIRED_FIELDS = {
        "I/O": ["digital_inputs", "digital_outputs", "analog_inputs", "analog_outputs"],
        "Environment": ["temperature_range", "installation_type", "humidity"],
        "Communication": ["protocol", "network_type"],
        "Power": ["voltage", "power_consumption"]
    }
    
    # Get questions from elicitor for completeness checking
    CATEGORY_QUESTIONS = RequirementsElicitor.CATEGORY_QUESTIONS
    
    # Map fields to specific questions
    FIELD_TO_QUESTION = {
        "digital_inputs": "How many digital inputs do you need?",
        "digital_outputs": "How many digital outputs do you need?",
        "analog_inputs": "Do you need analog inputs? If yes, how many and what type (0-10V, 4-20mA)?",
        "analog_outputs": "Do you need analog outputs? If yes, how many and what type?",
        "temperature_range": "What is the operating temperature range?",
        "installation_type": "Is this an indoor or outdoor installation?",
        "humidity": "What is the humidity level (normal, high, condensing)?",
        "protocol": "What communication protocols do you need (Ethernet, Modbus, Profibus, etc.)?",
        "network_type": "Do you need remote access capability?",
        "voltage": "What is your available power supply voltage (24VDC, 120VAC, 240VAC)?",
        "power_consumption": "What is your maximum power budget in watts?"
    }
    
    def __init__(self, logger: DecisionLogger):
        self.logger = logger
    
    def check_completeness(self, state: SimpleState) -> float:
        """Calculate completeness based on answered questions"""
        
        # More flexible mapping with partial matches
        QUESTION_TO_FIELD = {
            "digital inputs": "digital_inputs",
            "digital outputs": "digital_outputs", 
            "analog inputs": "analog_inputs",
            "analog outputs": "analog_outputs",
            "temperature": "temperature_range",
            "indoor or outdoor": "installation_type",
            "humidity": "humidity",
            "communication protocol": "protocol",
            "remote access": "network_type",
            "power supply voltage": "voltage",
            "power budget": "power_consumption"
        }
        
        # Count how many required fields have answers
        answered_fields = set()
        for req in state.requirements:
            if req.answer:  # Only count questions that have answers
                question_lower = req.question.lower()
                # Match question to field using more flexible matching
                for key_phrase, field in QUESTION_TO_FIELD.items():
                    if key_phrase in question_lower:
                        answered_fields.add(field)
                        break
        
        # Calculate score
        total_required = sum(len(fields) for fields in self.REQUIRED_FIELDS.values())
        score = len(answered_fields) / total_required if total_required > 0 else 0
        
        # Update state's completeness score
        state.completeness_score = score
        
        reasoning = []
        reasoning.append(f"Total required fields: {total_required}")
        reasoning.append(f"Answered fields: {len(answered_fields)}")
        reasoning.append(f"Completeness score: {score:.2%}")
        
        # Log decision
        self.logger.log_decision(
            agent_name="completeness",
            input_received=f"State with {len(state.requirements)} requirements",
            reasoning_steps=reasoning,
            decision_made=f"score_{score:.2f}",
            output_produced=f"Completeness: {score:.2%}"
        )
        
        # Update state with decision
        state.add_decision(
            agent="completeness",
            decision=f"completeness_check",
            reasoning=reasoning
        )
        
        return score
    
    def identify_gaps(self, state: SimpleState) -> List[str]:
        """
        Identify missing required fields
        
        Args:
            state: Current state with requirements
            
        Returns:
            List of missing field names
        """
        gaps = []
        
        for category, fields in self.REQUIRED_FIELDS.items():
            for field in fields:
                if not self._is_field_answered(field, state):
                    gaps.append(field)
        
        # Log gaps
        self.logger.log_decision(
            agent_name="completeness",
            input_received=f"State analysis",
            reasoning_steps=[f"Checking all required fields", f"Found {len(gaps)} gaps"],
            decision_made="identify_gaps",
            output_produced=f"Missing fields: {gaps}"
        )
        
        return gaps
    
    def generate_gap_questions(self, gaps: List[str]) -> List[str]:
        """
        Generate specific questions for missing fields
        
        Args:
            gaps: List of missing field names
            
        Returns:
            List of questions to ask for those fields
        """
        questions = []
        
        for gap in gaps:
            if gap in self.FIELD_TO_QUESTION:
                questions.append(self.FIELD_TO_QUESTION[gap])
            else:
                # Generate a generic question if no mapping exists
                questions.append(f"Please provide information about: {gap.replace('_', ' ')}")
        
        # Log question generation
        self.logger.log_decision(
            agent_name="completeness",
            input_received=f"{len(gaps)} gaps",
            reasoning_steps=[f"Mapping {len(gaps)} fields to questions"],
            decision_made="generate_questions",
            output_produced=f"Generated {len(questions)} questions"
        )
        
        return questions
    
    def process(self, state: SimpleState) -> SimpleState:
        """
        Main processing method - evaluates completeness and returns new state
        
        Args:
            state: Current state
            
        Returns:
            New state with completeness analysis (does not modify original)
        """
        # Create a deep copy of the state
        new_state = deepcopy(state)
        
        # Calculate completeness
        score = self.check_completeness(new_state)
        
        # Identify gaps
        gaps = self.identify_gaps(new_state)
        
        # Generate questions for gaps
        gap_questions = self.generate_gap_questions(gaps)
        
        # Create result summary
        result = {
            "complete": score >= 0.85,
            "score": score,
            "gaps": gaps,
            "gap_questions": gap_questions,
            "missing_count": len(gaps),
            "recommendation": self._get_recommendation(score, gaps)
        }
        
        # Add result to state validation results
        new_state.validation_results.append({
            "type": "completeness_check",
            "result": result
        })
        
        return new_state
    
    def _is_field_answered(self, field: str, state: SimpleState) -> bool:
        """
        Check if a required field has been answered
        
        Args:
            field: Field name to check
            state: Current state
            
        Returns:
            True if field has an answer, False otherwise
        """
        # Get the question for this field
        question = self.FIELD_TO_QUESTION.get(field)
        
        if not question:
            return False
        
        # Check if this question has been answered
        for req in state.requirements:
            if req.question == question and req.answer:
                return True
        
        return False
    
    def _get_recommendation(self, score: float, gaps: List[str]) -> str:
        """
        Get recommendation based on completeness
        
        Args:
            score: Completeness score
            gaps: List of missing fields
            
        Returns:
            Recommendation message
        """
        if score >= 0.85:
            return "Requirements are sufficiently complete for validation"
        elif score >= 0.6:
            if gaps:
                critical_gaps = [g for g in gaps if g in ["digital_inputs", "digital_outputs", "voltage", "temperature_range"]]
                if critical_gaps:
                    return f"Please provide critical information: {', '.join(critical_gaps)}"
                else:
                    return "Consider providing more details for better system recommendations"
            return "Requirements are partially complete, continue gathering information"
        else:
            return "Requirements need more information. Please answer the questions provided"
    
    def get_field_summary(self, state: SimpleState) -> Dict:
        """
        Get summary of field coverage
        
        Returns:
            Dict with field status for each category
        """
        summary = {}
        
        for category, fields in self.REQUIRED_FIELDS.items():
            field_status = {}
            for field in fields:
                field_status[field] = {
                    "answered": self._is_field_answered(field, state),
                    "question": self.FIELD_TO_QUESTION.get(field, "N/A")
                }
            
            summary[category] = {
                "required_fields": fields,
                "field_status": field_status,
                "answered_count": sum(1 for f in field_status.values() if f["answered"]),
                "total_fields": len(fields)
            }
        
        return summary