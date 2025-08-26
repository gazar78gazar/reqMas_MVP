"""
Phase 2 Enhanced Orchestrator
Integrates Bayesian Network, Confidence Aggregation, and Progressive Conflict Detection
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

# Phase 2 imports
from phase2.probabilistic.bayesian_network import BayesianNetwork, Evidence
from phase2.probabilistic.confidence_aggregator import (
    ConfidenceAggregator, AgentConfidence, AggregationStrategy
)
from phase2.resolution.dependency_graph import DependencyGraph

# Phase 1 imports - adjusted to match project structure
from src.state.crdt_state_manager import CRDTStateManager as SharedStateManager
from src.agents.requirements_elicitor import RequirementsElicitorAgent as RequirementsElicitor
from src.agents.specification_mapper import SpecificationMapperAgent as SpecificationMapper
from src.agents.resolution_agent import ResolutionAgent

logger = logging.getLogger(__name__)

@dataclass
class Phase2ProcessingResult:
    """Result from Phase 2 processing"""
    uc_probabilities: Dict[str, float]
    aggregated_confidence: float
    needs_disambiguation: bool
    auto_resolve: bool
    conflicts_detected: List[Any]
    suggested_resolution: Optional[str]
    abq_question: Optional[Dict]

class Phase2Orchestrator:
    """
    Enhanced orchestrator with Phase 2 capabilities
    Adds probabilistic mapping, smart resolution, and dynamic routing
    """
    
    def __init__(self, state_manager: SharedStateManager):
        # Phase 1 components
        self.state_manager = state_manager
        self.elicitor = RequirementsElicitor()
        self.mapper = SpecificationMapper()
        self.resolver = ResolutionAgent()
        
        # Phase 2 components
        self.bayesian_net = BayesianNetwork()
        self.confidence_agg = ConfidenceAggregator()
        self.dep_graph = DependencyGraph()
        
        # Dynamic routing thresholds
        self.routing_thresholds = {
            'direct': 0.8,
            'parallel': 0.6,
            'disambiguation': 0.4
        }
        
        # Track processing state
        self.processing_history = []
        
    async def process(self, user_input: str, session_id: str) -> Phase2ProcessingResult:
        """
        Main processing pipeline with Phase 2 enhancements
        """
        logger.info(f"Phase 2 processing: {user_input[:50]}...")
        
        # Step 1: Update Bayesian beliefs
        evidence = Evidence(
            text=user_input,
            keywords=set(),
            constraints_mentioned=set(),
            confidence=1.0
        )
        uc_probabilities = self.bayesian_net.update_beliefs(evidence)
        
        # Step 2: Dynamic routing based on UC confidence
        route = self._determine_route(uc_probabilities)
        logger.info(f"Selected route: {route}")
        
        # Step 3: Execute parallel agent analysis
        agent_results = await self._execute_agents(user_input, uc_probabilities, route)
        
        # Step 4: Aggregate confidence from agents
        agent_confidences = self._extract_agent_confidences(agent_results)
        aggregated_result = self.confidence_agg.aggregate(
            agent_confidences,
            context={'route': route, 'uc_probs': uc_probabilities}
        )
        
        # Step 5: Check for progressive conflicts
        current_constraints = self.state_manager.get_active_constraints()
        new_constraints = self._extract_new_constraints(agent_results)
        
        conflicts = []
        if new_constraints:
            # Check each new constraint for conflicts
            for new_const in new_constraints:
                test_sequence = current_constraints + [new_const]
                conflict = self.dep_graph.detect_progressive_conflict(test_sequence)
                if conflict:
                    conflicts.append(conflict)
        
        # Step 6: Determine action based on confidence and conflicts
        result = Phase2ProcessingResult(
            uc_probabilities=uc_probabilities,
            aggregated_confidence=aggregated_result.final_confidence,
            needs_disambiguation=False,
            auto_resolve=False,
            conflicts_detected=conflicts,
            suggested_resolution=None,
            abq_question=None
        )
        
        # Handle conflicts
        if conflicts:
            result = self._handle_conflicts(result, conflicts, aggregated_result)
        
        # Handle ambiguity
        elif self.bayesian_net.is_ambiguous():
            result = self._handle_ambiguity(result)
        
        # Handle low confidence
        elif aggregated_result.requires_disambiguation:
            result = self._handle_low_confidence(result, aggregated_result)
        
        # Update state if proceeding
        if not result.needs_disambiguation and not conflicts:
            await self._update_state(agent_results, new_constraints)
        
        return result
    
    def _determine_route(self, uc_probabilities: Dict[str, float]) -> str:
        """Determine processing route based on UC confidence"""
        top_uc = max(uc_probabilities.values()) if uc_probabilities else 0
        
        if top_uc >= self.routing_thresholds['direct']:
            return 'direct'
        elif top_uc >= self.routing_thresholds['parallel']:
            return 'parallel'
        else:
            return 'disambiguation'
    
    async def _execute_agents(self, 
                             user_input: str, 
                             uc_probs: Dict[str, float],
                             route: str) -> Dict:
        """Execute agents based on selected route"""
        
        if route == 'direct':
            # High confidence - minimal processing
            elicitor_result = await self.elicitor.process(user_input)
            return {
                'elicitor': elicitor_result,
                'confidence': 0.9
            }
        
        elif route == 'parallel':
            # Medium confidence - full parallel processing
            tasks = [
                self.elicitor.process(user_input),
                self.mapper.process(user_input, uc_probs)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            return {
                'elicitor': results[0] if not isinstance(results[0], Exception) else None,
                'mapper': results[1] if not isinstance(results[1], Exception) else None,
                'confidence': 0.7
            }
        
        else:  # disambiguation
            # Low confidence - need more information
            return {
                'needs_clarification': True,
                'confidence': 0.3
            }
    
    def _extract_agent_confidences(self, agent_results: Dict) -> List[AgentConfidence]:
        """Extract confidence scores from agent results"""
        confidences = []
        
        # Map your actual agent IDs and extract their confidences
        if 'elicitor' in agent_results and agent_results['elicitor']:
            confidences.append(AgentConfidence(
                agent_id='io_expert',  # Map to Phase 2 naming
                confidence=agent_results.get('confidence', 0.5),
                expertise_weight=0.4,
                evidence_count=len(agent_results['elicitor'].get('requirements', []))
            ))
        
        # Add other agents as they're integrated
        # This is a placeholder - adjust based on your actual agent structure
        
        # Default confidences if needed
        if not confidences:
            confidences = [
                AgentConfidence('io_expert', 0.5, 0.4, 0),
                AgentConfidence('system_expert', 0.5, 0.35, 0),
                AgentConfidence('communication_expert', 0.5, 0.25, 0)
            ]
        
        return confidences
    
    def _extract_new_constraints(self, agent_results: Dict) -> List[str]:
        """Extract new constraints from agent results"""
        constraints = []
        
        if 'mapper' in agent_results and agent_results['mapper']:
            constraints.extend(agent_results['mapper'].get('constraints', []))
        
        if 'elicitor' in agent_results and agent_results['elicitor']:
            # Extract constraints from requirements
            for req in agent_results['elicitor'].get('requirements', []):
                if 'constraint_id' in req:
                    constraints.append(req['constraint_id'])
        
        return constraints
    
    def _handle_conflicts(self, 
                         result: Phase2ProcessingResult,
                         conflicts: List,
                         aggregated_result) -> Phase2ProcessingResult:
        """Handle detected conflicts"""
        
        primary_conflict = conflicts[0]  # Handle first/most severe
        
        # Check if auto-resolvable
        if aggregated_result.auto_resolve_eligible and primary_conflict.severity < 0.7:
            result.auto_resolve = True
            result.suggested_resolution = primary_conflict.resolution_hints[0]
        else:
            # Generate A/B question for conflict resolution
            result.needs_disambiguation = True
            result.abq_question = self._generate_conflict_abq(primary_conflict)
        
        return result
    
    def _handle_ambiguity(self, result: Phase2ProcessingResult) -> Phase2ProcessingResult:
        """Handle UC ambiguity"""
        
        disambig_info = self.bayesian_net.get_disambiguation_info()
        
        if disambig_info:
            result.needs_disambiguation = True
            result.abq_question = self._generate_uc_abq(disambig_info)
        
        return result
    
    def _handle_low_confidence(self, 
                              result: Phase2ProcessingResult,
                              aggregated_result) -> Phase2ProcessingResult:
        """Handle low confidence scenarios"""
        
        result.needs_disambiguation = True
        result.abq_question = {
            'type': 'clarification',
            'question': 'Can you provide more specific details about your requirements?',
            'reason': aggregated_result.explanation
        }
        
        return result
    
    def _generate_conflict_abq(self, conflict) -> Dict:
        """Generate A/B question for conflict resolution"""
        
        participants = conflict.participants[:2]  # Binary choice
        
        return {
            'type': 'conflict_resolution',
            'question': f"We detected a conflict: {conflict.explanation}",
            'options': {
                'A': f"Prioritize {participants[0]}",
                'B': f"Prioritize {participants[1]}"
            },
            'context': conflict.resolution_hints
        }
    
    def _generate_uc_abq(self, disambig_info: Dict) -> Dict:
        """Generate A/B question for UC disambiguation"""
        
        uc1, conf1 = disambig_info['ambiguous_ucs'][0]
        uc2, conf2 = disambig_info['ambiguous_ucs'][1]
        
        return {
            'type': 'uc_disambiguation',
            'question': 'Which best describes your application?',
            'options': {
                'A': f"{uc1} - {', '.join(list(disambig_info['uc1_features'])[:2])}",
                'B': f"{uc2} - {', '.join(list(disambig_info['uc2_features'])[:2])}"
            },
            'confidence': max(conf1, conf2)
        }
    
    async def _update_state(self, agent_results: Dict, new_constraints: List[str]):
        """Update shared state with validated results"""
        
        # Update constraints
        for constraint in new_constraints:
            self.state_manager.add_constraint(constraint)
        
        # Update requirements
        if 'elicitor' in agent_results and agent_results['elicitor']:
            for req in agent_results['elicitor'].get('requirements', []):
                self.state_manager.add_requirement(req)
        
        # Update UC probabilities
        uc_probs = self.bayesian_net.get_uc_probabilities()
        self.state_manager.update_uc_probabilities(uc_probs)
    
    def process_user_response(self, abq_response: str, context: Dict) -> Dict:
        """Process user's response to A/B question"""
        
        if context['type'] == 'conflict_resolution':
            # User chose A or B for conflict
            choice = abq_response.upper()
            if choice == 'A':
                # Keep first constraint, remove second
                return {'action': 'keep_first', 'remove': context['options']['B']}
            else:
                # Keep second, remove first
                return {'action': 'keep_second', 'remove': context['options']['A']}
        
        elif context['type'] == 'uc_disambiguation':
            # Update Bayesian network with user's UC choice
            chosen_uc = context['options'][abq_response.upper()].split(' - ')[0]
            
            # Create strong evidence for chosen UC
            evidence = Evidence(
                text=f"User confirmed: {chosen_uc}",
                keywords=set(),
                constraints_mentioned=set(),
                confidence=0.95
            )
            self.bayesian_net.update_beliefs(evidence)
            
            return {'action': 'uc_selected', 'uc': chosen_uc}
        
        return {'action': 'unknown'}
    
    def get_status(self) -> Dict:
        """Get current Phase 2 system status"""
        return {
            'uc_beliefs': self.bayesian_net.get_top_ucs(3),
            'is_ambiguous': self.bayesian_net.is_ambiguous(),
            'confidence_report': self.confidence_agg.get_confidence_report(),
            'active_constraints': self.state_manager.get_active_constraints(),
            'processing_history': len(self.processing_history)
        }


# Usage example
async def test_phase2_orchestrator():
    """Test the Phase 2 orchestrator"""
    
    # Initialize with your state manager
    state_manager = SharedStateManager()  # Your existing state manager
    orchestrator = Phase2Orchestrator(state_manager)
    
    # Test progressive conflict detection
    test_inputs = [
        "I need a compact industrial controller",
        "It should be modular and expandable",
        "Must support 128 digital I/O points"
    ]
    
    for input_text in test_inputs:
        result = await orchestrator.process(input_text, "test_session")
        
        print(f"\nInput: {input_text}")
        print(f"UC Probabilities: {result.uc_probabilities}")
        print(f"Confidence: {result.aggregated_confidence:.2%}")
        
        if result.conflicts_detected:
            print(f"⚠️ Conflict: {result.conflicts_detected[0].explanation}")
        
        if result.abq_question:
            print(f"❓ Question: {result.abq_question['question']}")
            print(f"   A: {result.abq_question['options']['A']}")
            print(f"   B: {result.abq_question['options']['B']}")


if __name__ == "__main__":
    asyncio.run(test_phase2_orchestrator())
