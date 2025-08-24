from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
import json


class RequirementEntry(BaseModel):
    """Single requirement collected from user"""
    category: str = Field(description="I/O, Environment, Communication, or Power")
    question: str = Field(description="The question asked")
    answer: Optional[str] = Field(default=None, description="User's response")
    timestamp: datetime = Field(default_factory=datetime.now, description="When asked")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SimpleState(BaseModel):
    """Flat state structure for MVP - no blackboard complexity"""
    session_id: str = Field(description="Unique session identifier")
    messages: List[Dict] = Field(default_factory=list, description="Conversation history")
    requirements: List[RequirementEntry] = Field(default_factory=list, description="Collected requirements")
    completeness_score: float = Field(default=0.0, description="0.0 to 1.0")
    validation_results: List[Dict] = Field(default_factory=list, description="Validation outcomes")
    current_agent: str = Field(default="orchestrator", description="Active agent name")
    iteration_count: int = Field(default=0, description="Number of passes")
    decision_log: List[Dict] = Field(default_factory=list, description="All agent decisions")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def to_json(self) -> str:
        """Serialize state to JSON string"""
        return self.model_dump_json(indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SimpleState':
        """Load state from JSON string"""
        data = json.loads(json_str)
        # Convert ISO strings back to datetime for requirements
        if 'requirements' in data:
            for req in data['requirements']:
                if 'timestamp' in req and isinstance(req['timestamp'], str):
                    req['timestamp'] = datetime.fromisoformat(req['timestamp'])
        return cls(**data)
    
    def add_requirement(self, category: str, question: str, answer: Optional[str] = None) -> None:
        """Add a new requirement to the state"""
        entry = RequirementEntry(
            category=category,
            question=question,
            answer=answer
        )
        self.requirements.append(entry)
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to conversation history"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_decision(self, agent: str, decision: str, reasoning: List[str]) -> None:
        """Log an agent decision"""
        self.decision_log.append({
            "agent": agent,
            "decision": decision,
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat(),
            "iteration": self.iteration_count
        })
    
    def get_categories_covered(self) -> List[str]:
        """Get list of requirement categories that have been addressed"""
        categories = set()
        for req in self.requirements:
            if req.answer:  # Only count if answered
                categories.add(req.category)
        return list(categories)