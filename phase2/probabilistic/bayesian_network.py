"""
Bayesian Network for Phase 2 Probabilistic Mapping
Handles UC inference, belief propagation, and confidence calculation
"""

import json
import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class UCNode:
    """Represents a Use Case node in the Bayesian network"""
    uc_id: str
    name: str
    prior_probability: float
    keywords: Set[str]
    strong_indicators: Set[str]
    weak_indicators: Set[str]
    related_ucs: List[str]
    constraint_patterns: List[str]

@dataclass
class Evidence:
    """Evidence for belief propagation"""
    text: str
    keywords: Set[str]
    constraints_mentioned: Set[str]
    confidence: float = 1.0
    source: str = "user_input"

@dataclass
class Belief:
    """Current belief state for a UC"""
    uc_id: str
    probability: float
    supporting_evidence: List[str]
    conflicting_evidence: List[str]

class BayesianNetwork:
    """
    Bayesian Network for UC and constraint inference
    Implements belief propagation with evidence accumulation
    """
    
    def __init__(self, usecase_file: str = "data/useCase.json"):
        self.nodes: Dict[str, UCNode] = {}
        self.beliefs: Dict[str, Belief] = {}
        self.evidence_history: List[Evidence] = []
        self.conditional_probabilities: Dict[Tuple[str, str], float] = {}
        
        # Thresholds for Phase 2
        self.ambiguity_threshold = 0.15  # UCs within 15% are ambiguous
        self.high_confidence = 0.7
        self.medium_confidence = 0.5
        
        # Load UC data and initialize network
        self._load_usecase_data(usecase_file)
        self._initialize_priors()
        self._build_conditional_probabilities()
    
    def _load_usecase_data(self, filepath: str):
        """Load UC definitions and build network nodes"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Extract UC patterns and indicators
            for uc_id, uc_data in data.get('use_cases', {}).items():
                # Strong indicators - domain-specific terms
                strong = set()
                weak = set()
                
                # Parse from UC description and requirements
                if 'industrial' in uc_data.get('name', '').lower():
                    strong.add('plc')
                    strong.add('scada')
                    strong.add('industrial')
                    weak.add('control')
                    weak.add('automation')
                
                if 'solar' in uc_data.get('name', '').lower():
                    strong.add('solar')
                    strong.add('photovoltaic')
                    strong.add('mppt')
                    weak.add('energy')
                    weak.add('power')
                
                if 'motion' in uc_data.get('name', '').lower():
                    strong.add('servo')
                    strong.add('motion')
                    strong.add('trajectory')
                    weak.add('motor')
                    weak.add('position')
                
                if 'water' in uc_data.get('name', '').lower():
                    strong.add('pump')
                    strong.add('flow')
                    strong.add('ph')
                    strong.add('treatment')
                    weak.add('water')
                    weak.add('tank')
                
                # Create UC node
                self.nodes[uc_id] = UCNode(
                    uc_id=uc_id,
                    name=uc_data.get('name', ''),
                    prior_probability=self._calculate_prior(uc_id),
                    keywords=strong | weak,
                    strong_indicators=strong,
                    weak_indicators=weak,
                    related_ucs=self._find_related_ucs(uc_id, data),
                    constraint_patterns=[]
                )
                
                # Initialize belief
                self.beliefs[uc_id] = Belief(
                    uc_id=uc_id,
                    probability=self.nodes[uc_id].prior_probability,
                    supporting_evidence=[],
                    conflicting_evidence=[]
                )
                
        except Exception as e:
            logger.error(f"Failed to load UC data: {e}")
            self._use_fallback_initialization()
    
    def _calculate_prior(self, uc_id: str) -> float:
        """Calculate prior probability based on UC frequency"""
        # Industry statistics for IoT/Industrial domains
        priors = {
            'UC3': 0.25,  # Industrial automation - most common
            'UC5': 0.15,  # Motion control
            'UC6': 0.12,  # Water treatment
            'UC2': 0.10,  # Solar/environmental
            'UC7': 0.08,  # Machine automation
            'UC12': 0.08, # Test & measurement
            'UC1': 0.05,  # Generic IoT
        }
        return priors.get(uc_id, 0.05)
    
    def _find_related_ucs(self, uc_id: str, data: dict) -> List[str]:
        """Find related UCs based on shared CSRs"""
        related = []
        # This would parse the actual relationships from useCase.json
        relationships = {
            'UC3': ['UC5', 'UC7'],  # Industrial related
            'UC5': ['UC3', 'UC7'],  # Motion related  
            'UC6': ['UC2'],         # Environmental monitoring
        }
        return relationships.get(uc_id, [])
    
    def _build_conditional_probabilities(self):
        """Build conditional probability tables"""
        # P(Evidence | UC) for different evidence types
        
        # Strong indicator matches
        for uc_id, node in self.nodes.items():
            for indicator in node.strong_indicators:
                self.conditional_probabilities[(indicator, uc_id)] = 0.9
            for indicator in node.weak_indicators:
                self.conditional_probabilities[(indicator, uc_id)] = 0.4
    
    def _use_fallback_initialization(self):
        """Fallback initialization if UC file not found"""
        logger.warning("Using fallback UC initialization")
        
        # Basic UC definitions for testing
        fallback_ucs = {
            'UC3': ('Industrial Automation', {'plc', 'industrial', 'scada'}, 0.25),
            'UC5': ('Motion Control', {'motion', 'servo', 'trajectory'}, 0.15),
            'UC6': ('Water Treatment', {'water', 'pump', 'flow', 'ph'}, 0.12),
        }
        
        for uc_id, (name, keywords, prior) in fallback_ucs.items():
            self.nodes[uc_id] = UCNode(
                uc_id=uc_id,
                name=name,
                prior_probability=prior,
                keywords=keywords,
                strong_indicators=keywords,
                weak_indicators=set(),
                related_ucs=[],
                constraint_patterns=[]
            )
            
            self.beliefs[uc_id] = Belief(
                uc_id=uc_id,
                probability=prior,
                supporting_evidence=[],
                conflicting_evidence=[]
            )
    
    def update_beliefs(self, evidence: Evidence) -> Dict[str, float]:
        """
        Update beliefs based on new evidence using Bayes rule
        Returns updated UC probabilities
        """
        self.evidence_history.append(evidence)
        
        # Extract keywords from evidence
        evidence_keywords = self._extract_keywords(evidence.text)
        evidence.keywords = evidence_keywords
        
        # Calculate likelihoods P(E|UC) for each UC
        likelihoods = {}
        for uc_id, node in self.nodes.items():
            likelihood = self._calculate_likelihood(evidence_keywords, node)
            likelihoods[uc_id] = likelihood
        
        # Apply Bayes rule: P(UC|E) = P(E|UC) * P(UC) / P(E)
        # P(E) is normalization constant
        total_probability = 0
        unnormalized = {}
        
        for uc_id, belief in self.beliefs.items():
            prior = belief.probability
            likelihood = likelihoods[uc_id]
            unnormalized[uc_id] = likelihood * prior
            total_probability += unnormalized[uc_id]
        
        # Normalize and update beliefs
        if total_probability > 0:
            for uc_id in self.beliefs:
                new_prob = unnormalized[uc_id] / total_probability
                
                # Track evidence
                if new_prob > self.beliefs[uc_id].probability:
                    self.beliefs[uc_id].supporting_evidence.append(evidence.text[:50])
                elif new_prob < self.beliefs[uc_id].probability:
                    self.beliefs[uc_id].conflicting_evidence.append(evidence.text[:50])
                
                self.beliefs[uc_id].probability = new_prob
        
        return self.get_uc_probabilities()
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract relevant keywords from input text"""
        text_lower = text.lower()
        keywords = set()
        
        # Check against all known indicators
        for node in self.nodes.values():
            for keyword in node.keywords:
                if keyword in text_lower:
                    keywords.add(keyword)
        
        # Add domain-specific term extraction here
        return keywords
    
    def _calculate_likelihood(self, evidence_keywords: Set[str], node: UCNode) -> float:
        """Calculate P(Evidence | UC)"""
        if not evidence_keywords:
            return 0.1  # Weak evidence
        
        likelihood = 0.1  # Base likelihood
        
        # Strong indicators have high impact
        strong_matches = evidence_keywords & node.strong_indicators
        if strong_matches:
            likelihood += 0.4 * len(strong_matches)
        
        # Weak indicators have lower impact
        weak_matches = evidence_keywords & node.weak_indicators
        if weak_matches:
            likelihood += 0.1 * len(weak_matches)
        
        # Cap at 0.95 to avoid certainty
        return min(likelihood, 0.95)
    
    def get_uc_probabilities(self) -> Dict[str, float]:
        """Get current UC probability distribution"""
        return {uc_id: belief.probability 
                for uc_id, belief in self.beliefs.items()}
    
    def get_top_ucs(self, n: int = 3) -> List[Tuple[str, float]]:
        """Get top N most probable UCs"""
        probs = self.get_uc_probabilities()
        sorted_ucs = sorted(probs.items(), key=lambda x: x[1], reverse=True)
        return sorted_ucs[:n]
    
    def is_ambiguous(self) -> bool:
        """Check if current belief state is ambiguous"""
        top_ucs = self.get_top_ucs(2)
        if len(top_ucs) < 2:
            return False
        
        # Check if top 2 UCs are within ambiguity threshold
        diff = abs(top_ucs[0][1] - top_ucs[1][1])
        return diff < self.ambiguity_threshold
    
    def get_disambiguation_info(self) -> Dict:
        """Get information for disambiguation questions"""
        if not self.is_ambiguous():
            return None
        
        top_ucs = self.get_top_ucs(3)
        
        # Find distinguishing features
        uc1_node = self.nodes[top_ucs[0][0]]
        uc2_node = self.nodes[top_ucs[1][0]]
        
        # Find unique indicators
        uc1_unique = uc1_node.strong_indicators - uc2_node.strong_indicators
        uc2_unique = uc2_node.strong_indicators - uc1_node.strong_indicators
        
        return {
            'ambiguous_ucs': top_ucs[:2],
            'uc1_features': uc1_unique,
            'uc2_features': uc2_unique,
            'confidence': max(top_ucs[0][1], top_ucs[1][1]),
            'entropy': self._calculate_entropy()
        }
    
    def _calculate_entropy(self) -> float:
        """Calculate entropy of current belief distribution"""
        entropy = 0
        for belief in self.beliefs.values():
            if belief.probability > 0:
                entropy -= belief.probability * np.log2(belief.probability)
        return entropy
    
    def reset_beliefs(self):
        """Reset beliefs to priors"""
        for uc_id, node in self.nodes.items():
            self.beliefs[uc_id] = Belief(
                uc_id=uc_id,
                probability=node.prior_probability,
                supporting_evidence=[],
                conflicting_evidence=[]
            )
        self.evidence_history.clear()
    
    def explain_beliefs(self) -> str:
        """Generate explanation of current beliefs"""
        top_ucs = self.get_top_ucs(3)
        
        explanation = "Current UC Analysis:\n"
        for uc_id, prob in top_ucs:
            node = self.nodes[uc_id]
            belief = self.beliefs[uc_id]
            explanation += f"\n{node.name} ({uc_id}): {prob:.2%} confidence\n"
            
            if belief.supporting_evidence:
                explanation += f"  Supporting: {', '.join(belief.supporting_evidence[:3])}\n"
            if belief.conflicting_evidence:
                explanation += f"  Conflicting: {', '.join(belief.conflicting_evidence[:3])}\n"
        
        if self.is_ambiguous():
            explanation += "\n⚠️ Ambiguous - disambiguation needed"
        
        return explanation


# Usage example for testing
if __name__ == "__main__":
    # Initialize network
    bn = BayesianNetwork()
    
    # Test evidence updates
    evidence1 = Evidence(
        text="I need to monitor water pumps and pH levels",
        keywords=set(),
        constraints_mentioned=set()
    )
    
    probs = bn.update_beliefs(evidence1)
    print("After evidence 1:", bn.get_top_ucs(3))
    print("Is ambiguous?", bn.is_ambiguous())
    
    # Add more evidence
    evidence2 = Evidence(
        text="Also need flow control and chemical dosing",
        keywords=set(),
        constraints_mentioned=set()
    )
    
    probs = bn.update_beliefs(evidence2)
    print("\nAfter evidence 2:", bn.get_top_ucs(3))
    print(bn.explain_beliefs())
