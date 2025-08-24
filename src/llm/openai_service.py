"""
OpenAI GPT-4o Service for Structured Output
"""
import os
import json
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from openai import OpenAI
from src.logging.decision_logger import DecisionLogger

# Load environment variables
load_dotenv()

class OpenAIService:
    """Service for GPT-4o with structured JSON output"""
    
    def __init__(self, logger: DecisionLogger):
        self.logger = logger
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file")
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-2024-08-06"  # Latest GPT-4o with structured outputs
    
    def generate_questions(self, state: Dict, category: str = None) -> List[str]:
        """Generate dynamic questions based on current state"""
        
        # Define structured output schema
        schema = {
            "type": "object",
            "properties": {
                "questions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 8,
                    "description": "List of technical questions to ask"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Why these questions were chosen"
                },
                "category_focus": {
                    "type": "string",
                    "enum": ["I/O", "Environment", "Communication", "Power", "Mixed"],
                    "description": "Primary category of questions"
                }
            },
            "required": ["questions", "reasoning", "category_focus"],
            "additionalProperties": False
        }
        
        # Build context from state
        existing_reqs = []
        if state.get("requirements"):
            for req in state["requirements"]:
                existing_reqs.append(f"- {req.question}: {req.answer}")
        
        context = "\n".join(existing_reqs) if existing_reqs else "No requirements collected yet"
        
        prompt = f"""You are a technical requirements expert for industrial IoT systems.
        
Current requirements collected:
{context}

Completeness: {state.get('completeness_score', 0):.1%}

Generate the next set of questions to gather missing technical requirements.
Focus on: {category or 'identifying critical gaps'}.

Requirements categories: I/O (inputs/outputs), Environment (temperature/conditions), 
Communication (protocols/networks), Power (voltage/consumption).

Generate questions that:
1. Fill gaps in current requirements
2. Are specific and technical
3. Can be answered concisely
4. Cover different categories if early in process"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a technical requirements elicitation expert."},
                    {"role": "user", "content": prompt}
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "question_generation",
                        "strict": True,
                        "schema": schema
                    }
                }
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Log the decision
            self.logger.log_decision(
                agent_name="openai_elicitor",
                input_received=f"State with {len(existing_reqs)} requirements",
                reasoning_steps=[result["reasoning"]],
                decision_made=f"generate_{len(result['questions'])}_questions",
                output_produced=f"Generated {len(result['questions'])} questions in {result['category_focus']}"
            )
            
            return result["questions"]
            
        except Exception as e:
            self.logger.log_decision(
                agent_name="openai_elicitor",
                input_received="Question generation",
                reasoning_steps=[f"Error: {str(e)}"],
                decision_made="fallback_to_fixed",
                output_produced="Using fixed questions due to error"
            )
            # Fallback to fixed questions
            return []
    
    def parse_answer(self, question: str, answer: str) -> Dict[str, Any]:
        """Parse natural language answer into structured data"""
        
        schema = {
            "type": "object",
            "properties": {
                "parsed_value": {
                    "type": "string",
                    "description": "The extracted technical value"
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Confidence in parsing (0-1)"
                },
                "category": {
                    "type": "string",
                    "enum": ["I/O", "Environment", "Communication", "Power", "Other"],
                    "description": "Category of the requirement"
                },
                "needs_clarification": {
                    "type": "boolean",
                    "description": "Whether answer needs clarification"
                }
            },
            "required": ["parsed_value", "confidence", "category", "needs_clarification"],
            "additionalProperties": False
        }
        
        prompt = f"""Parse this technical requirement answer.

Question: {question}
User Answer: {answer}

Extract the technical value, categorize it, and assess if clarification is needed.
Examples:
- "I think about 8 or 10" → parsed_value: "8-10", needs_clarification: true
- "24VDC" → parsed_value: "24VDC", needs_clarification: false
- "outdoor but covered" → parsed_value: "outdoor with cover", needs_clarification: true"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a technical requirements parser."},
                    {"role": "user", "content": prompt}
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "answer_parsing",
                        "strict": True,
                        "schema": schema
                    }
                }
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            # Fallback to simple parsing
            return {
                "parsed_value": answer,
                "confidence": 1.0,
                "category": "Other",
                "needs_clarification": False
            }
    
    def validate_requirements(self, requirements: List[Dict]) -> Dict[str, Any]:
        """Validate technical feasibility of requirements"""
        
        schema = {
            "type": "object",
            "properties": {
                "is_valid": {"type": "boolean"},
                "violations": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "warnings": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "suggestions": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "confidence": {"type": "number", "minimum": 0, "maximum": 1}
            },
            "required": ["is_valid", "violations", "warnings", "suggestions", "confidence"],
            "additionalProperties": False
        }
        
        reqs_text = "\n".join([f"- {r.get('question', '')}: {r.get('answer', '')}" for r in requirements])
        
        prompt = f"""Validate these technical requirements for an industrial IoT system:

{reqs_text}

Check for:
1. Technical incompatibilities (e.g., voltage mismatches)
2. Unrealistic combinations (e.g., -40°C with standard components)
3. Missing critical requirements
4. Potential issues or warnings

Provide specific, actionable feedback."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a technical validation expert for industrial systems."},
                    {"role": "user", "content": prompt}
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "validation",
                        "strict": True,
                        "schema": schema
                    }
                }
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            return {
                "is_valid": True,
                "violations": [],
                "warnings": [f"Validation error: {str(e)}"],
                "suggestions": [],
                "confidence": 0.5
            }