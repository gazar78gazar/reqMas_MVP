from typing import Dict, List, Optional
from copy import deepcopy
from src.state.simple_state import SimpleState
from src.logging.decision_logger import DecisionLogger


class RequirementsElicitor:
    """Agent responsible for asking questions to gather requirements"""
    
    # Fixed question paths for each category
    IO_QUESTIONS = [
        "How many digital inputs do you need?",
        "How many digital outputs do you need?",
        "Do you need analog inputs? If yes, how many and what type (0-10V, 4-20mA)?",
        "Do you need analog outputs? If yes, how many and what type?",
        "What is the maximum distance between I/O points and the controller?",
        "Do you need any special I/O like RTD, thermocouple, or high-speed counters?",
        "What response time do you need for I/O updates (milliseconds)?"
    ]
    
    ENV_QUESTIONS = [
        "What is the operating temperature range?",
        "Is this an indoor or outdoor installation?",
        "What is the humidity level (normal, high, condensing)?",
        "Are there any vibration or shock requirements?",
        "Is there exposure to dust, chemicals, or corrosive materials?"
    ]
    
    COMM_QUESTIONS = [
        "What communication protocols do you need (Ethernet, Modbus, Profibus, etc.)?",
        "Do you need remote access capability?",
        "How many devices will communicate with the PLC?",
        "What is the required data update rate for communications?",
        "Do you need redundant communication paths?"
    ]
    
    POWER_QUESTIONS = [
        "What is your available power supply voltage (24VDC, 120VAC, 240VAC)?",
        "What is your maximum power budget in watts?",
        "Do you need battery backup or UPS support?",
        "Do you need redundant power supplies?"
    ]
    
    CATEGORY_QUESTIONS = {
        "I/O": IO_QUESTIONS,
        "Environment": ENV_QUESTIONS,
        "Communication": COMM_QUESTIONS,
        "Power": POWER_QUESTIONS
    }
    
    def __init__(self, logger: DecisionLogger):
        self.logger = logger
    
    def get_next_questions(self, state: SimpleState) -> List[str]:
        """
        Returns questions from each category
        
        Args:
            state: Current state with requirements
            
        Returns:
            List of next questions to ask (up to 8, 2 per category)
        """
        reasoning = []
        next_questions = []
        asked_questions = {req.question for req in state.requirements}
        
        reasoning.append(f"Already asked {len(asked_questions)} questions")
        
        # Get 1-2 questions from EACH category for better coverage
        for category, questions in self.CATEGORY_QUESTIONS.items():
            category_qs = []
            for question in questions:
                if question not in asked_questions:
                    category_qs.append(question)
                    if len(category_qs) >= 2:  # Max 2 per category
                        break
            next_questions.extend(category_qs)
            if category_qs:
                reasoning.append(f"Added {len(category_qs)} questions from {category}")
        
        # Return up to 8 questions (2 per category × 4 categories)
        final_questions = next_questions[:8]
        
        reasoning.append(f"Returning {len(final_questions)} questions across categories")
        
        # Log decision
        self.logger.log_decision(
            agent_name="elicitor",
            input_received=f"State with {len(state.requirements)} requirements",
            reasoning_steps=reasoning,
            decision_made=f"return_{len(final_questions)}_questions",
            output_produced=f"Returning {len(final_questions)} questions"
        )
        
        return final_questions
    
    def process_answers(self, questions_answers: Dict[str, str], state: SimpleState) -> SimpleState:
        """
        Process any answers, even if question wasn't in current batch
        
        Args:
            questions_answers: Dictionary of question -> answer mappings
            state: Current state
            
        Returns:
            New state with processed answers (does not modify original)
        """
        # Create a deep copy of the state to avoid modifying the original
        new_state = deepcopy(state)
        reasoning = []
        processed = 0
        
        reasoning.append(f"Processing {len(questions_answers)} answers")
        
        for question, answer in questions_answers.items():
            if not answer:  # Skip empty answers
                continue
            
            # Check if already exists
            existing_req = None
            for req in new_state.requirements:
                if req.question == question:
                    existing_req = req
                    break
            
            if existing_req:
                if not existing_req.answer:  # Update if no answer yet
                    existing_req.answer = answer
                    reasoning.append(f"Updated answer for: {question[:50]}...")
                    processed += 1
                else:
                    reasoning.append(f"Skipping already answered: {question[:50]}...")
            else:
                # Determine category from question content
                category = self._determine_category(question)
                
                # Add new requirement with answer
                new_state.add_requirement(category, question, answer)
                reasoning.append(f"Added {category} requirement: {question[:50]}...")
                processed += 1
                
                # Add to conversation history
                new_state.add_message("assistant", question)
                new_state.add_message("user", answer)
        
        reasoning.append(f"Processed {processed} new/updated answers")
        
        # Log the processing
        self.logger.log_decision(
            agent_name="elicitor",
            input_received=f"Processing {len(questions_answers)} Q&A pairs",
            reasoning_steps=reasoning,
            decision_made="process_answers",
            output_produced=f"Processed {processed} requirements"
        )
        
        # Add decision to state
        new_state.add_decision(
            agent="elicitor",
            decision="process_answers",
            reasoning=reasoning
        )
        
        return new_state
    
    def _determine_category(self, question: str) -> str:
        """
        Determine category from question content
        
        Args:
            question: The question text
            
        Returns:
            Category name (I/O, Environment, Communication, Power, or Other)
        """
        question_lower = question.lower()
        
        # Check against known questions first
        for category, questions in self.CATEGORY_QUESTIONS.items():
            if question in questions:
                return category
        
        # Fallback to keyword matching
        if any(word in question_lower for word in ['input', 'output', 'i/o', 'analog', 'digital', 'distance', 'rtd', 'thermocouple', 'counter']):
            return "I/O"
        elif any(word in question_lower for word in ['temperature', 'humidity', 'indoor', 'outdoor', 'environment', 'vibration', 'shock', 'dust', 'chemical']):
            return "Environment"
        elif any(word in question_lower for word in ['protocol', 'network', 'communication', 'ethernet', 'modbus', 'remote', 'device', 'data rate']):
            return "Communication"
        elif any(word in question_lower for word in ['voltage', 'power', 'consumption', 'supply', 'battery', 'ups', 'redundant', 'vdc', 'vac', 'watts']):
            return "Power"
        else:
            return "Other"
    
    def get_progress(self, state: SimpleState) -> Dict:
        """
        Get elicitation progress statistics
        
        Returns:
            Dict with progress information
        """
        asked_questions = [req.question for req in state.requirements]
        total_questions = sum(len(questions) for questions in self.CATEGORY_QUESTIONS.values())
        
        # Count answered questions
        answered = sum(1 for req in state.requirements if req.answer)
        
        # Count by category
        category_progress = {}
        for category in self.CATEGORY_QUESTIONS:
            category_questions = self.CATEGORY_QUESTIONS[category]
            asked_in_category = sum(1 for q in category_questions if q in asked_questions)
            answered_in_category = sum(
                1 for req in state.requirements 
                if req.category == category and req.answer
            )
            category_progress[category] = {
                "total": len(category_questions),
                "asked": asked_in_category,
                "answered": answered_in_category
            }
        
        return {
            "total_questions": total_questions,
            "asked": len(asked_questions),
            "answered": answered,
            "percentage_asked": (len(asked_questions) / total_questions * 100) if total_questions > 0 else 0,
            "percentage_answered": (answered / total_questions * 100) if total_questions > 0 else 0,
            "by_category": category_progress
        }
    
    def is_complete(self, state: SimpleState) -> bool:
        """
        Check if all questions have been asked
        
        Returns:
            True if all questions asked, False otherwise
        """
        asked_questions = {req.question for req in state.requirements}
        total_questions = sum(len(q) for q in self.CATEGORY_QUESTIONS.values())
        
        for category, questions in self.CATEGORY_QUESTIONS.items():
            for question in questions:
                if question not in asked_questions:
                    return False
        
        return True