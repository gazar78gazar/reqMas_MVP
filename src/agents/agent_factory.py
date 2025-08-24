"""
Agent Factory for creating all agents with proper logging
"""
from src.logging.decision_logger import DecisionLogger
from src.agents.elicitor import RequirementsElicitor
from src.agents.completeness import CompletenessChecker
from src.agents.validator import ConstraintValidator


def create_agents(session_id: str) -> dict:
    """
    Create all agents with a shared logger
    
    Args:
        session_id: Unique session identifier for logging
        
    Returns:
        Dictionary of initialized agents
    """
    logger = DecisionLogger(session_id)
    
    return {
        "elicitor": RequirementsElicitor(logger),
        "completeness": CompletenessChecker(logger),
        "validator": ConstraintValidator(logger)
    }


def create_agent(agent_type: str, session_id: str):
    """
    Create a single agent by type
    
    Args:
        agent_type: Type of agent ('elicitor', 'completeness', 'validator')
        session_id: Unique session identifier for logging
        
    Returns:
        Initialized agent instance
        
    Raises:
        ValueError: If agent_type is not recognized
    """
    logger = DecisionLogger(session_id)
    
    if agent_type == "elicitor":
        return RequirementsElicitor(logger)
    elif agent_type == "completeness":
        return CompletenessChecker(logger)
    elif agent_type == "validator":
        return ConstraintValidator(logger)
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")