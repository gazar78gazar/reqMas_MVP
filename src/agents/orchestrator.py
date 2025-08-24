from typing import Dict, Any
from src.state.simple_state import SimpleState
from src.logging.decision_logger import DecisionLogger


class Orchestrator:
    """Simple orchestrator for routing between agents"""
    
    def __init__(self, logger: DecisionLogger):
        self.logger = logger
        self.max_iterations = 3
    
    def route(self, state: SimpleState) -> str:
        """
        Determine which agent should process next
        
        Returns:
            str: Name of next agent or "END" to terminate
        """
        reasoning = []
        
        # Check iteration limit
        if state.iteration_count >= self.max_iterations:
            reasoning.append(f"Reached maximum iterations ({self.max_iterations})")
            reasoning.append("Terminating to prevent infinite loops")
            next_agent = "END"
            
        # Check if we have any requirements
        elif len(state.requirements) == 0:
            reasoning.append("No requirements collected yet")
            reasoning.append("Starting with elicitor to gather initial requirements")
            next_agent = "elicitor"
            
        # Check completeness
        elif state.completeness_score < 0.85:
            reasoning.append(f"Completeness score: {state.completeness_score:.2f}")
            reasoning.append("Below threshold of 0.85")
            reasoning.append("Routing back to elicitor to gather more requirements")
            next_agent = "elicitor"  # Go back to get more questions!
            
        # Ready for validation
        else:
            reasoning.append(f"Completeness score: {state.completeness_score:.2f}")
            reasoning.append("Above threshold, requirements look complete")
            reasoning.append("Routing to validator for final checks")
            next_agent = "validator"
        
        # Log the routing decision
        self.logger.log_routing(
            current_state={
                "iteration_count": state.iteration_count,
                "completeness_score": state.completeness_score,
                "requirements_count": len(state.requirements),
                "categories_covered": state.get_categories_covered()
            },
            next_agent=next_agent,
            reasoning=reasoning
        )
        
        # Update state with decision
        state.add_decision(
            agent="orchestrator",
            decision=f"route_to_{next_agent}",
            reasoning=reasoning
        )
        
        # Update current agent in state
        if next_agent != "END":
            state.current_agent = next_agent
        
        return next_agent
    
    def process_error(self, state: SimpleState, error: Exception, agent: str) -> str:
        """
        Handle errors during agent processing
        
        Returns:
            str: Next action - usually "END" or retry logic
        """
        error_msg = f"Error in {agent}: {str(error)}"
        
        # Log the error
        self.logger.log_error(
            agent_name=agent,
            error_message=str(error),
            context={
                "iteration": state.iteration_count,
                "completeness": state.completeness_score
            }
        )
        
        # Add to state decision log
        state.add_decision(
            agent=agent,
            decision="ERROR",
            reasoning=[error_msg, "Terminating due to error"]
        )
        
        return "END"
    
    def should_continue(self, state: SimpleState) -> bool:
        """
        Check if processing should continue
        
        Returns:
            bool: True if should continue, False otherwise
        """
        # Check various termination conditions
        if state.iteration_count >= self.max_iterations:
            return False
        
        if state.current_agent == "END":
            return False
        
        # Check for repeated errors
        recent_errors = [
            d for d in state.decision_log[-3:]  # Last 3 decisions
            if d.get("decision") == "ERROR"
        ]
        if len(recent_errors) >= 2:
            return False
        
        return True
    
    def get_routing_summary(self, state: SimpleState) -> Dict[str, Any]:
        """
        Get summary of routing decisions for this session
        
        Returns:
            dict: Summary statistics
        """
        routes = {}
        for decision in state.decision_log:
            if decision["agent"] == "orchestrator":
                route = decision["decision"]
                if route not in routes:
                    routes[route] = 0
                routes[route] += 1
        
        return {
            "total_routes": len([d for d in state.decision_log if d["agent"] == "orchestrator"]),
            "routes": routes,
            "final_completeness": state.completeness_score,
            "iterations": state.iteration_count,
            "terminated": state.current_agent == "END"
        }