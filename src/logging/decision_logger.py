import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


class DecisionLogger:
    """Logger for tracking all agent decisions and reasoning"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.log_dir = Path(f"logs/sessions/{session_id}")
        self.log_file = self.log_dir / "decisions.jsonl"
        
        # Create directories if they don't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def log_decision(
        self,
        agent_name: str,
        input_received: Any,
        reasoning_steps: List[str],
        decision_made: str,
        output_produced: Any,
        error: Optional[str] = None
    ) -> None:
        """Log a single agent decision"""
        
        # Truncate large inputs/outputs for logging
        input_str = str(input_received)[:1000] if input_received else ""
        output_str = str(output_produced)[:1000] if output_produced else ""
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "agent": agent_name,
            "input": input_str,
            "reasoning": reasoning_steps,
            "decision": decision_made,
            "output": output_str,
            "error": error
        }
        
        # Write to JSONL file (append mode)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def log_routing(
        self,
        current_state: Dict,
        next_agent: str,
        reasoning: List[str]
    ) -> None:
        """Log orchestrator routing decision"""
        self.log_decision(
            agent_name="orchestrator",
            input_received=f"State with {current_state.get('iteration_count', 0)} iterations",
            reasoning_steps=reasoning,
            decision_made=f"Route to {next_agent}",
            output_produced=next_agent
        )
    
    def log_error(
        self,
        agent_name: str,
        error_message: str,
        context: Optional[Dict] = None
    ) -> None:
        """Log an error that occurred during processing"""
        self.log_decision(
            agent_name=agent_name,
            input_received=context,
            reasoning_steps=["Error occurred during processing"],
            decision_made="ERROR",
            output_produced=None,
            error=error_message
        )
    
    def get_session_logs(self) -> List[Dict]:
        """Read all logs for this session"""
        logs = []
        if self.log_file.exists():
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        logs.append(json.loads(line))
        return logs
    
    def get_agent_decisions(self, agent_name: str) -> List[Dict]:
        """Get all decisions made by a specific agent"""
        all_logs = self.get_session_logs()
        return [log for log in all_logs if log.get('agent') == agent_name]
    
    def get_errors(self) -> List[Dict]:
        """Get all errors logged in this session"""
        all_logs = self.get_session_logs()
        return [log for log in all_logs if log.get('error') is not None]
    
    def summary(self) -> Dict:
        """Get summary statistics for this session"""
        logs = self.get_session_logs()
        
        agents = {}
        errors = 0
        
        for log in logs:
            agent = log.get('agent', 'unknown')
            if agent not in agents:
                agents[agent] = 0
            agents[agent] += 1
            
            if log.get('error'):
                errors += 1
        
        return {
            "session_id": self.session_id,
            "total_decisions": len(logs),
            "agents": agents,
            "errors": errors,
            "log_file": str(self.log_file)
        }