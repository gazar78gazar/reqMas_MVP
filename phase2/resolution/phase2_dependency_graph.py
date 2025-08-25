"""
Constraint Dependency Graph for Phase 2
Builds and analyzes constraint relationships for progressive conflict detection
"""

import json
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class RelationType(Enum):
    """Types of constraint relationships"""
    MUTEX = "mutex"              # Mutually exclusive
    REQUIRES = "requires"        # One requires the other
    IMPLIES = "implies"          # One implies the other
    CONFLICTS = "conflicts"      # Soft conflict
    ENHANCES = "enhances"        # Works better together
    LIMITS = "limits"            # One limits the other

@dataclass
class ConstraintNode:
    """Node in the dependency graph"""
    constraint_id: str
    name: str
    category: str
    relationships: Dict[str, List[str]] = field(default_factory=dict)
    properties: Dict[str, any] = field(default_factory=dict)
    
    # For progressive conflict detection
    cumulative_requirements: Set[str] = field(default_factory=set)
    threshold_values: Dict[str, float] = field(default_factory=dict)

@dataclass
class ConflictPath:
    """Represents a conflict discovered through graph traversal"""
    conflict_type: str
    participants: List[str]
    path: List[str]
    severity: float
    explanation: str
    resolution_hints: List[str]

class DependencyGraph:
    """
    Constraint dependency graph for progressive conflict detection
    Handles transitive relationships and multi-constraint conflicts
    """
    
    def __init__(self, constraints_file: str = "data/constraints.json"):
        self.nodes: Dict[str, ConstraintNode] = {}
        self.adjacency_list: Dict[str, Set[Tuple[str, RelationType]]] = defaultdict(set)
        self.mutex_pairs: Set[Tuple[str, str]] = set()
        self.requirement_chains: Dict[str, Set[str]] = defaultdict(set)
        
        # Progressive conflict patterns
        self.progressive_patterns = {
            'space_accumulation': ['COMPACT_FORM', 'MODULAR', 'HIGH_IO'],
            'power_escalation': ['LOW_POWER', 'PROCESSING', 'GPU'],
            'environment_conflict': ['INDOOR', 'PRECISION', 'HARSH_ENV'],
            'cost_creep': ['BUDGET', 'FEATURES', 'QUALITY']
        }
        
        # Load constraint definitions
        self._load_constraints(constraints_file)
        self._build_relationships()
        self._identify_transitive_conflicts()
    
    def _load_constraints(self, filepath: str):
        """Load constraint definitions and build nodes"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Build nodes from constraints
            for const_id, const_data in data.get('constraints', {}).items():
                node = ConstraintNode(
                    constraint_id=const_id,
                    name=const_data.get('name', ''),
                    category=const_data.get('category', 'general'),
                    properties=const_data.get('properties', {})
                )
                
                # Extract threshold values
                if 'max_value' in const_data:
                    node.threshold_values['max'] = const_data['max_value']
                if 'min_value' in const_data:
                    node.threshold_values['min'] = const_data['min_value']
                
                self.nodes[const_id] = node
            
            # Load explicit MUTEX relationships
            for mutex_pair in data.get('constraint_relationships', {}).get('MUTEX_pairs', []):
                if len(mutex_pair) == 2:
                    self._add_mutex(mutex_pair[0], mutex_pair[1])
            
        except Exception as e:
            logger.error(f"Failed to load constraints: {e}")
            self._use_fallback_constraints()
    
    def _use_fallback_constraints(self):
        """Fallback constraint definitions for testing"""
        # Core MUTEX pairs that must be detected
        mutex_definitions = [
            ('CNST_FANLESS', 'CNST_GPU_REQUIRED'),
            ('CNST_POWER_MAX_10W', 'CNST_PROCESSOR_MIN_I7'),
            ('CNST_COMPACT_FORM', 'CNST_DIGITAL_IO_MIN_64'),
            ('CNST_COMPACT_FORM', 'CNST_DIGITAL_IO_MIN_128'),
            ('CNST_INDOOR_USE', 'CNST_IP69K'),
            ('CNST_PRECISION_TEMP', 'CNST_HARSH_ENV'),
            ('CNST_WIFI', 'CNST_LATENCY_MAX_1MS'),
            ('CNST_BATTERY_POWERED', 'CNST_HIGH_COMPUTE')
        ]
        
        for c1, c2 in mutex_definitions:
            self._add_mutex(c1, c2)
            
            # Create nodes if they don't exist
            if c1 not in self.nodes:
                self.nodes[c1] = ConstraintNode(c1, c1, 'general')
            if c2 not in self.nodes:
                self.nodes[c2] = ConstraintNode(c2, c2, 'general')
    
    def _build_relationships(self):
        """Build comprehensive relationship graph"""
        # Add requirement relationships
        requirements = {
            'CNST_GPU_REQUIRED': ['CNST_COOLING_ACTIVE', 'CNST_POWER_MIN_100W'],
            'CNST_PROCESSOR_MIN_I7': ['CNST_MEMORY_MIN_8GB', 'CNST_POWER_MIN_35W'],
            'CNST_DIGITAL_IO_MIN_128': ['CNST_EXPANSION_SLOTS', 'CNST_LARGE_FORM'],
            'CNST_REALTIME_1MS': ['CNST_RTOS', 'CNST_DETERMINISTIC'],
            'CNST_IP69K': ['CNST_SEALED_ENCLOSURE', 'CNST_INDUSTRIAL_CONNECTORS']
        }
        
        for source, targets in requirements.items():
            for target in targets:
                self._add_relationship(source, target, RelationType.REQUIRES)
        
        # Add implication relationships
        implications = {
            'CNST_OUTDOOR': ['CNST_WEATHER_RESISTANT', 'CNST_TEMP_EXTENDED'],
            'CNST_MEDICAL': ['CNST_SAFETY_CERTIFIED', 'CNST_EMC_COMPLIANT'],
            'CNST_AUTOMOTIVE': ['CNST_VIBRATION_RESISTANT', 'CNST_TEMP_AUTOMOTIVE']
        }
        
        for source, targets in implications.items():
            for target in targets:
                self._add_relationship(source, target, RelationType.IMPLIES)
        
        # Add limiting relationships
        limits = {
            'CNST_BUDGET_1000': ['CNST_FEATURES_BASIC'],
            'CNST_COMPACT_FORM': ['CNST_IO_LIMITED'],
            'CNST_BATTERY_POWERED': ['CNST_PERFORMANCE_LIMITED']
        }
        
        for source, targets in limits.items():
            for target in targets:
                self._add_relationship(source, target, RelationType.LIMITS)
    
    def _add_mutex(self, c1: str, c2: str):
        """Add mutual exclusion relationship"""
        self.mutex_pairs.add(tuple(sorted([c1, c2])))
        self._add_relationship(c1, c2, RelationType.MUTEX)
        self._add_relationship(c2, c1, RelationType.MUTEX)
    
    def _add_relationship(self, source: str, target: str, rel_type: RelationType):
        """Add directed relationship to graph"""
        self.adjacency_list[source].add((target, rel_type))
        
        if source in self.nodes:
            if rel_type.value not in self.nodes[source].relationships:
                self.nodes[source].relationships[rel_type.value] = []
            self.nodes[source].relationships[rel_type.value].append(target)
    
    def _identify_transitive_conflicts(self):
        """Pre-compute transitive conflicts through graph analysis"""
        # Find conflicts through requirement chains
        for node_id in self.nodes:
            requirements = self._get_all_requirements(node_id)
            
            # Check if requirements conflict with each other
            for req1 in requirements:
                for req2 in requirements:
                    if req1 != req2 and self.is_mutex(req1, req2):
                        logger.info(f"Transitive conflict: {node_id} → {req1} ⊗ {req2}")
    
    def _get_all_requirements(self, constraint_id: str, visited: Set[str] = None) -> Set[str]:
        """Get all transitive requirements for a constraint"""
        if visited is None:
            visited = set()
        
        if constraint_id in visited:
            return set()
        
        visited.add(constraint_id)
        requirements = {constraint_id}
        
        # BFS for all requirements
        queue = deque([constraint_id])
        
        while queue:
            current = queue.popleft()
            
            for neighbor, rel_type in self.adjacency_list.get(current, []):
                if rel_type in [RelationType.REQUIRES, RelationType.IMPLIES]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        requirements.add(neighbor)
                        queue.append(neighbor)
        
        return requirements
    
    def is_mutex(self, c1: str, c2: str) -> bool:
        """Check if two constraints are mutually exclusive"""
        return tuple(sorted([c1, c2])) in self.mutex_pairs
    
    def detect_progressive_conflict(self, constraints: List[str]) -> Optional[ConflictPath]:
        """
        Detect conflicts that emerge as constraints accumulate
        This is the KEY method for Phase 2 progressive detection
        """
        if len(constraints) < 2:
            return None
        
        # Check each new constraint against accumulated state
        accumulated = set()
        
        for i, new_constraint in enumerate(constraints):
            # Check direct MUTEX with accumulated
            for existing in accumulated:
                if self.is_mutex(new_constraint, existing):
                    return ConflictPath(
                        conflict_type="direct_mutex",
                        participants=[existing, new_constraint],
                        path=constraints[:i+1],
                        severity=1.0,
                        explanation=f"{new_constraint} conflicts with previously set {existing}",
                        resolution_hints=[
                            f"Remove {existing} to allow {new_constraint}",
                            f"Skip {new_constraint} to keep {existing}",
                            "Find alternative that satisfies both needs"
                        ]
                    )
            
            # Check transitive conflicts
            new_requirements = self._get_all_requirements(new_constraint)
            accumulated_requirements = set()
            for existing in accumulated:
                accumulated_requirements.update(self._get_all_requirements(existing))
            
            # Find conflicts in requirement sets
            for new_req in new_requirements:
                for acc_req in accumulated_requirements:
                    if self.is_mutex(new_req, acc_req):
                        return ConflictPath(
                            conflict_type="transitive_conflict",
                            participants=[new_constraint] + list(accumulated),
                            path=constraints[:i+1],
                            severity=0.8,
                            explanation=f"{new_constraint} requires {new_req} which conflicts with {acc_req}",
                            resolution_hints=[
                                f"Choose between {new_constraint} and constraints requiring {acc_req}",
                                "Consider partial implementation",
                                "Look for alternative solutions"
                            ]
                        )
            
            # Check threshold violations (accumulation conflicts)
            conflict = self._check_threshold_violations(accumulated | {new_constraint})
            if conflict:
                return conflict
            
            accumulated.add(new_constraint)
        
        return None
    
    def _check_threshold_violations(self, constraints: Set[str]) -> Optional[ConflictPath]:
        """Check for conflicts due to accumulated threshold violations"""
        # Check space constraints
        space_constraints = {'CNST_COMPACT_FORM', 'CNST_MODULAR', 
                           'CNST_DIGITAL_IO_MIN_64', 'CNST_DIGITAL_IO_MIN_128'}
        active_space = constraints & space_constraints
        
        if 'CNST_COMPACT_FORM' in active_space:
            if 'CNST_DIGITAL_IO_MIN_128' in active_space:
                return ConflictPath(
                    conflict_type="space_violation",
                    participants=list(active_space),
                    path=list(active_space),
                    severity=0.9,
                    explanation="Compact form factor cannot accommodate 128 I/O points",
                    resolution_hints=[
                        "Use larger form factor",
                        "Reduce I/O count",
                        "Use distributed I/O modules"
                    ]
                )
            elif 'CNST_DIGITAL_IO_MIN_64' in active_space and 'CNST_MODULAR' in active_space:
                return ConflictPath(
                    conflict_type="space_warning",
                    participants=list(active_space),
                    path=list(active_space),
                    severity=0.6,
                    explanation="Compact + Modular + 64 I/O is challenging but possible",
                    resolution_hints=[
                        "Consider stackable modules",
                        "Use high-density connectors"
                    ]
                )
        
        # Check power constraints
        power_constraints = {'CNST_POWER_MAX_10W', 'CNST_POWER_MAX_20W',
                           'CNST_GPU_REQUIRED', 'CNST_PROCESSOR_MIN_I7'}
        active_power = constraints & power_constraints
        
        if 'CNST_POWER_MAX_10W' in active_power:
            if any(c in active_power for c in ['CNST_GPU_REQUIRED', 'CNST_PROCESSOR_MIN_I7']):
                return ConflictPath(
                    conflict_type="power_violation",
                    participants=list(active_power),
                    path=list(active_power),
                    severity=1.0,
                    explanation="10W power limit incompatible with high-performance components",
                    resolution_hints=[
                        "Increase power budget",
                        "Use low-power alternatives",
                        "Consider edge AI accelerators"
                    ]
                )
        
        return None
    
    def find_conflict_resolution_path(self, 
                                     conflicting_constraints: List[str]) -> List[str]:
        """Find alternative constraints that avoid conflicts"""
        alternatives = []
        
        for constraint in conflicting_constraints:
            # Find constraints in same category that don't conflict
            if constraint in self.nodes:
                category = self.nodes[constraint].category
                
                for node_id, node in self.nodes.items():
                    if node.category == category and node_id != constraint:
                        # Check if alternative conflicts with others
                        has_conflict = False
                        for other in conflicting_constraints:
                            if other != constraint and self.is_mutex(node_id, other):
                                has_conflict = True
                                break
                        
                        if not has_conflict:
                            alternatives.append(node_id)
        
        return alternatives
    
    def explain_relationship_path(self, c1: str, c2: str) -> str:
        """Explain the relationship path between two constraints"""
        if self.is_mutex(c1, c2):
            return f"{c1} ⊗ {c2}: Direct mutual exclusion"
        
        # BFS to find path
        queue = deque([(c1, [c1])])
        visited = {c1}
        
        while queue:
            current, path = queue.popleft()
            
            for neighbor, rel_type in self.adjacency_list.get(current, []):
                if neighbor == c2:
                    path.append(neighbor)
                    return self._format_path_explanation(path, c1, c2)
                
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return f"No direct relationship found between {c1} and {c2}"
    
    def _format_path_explanation(self, path: List[str], start: str, end: str) -> str:
        """Format a relationship path for human reading"""
        if len(path) == 2:
            return f"{start} → {end}: Direct relationship"
        
        explanation = f"Path from {start} to {end}:\n"
        for i in range(len(path) - 1):
            explanation += f"  {path[i]} → {path[i+1]}\n"
        
        return explanation


# Usage example for testing
if __name__ == "__main__":
    graph = DependencyGraph()
    
    # Test 1: Direct MUTEX detection
    print("Test 1: Direct MUTEX")
    print(f"FANLESS vs GPU: {graph.is_mutex('CNST_FANLESS', 'CNST_GPU_REQUIRED')}")
    print()
    
    # Test 2: Progressive conflict - should detect
    print("Test 2: Progressive Conflict (Compact → High I/O)")
    sequence1 = ['CNST_COMPACT_FORM', 'CNST_MODULAR', 'CNST_DIGITAL_IO_MIN_128']
    conflict1 = graph.detect_progressive_conflict(sequence1)
    if conflict1:
        print(f"✓ Conflict detected: {conflict1.explanation}")
        print(f"  Resolution hints: {conflict1.resolution_hints[0]}")
    else:
        print("✗ No conflict detected (ERROR - should detect!)")
    print()
    
    # Test 3: Progressive conflict - environmental
    print("Test 3: Environmental Progression")
    sequence2 = ['CNST_INDOOR_USE', 'CNST_PRECISION_TEMP', 'CNST_IP69K']
    conflict2 = graph.detect_progressive_conflict(sequence2)
    if conflict2:
        print(f"✓ Conflict detected: {conflict2.explanation}")
    else:
        print("✗ No conflict detected (ERROR - should detect!)")
    print()
    
    # Test 4: Find alternatives
    print("Test 4: Finding Alternatives")
    alternatives = graph.find_conflict_resolution_path(['CNST_COMPACT_FORM', 'CNST_DIGITAL_IO_MIN_128'])
    print(f"Alternatives: {alternatives[:3] if alternatives else 'None found'}")
