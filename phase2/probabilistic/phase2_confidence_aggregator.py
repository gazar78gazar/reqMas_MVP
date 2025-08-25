"""
Confidence Aggregation Engine for Phase 2
Implements multiple strategies for combining agent confidences
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class AggregationStrategy(Enum):
    """Available confidence aggregation strategies"""
    WEIGHTED = "weighted"           # Weighted by agent expertise
    MINIMUM = "minimum"             # Conservative - take minimum
    BAYESIAN = "bayesian"          # Bayesian combination
    ADAPTIVE = "adaptive"          # Context-aware selection
    VOTING = "voting"              # Majority voting with threshold

@dataclass
class AgentConfidence:
    """Confidence from a single agent"""
    agent_id: str
    confidence: float
    expertise_weight: float
    evidence_count: int
    uncertainty_reason: Optional[str] = None

@dataclass
class AggregatedConfidence:
    """Result of confidence aggregation"""
    final_confidence: float
    strategy_used: AggregationStrategy
    contributing_agents: List[str]
    confidence_breakdown: Dict[str, float]
    requires_disambiguation: bool
    auto_resolve_eligible: bool
    explanation: str

class ConfidenceAggregator:
    """
    Aggregates confidence scores from multiple agents
    Implements Phase 2 confidence-based resolution
    """
    
    def __init__(self):
        # Agent expertise weights (based on domain)
        self.agent_weights = {
            'io_expert': 0.4,          # Highest weight - I/O is critical
            'system_expert': 0.35,     # System requirements important
            'communication_expert': 0.25  # Communication secondary
        }
        
        # Thresholds for different actions
        self.thresholds = {
            'auto_resolve_high': 0.8,   # Auto-resolve if diff > 30%
            'auto_resolve_diff': 0.3,   # Confidence difference threshold
            'require_user_low': 0.5,     # Always ask user below this
            'ambiguity_threshold': 0.2,  # Consider ambiguous if within 20%
            'voting_threshold': 0.6      # Majority threshold for voting
        }
        
        # Strategy selection rules
        self.strategy_rules = {
            'high_agreement': AggregationStrategy.WEIGHTED,
            'high_conflict': AggregationStrategy.MINIMUM,
            'uncertainty': AggregationStrategy.BAYESIAN,
            'critical_decision': AggregationStrategy.VOTING
        }
        
        # Track historical performance for adaptation
        self.strategy_performance = {strategy: 1.0 for strategy in AggregationStrategy}
    
    def aggregate(self, 
                  agent_confidences: List[AgentConfidence],
                  context: Optional[Dict] = None) -> AggregatedConfidence:
        """
        Main aggregation method - selects and applies appropriate strategy
        """
        if not agent_confidences:
            return self._create_low_confidence_result("No agent inputs")
        
        # Select aggregation strategy based on context
        strategy = self._select_strategy(agent_confidences, context)
        
        # Apply selected strategy
        if strategy == AggregationStrategy.WEIGHTED:
            result = self._weighted_aggregation(agent_confidences)
        elif strategy == AggregationStrategy.MINIMUM:
            result = self._minimum_aggregation(agent_confidences)
        elif strategy == AggregationStrategy.BAYESIAN:
            result = self._bayesian_aggregation(agent_confidences)
        elif strategy == AggregationStrategy.VOTING:
            result = self._voting_aggregation(agent_confidences)
        else:  # ADAPTIVE
            result = self._adaptive_aggregation(agent_confidences, context)
        
        # Determine action eligibility
        result.requires_disambiguation = self._needs_disambiguation(result, agent_confidences)
        result.auto_resolve_eligible = self._can_auto_resolve(result, agent_confidences)
        
        return result
    
    def _select_strategy(self, 
                        confidences: List[AgentConfidence],
                        context: Optional[Dict]) -> AggregationStrategy:
        """Select appropriate aggregation strategy based on inputs"""
        
        # Calculate agreement level
        conf_values = [c.confidence for c in confidences]
        std_dev = np.std(conf_values)
        mean_conf = np.mean(conf_values)
        
        # Critical decision context
        if context and context.get('is_critical', False):
            return AggregationStrategy.VOTING
        
        # High agreement - use weighted
        if std_dev < 0.1:
            return AggregationStrategy.WEIGHTED
        
        # High conflict - use conservative
        if std_dev > 0.3:
            return AggregationStrategy.MINIMUM
        
        # Uncertainty - use Bayesian
        if mean_conf < 0.6:
            return AggregationStrategy.BAYESIAN
        
        # Default to adaptive
        return AggregationStrategy.ADAPTIVE
    
    def _weighted_aggregation(self, confidences: List[AgentConfidence]) -> AggregatedConfidence:
        """Weighted average based on agent expertise"""
        total_weight = 0
        weighted_sum = 0
        breakdown = {}
        
        for conf in confidences:
            weight = self.agent_weights.get(conf.agent_id, 0.33)
            weighted_sum += conf.confidence * weight
            total_weight += weight
            breakdown[conf.agent_id] = conf.confidence
        
        final_confidence = weighted_sum / total_weight if total_weight > 0 else 0
        
        return AggregatedConfidence(
            final_confidence=final_confidence,
            strategy_used=AggregationStrategy.WEIGHTED,
            contributing_agents=[c.agent_id for c in confidences],
            confidence_breakdown=breakdown,
            requires_disambiguation=False,
            auto_resolve_eligible=False,
            explanation=f"Weighted average: I/O(40%), System(35%), Comm(25%)"
        )
    
    def _minimum_aggregation(self, confidences: List[AgentConfidence]) -> AggregatedConfidence:
        """Conservative approach - take minimum confidence"""
        min_conf = min(c.confidence for c in confidences)
        min_agent = min(confidences, key=lambda c: c.confidence)
        
        breakdown = {c.agent_id: c.confidence for c in confidences}
        
        return AggregatedConfidence(
            final_confidence=min_conf,
            strategy_used=AggregationStrategy.MINIMUM,
            contributing_agents=[c.agent_id for c in confidences],
            confidence_breakdown=breakdown,
            requires_disambiguation=False,
            auto_resolve_eligible=False,
            explanation=f"Conservative: using minimum from {min_agent.agent_id} due to {min_agent.uncertainty_reason or 'uncertainty'}"
        )
    
    def _bayesian_aggregation(self, confidences: List[AgentConfidence]) -> AggregatedConfidence:
        """Bayesian combination of probabilities"""
        # Convert confidences to odds
        odds = []
        breakdown = {}
        
        for conf in confidences:
            if conf.confidence > 0 and conf.confidence < 1:
                odds_value = conf.confidence / (1 - conf.confidence)
                weight = self.agent_weights.get(conf.agent_id, 0.33)
                odds.append(odds_value ** weight)
                breakdown[conf.agent_id] = conf.confidence
        
        if not odds:
            return self._create_low_confidence_result("Invalid confidences for Bayesian")
        
        # Combine odds
        combined_odds = np.prod(odds)
        
        # Convert back to probability
        final_confidence = combined_odds / (1 + combined_odds)
        
        return AggregatedConfidence(
            final_confidence=final_confidence,
            strategy_used=AggregationStrategy.BAYESIAN,
            contributing_agents=[c.agent_id for c in confidences],
            confidence_breakdown=breakdown,
            requires_disambiguation=False,
            auto_resolve_eligible=False,
            explanation="Bayesian combination considering evidence independence"
        )
    
    def _voting_aggregation(self, confidences: List[AgentConfidence]) -> AggregatedConfidence:
        """Majority voting with confidence threshold"""
        high_confidence_votes = 0
        breakdown = {}
        
        for conf in confidences:
            breakdown[conf.agent_id] = conf.confidence
            if conf.confidence >= self.thresholds['voting_threshold']:
                high_confidence_votes += 1
        
        # Need majority to be confident
        vote_ratio = high_confidence_votes / len(confidences)
        final_confidence = vote_ratio if vote_ratio > 0.5 else 0.3
        
        return AggregatedConfidence(
            final_confidence=final_confidence,
            strategy_used=AggregationStrategy.VOTING,
            contributing_agents=[c.agent_id for c in confidences],
            confidence_breakdown=breakdown,
            requires_disambiguation=False,
            auto_resolve_eligible=False,
            explanation=f"Voting: {high_confidence_votes}/{len(confidences)} agents confident"
        )
    
    def _adaptive_aggregation(self, 
                            confidences: List[AgentConfidence],
                            context: Optional[Dict]) -> AggregatedConfidence:
        """Adaptive strategy based on historical performance"""
        # Try multiple strategies and weight by past performance
        strategies = [
            self._weighted_aggregation(confidences),
            self._minimum_aggregation(confidences),
            self._bayesian_aggregation(confidences)
        ]
        
        # Weight by historical performance
        weighted_confidence = 0
        total_weight = 0
        
        for strat_result in strategies:
            weight = self.strategy_performance.get(strat_result.strategy_used, 1.0)
            weighted_confidence += strat_result.final_confidence * weight
            total_weight += weight
        
        final_confidence = weighted_confidence / total_weight if total_weight > 0 else 0
        
        breakdown = {c.agent_id: c.confidence for c in confidences}
        
        return AggregatedConfidence(
            final_confidence=final_confidence,
            strategy_used=AggregationStrategy.ADAPTIVE,
            contributing_agents=[c.agent_id for c in confidences],
            confidence_breakdown=breakdown,
            requires_disambiguation=False,
            auto_resolve_eligible=False,
            explanation="Adaptive: combining strategies based on performance"
        )
    
    def _needs_disambiguation(self, 
                            result: AggregatedConfidence,
                            confidences: List[AgentConfidence]) -> bool:
        """Determine if disambiguation is needed"""
        # Low overall confidence
        if result.final_confidence < self.thresholds['require_user_low']:
            return True
        
        # High variance in agent opinions
        conf_values = [c.confidence for c in confidences]
        if np.std(conf_values) > 0.3:
            return True
        
        # Conflicting evidence
        if any(c.uncertainty_reason for c in confidences):
            return True
        
        return False
    
    def _can_auto_resolve(self,
                         result: AggregatedConfidence,
                         confidences: List[AgentConfidence]) -> bool:
        """Determine if conflict can be auto-resolved"""
        # High confidence across all agents
        if result.final_confidence > self.thresholds['auto_resolve_high']:
            return True
        
        # Large confidence difference in binary choice
        if len(confidences) == 2:
            diff = abs(confidences[0].confidence - confidences[1].confidence)
            if diff > self.thresholds['auto_resolve_diff']:
                return True
        
        return False
    
    def _create_low_confidence_result(self, reason: str) -> AggregatedConfidence:
        """Create result for low confidence scenarios"""
        return AggregatedConfidence(
            final_confidence=0.0,
            strategy_used=AggregationStrategy.MINIMUM,
            contributing_agents=[],
            confidence_breakdown={},
            requires_disambiguation=True,
            auto_resolve_eligible=False,
            explanation=reason
        )
    
    def update_strategy_performance(self, 
                                   strategy: AggregationStrategy,
                                   success: bool):
        """Update historical performance for adaptive learning"""
        # Simple exponential moving average
        alpha = 0.1  # Learning rate
        current = self.strategy_performance[strategy]
        
        if success:
            self.strategy_performance[strategy] = current + alpha * (1 - current)
        else:
            self.strategy_performance[strategy] = current - alpha * current
    
    def explain_confidence(self, result: AggregatedConfidence) -> str:
        """Generate human-readable explanation of confidence calculation"""
        explanation = f"Confidence Analysis ({result.strategy_used.value} strategy):\n"
        explanation += f"Final Confidence: {result.final_confidence:.2%}\n\n"
        
        explanation += "Agent Contributions:\n"
        for agent, conf in result.confidence_breakdown.items():
            weight = self.agent_weights.get(agent, 0.33)
            explanation += f"  {agent}: {conf:.2%} (weight: {weight:.2f})\n"
        
        if result.requires_disambiguation:
            explanation += "\n⚠️ Disambiguation required - confidence too low or conflicting"
        elif result.auto_resolve_eligible:
            explanation += "\n✅ Auto-resolution eligible - high confidence difference"
        
        explanation += f"\nReasoning: {result.explanation}"
        
        return explanation


# Usage example for testing
if __name__ == "__main__":
    aggregator = ConfidenceAggregator()
    
    # Test case 1: High agreement
    confidences1 = [
        AgentConfidence("io_expert", 0.85, 0.4, 5),
        AgentConfidence("system_expert", 0.82, 0.35, 4),
        AgentConfidence("communication_expert", 0.88, 0.25, 3)
    ]
    
    result1 = aggregator.aggregate(confidences1)
    print("Test 1 - High Agreement:")
    print(aggregator.explain_confidence(result1))
    print()
    
    # Test case 2: Conflict
    confidences2 = [
        AgentConfidence("io_expert", 0.9, 0.4, 5),
        AgentConfidence("system_expert", 0.3, 0.35, 2, "Incompatible requirements"),
        AgentConfidence("communication_expert", 0.6, 0.25, 3)
    ]
    
    result2 = aggregator.aggregate(confidences2)
    print("Test 2 - Conflict:")
    print(aggregator.explain_confidence(result2))
    print()
    
    # Test case 3: Critical decision
    confidences3 = confidences1.copy()
    context = {'is_critical': True}
    
    result3 = aggregator.aggregate(confidences3, context)
    print("Test 3 - Critical Decision:")
    print(aggregator.explain_confidence(result3))
