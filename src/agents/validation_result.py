"""
ValidationResult class for structured validation output
"""
from typing import List
from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    """Structured result from constraint validation"""
    
    is_valid: bool = Field(description="Whether all constraints are satisfied")
    violations: List[str] = Field(default_factory=list, description="List of constraint violations")
    warnings: List[str] = Field(default_factory=list, description="List of warnings")
    suggestions: List[str] = Field(default_factory=list, description="List of suggestions for improvement")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for backward compatibility"""
        return {
            "is_valid": self.is_valid,
            "violations": self.violations,
            "warnings": self.warnings,
            "suggestions": self.suggestions
        }
    
    def add_violation(self, violation: str) -> None:
        """Add a violation to the list"""
        self.violations.append(violation)
        self.is_valid = False
    
    def add_warning(self, warning: str) -> None:
        """Add a warning to the list"""
        self.warnings.append(warning)
    
    def add_suggestion(self, suggestion: str) -> None:
        """Add a suggestion to the list"""
        self.suggestions.append(suggestion)
    
    def get_summary(self) -> str:
        """Get a summary of the validation result"""
        if self.is_valid:
            if self.warnings:
                return f"Valid with {len(self.warnings)} warning(s)"
            else:
                return "All constraints satisfied"
        else:
            return f"Invalid: {len(self.violations)} violation(s) found"
    
    def get_all_messages(self) -> List[str]:
        """Get all messages (violations, warnings, suggestions) in one list"""
        messages = []
        
        if self.violations:
            messages.append("VIOLATIONS:")
            messages.extend(f"  - {v}" for v in self.violations)
        
        if self.warnings:
            messages.append("WARNINGS:")
            messages.extend(f"  - {w}" for w in self.warnings)
        
        if self.suggestions:
            messages.append("SUGGESTIONS:")
            messages.extend(f"  - {s}" for s in self.suggestions)
        
        return messages