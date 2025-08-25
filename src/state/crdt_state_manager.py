"""
Phase 1 CRDT State Manager
Production-ready implementation for conflict-free state synchronization
"""

import json
import time
import hashlib
from typing import Dict, Set, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
from collections import defaultdict


class ConstraintStrength(Enum):
    """Constraint strength levels for Phase 1"""
    MANDATORY = 10
    RECOMMENDED = 4


@dataclass
class Constraint:
    """Individual constraint with LWW-Element-Set properties"""
    id: str
    value: Any
    strength: ConstraintStrength
    timestamp: float
    source_agent: str
    confidence: float = 1.0
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        return self.id == other.id if isinstance(other, Constraint) else False


@dataclass
class Resolution:
    """Conflict resolution record"""
    conflict_type: str
    constraint_a: str
    constraint_b: str
    chosen: str
    reason: str
    timestamp: float
    auto_resolved: bool


@dataclass
class StateSnapshot:
    """Immutable state snapshot for agent processing"""
    use_cases: Dict[str, float]
    constraints: Dict[str, Constraint]
    resolutions: List[Resolution]
    timestamp: float
    version: int


class CRDTStateManager:
    """
    Conflict-free Replicated Data Type State Manager
    Implements LWW-Element-Set for constraints and G-Counter for confidence
    """
    
    def __init__(self, session_id: str, mutex_config: Dict):
        self.session_id = session_id
        self.mutex_config = mutex_config
        
        # Core CRDT structures
        self.use_case_votes = defaultdict(lambda: defaultdict(float))  # G-Counter per UC
        self.constraints = {}  # LWW-Element-Set
        self.resolutions = []  # Append-only log
        
        # Version tracking
        self.version = 0
        self.last_update = time.time()
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Performance metrics
        self.merge_count = 0
        self.conflict_count = 0
        
    def add_use_case_signal(self, use_case_id: str, confidence: float, agent_id: str) -> None:
        """Add positive signal for use case (G-Counter increment only)"""
        with self.lock:
            # G-Counter: only increment, never decrement
            current = self.use_case_votes[use_case_id][agent_id]
            self.use_case_votes[use_case_id][agent_id] = max(current, confidence)
            self._increment_version()
    
    def add_constraint(self, constraint: Constraint) -> Tuple[bool, Optional[str]]:
        """
        Add constraint using LWW-Element-Set semantics
        Returns: (success, conflict_message)
        """
        with self.lock:
            # Check for MUTEX conflicts
            conflict = self._check_mutex_conflict(constraint.id)
            if conflict:
                return self._handle_mutex_conflict(constraint, conflict)
            
            # LWW-Element-Set: keep newest by timestamp
            if constraint.id in self.constraints:
                existing = self.constraints[constraint.id]
                if constraint.timestamp > existing.timestamp:
                    self.constraints[constraint.id] = constraint
                    self._increment_version()
                    return True, None
                return False, "Older timestamp, ignored"
            else:
                self.constraints[constraint.id] = constraint
                self._increment_version()
                return True, None
    
    def merge_state(self, other_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        CRDT merge operation - combines states without conflicts
        """
        with self.lock:
            self.merge_count += 1
            merge_report = {
                "merged_constraints": 0,
                "merged_use_cases": 0,
                "conflicts_resolved": 0
            }
            
            # Merge use case votes (G-Counter merge)
            for uc_id, agent_votes in other_state.get("use_cases", {}).items():
                for agent_id, confidence in agent_votes.items():
                    current = self.use_case_votes[uc_id][agent_id]
                    self.use_case_votes[uc_id][agent_id] = max(current, confidence)
                    if confidence > current:
                        merge_report["merged_use_cases"] += 1
            
            # Merge constraints (LWW-Element-Set merge)
            for constraint_id, constraint_data in other_state.get("constraints", {}).items():
                new_constraint = Constraint(**constraint_data)
                success, msg = self.add_constraint(new_constraint)
                if success:
                    merge_report["merged_constraints"] += 1
                elif "conflict" in str(msg).lower():
                    merge_report["conflicts_resolved"] += 1
            
            # Merge resolutions (append-only log)
            for resolution_data in other_state.get("resolutions", []):
                self.resolutions.append(Resolution(**resolution_data))
            
            self._increment_version()
            return merge_report
    
    def get_snapshot(self) -> StateSnapshot:
        """Get immutable snapshot for agent processing"""
        with self.lock:
            # Calculate aggregated use case confidences
            use_case_scores = {}
            for uc_id, agent_votes in self.use_case_votes.items():
                # Sum all agent votes for each use case
                use_case_scores[uc_id] = sum(agent_votes.values()) / max(len(agent_votes), 1)
            
            return StateSnapshot(
                use_cases=dict(use_case_scores),
                constraints=dict(self.constraints),
                resolutions=list(self.resolutions),
                timestamp=self.last_update,
                version=self.version
            )
    
    def resolve_conflict(self, constraint_a: str, constraint_b: str, 
                        chosen: str, reason: str, auto: bool = False) -> None:
        """Record conflict resolution"""
        with self.lock:
            resolution = Resolution(
                conflict_type="MUTEX",
                constraint_a=constraint_a,
                constraint_b=constraint_b,
                chosen=chosen,
                reason=reason,
                timestamp=time.time(),
                auto_resolved=auto
            )
            self.resolutions.append(resolution)
            
            # Remove the non-chosen constraint
            rejected = constraint_b if chosen == constraint_a else constraint_a
            if rejected in self.constraints:
                del self.constraints[rejected]
            
            self._increment_version()
    
    def get_active_constraints(self) -> List[Constraint]:
        """Get all active constraints sorted by strength and timestamp"""
        with self.lock:
            constraints = list(self.constraints.values())
            # Sort by strength (descending) then timestamp (newest first)
            return sorted(constraints, 
                        key=lambda c: (c.strength.value, c.timestamp), 
                        reverse=True)
    
    def get_top_use_cases(self, n: int = 3) -> List[Tuple[str, float]]:
        """Get top N use cases by confidence"""
        with self.lock:
            use_case_scores = {}
            for uc_id, agent_votes in self.use_case_votes.items():
                use_case_scores[uc_id] = sum(agent_votes.values()) / max(len(agent_votes), 1)
            
            return sorted(use_case_scores.items(), 
                        key=lambda x: x[1], 
                        reverse=True)[:n]
    
    def _check_mutex_conflict(self, constraint_id: str) -> Optional[str]:
        """Check if constraint conflicts with existing constraints"""
        for category in self.mutex_config.values():
            for mutex_pair in category:
                if constraint_id == mutex_pair["constraint_a"]:
                    if mutex_pair["constraint_b"] in self.constraints:
                        self.conflict_count += 1
                        return mutex_pair["constraint_b"]
                elif constraint_id == mutex_pair["constraint_b"]:
                    if mutex_pair["constraint_a"] in self.constraints:
                        self.conflict_count += 1
                        return mutex_pair["constraint_a"]
        return None
    
    def _handle_mutex_conflict(self, new_constraint: Constraint, 
                              conflicting_id: str) -> Tuple[bool, str]:
        """Handle MUTEX conflict between constraints"""
        existing = self.constraints[conflicting_id]
        
        # Auto-resolution rules
        
        # Rule 1: Recency wins if within 30 seconds
        if new_constraint.timestamp - existing.timestamp < 30:
            # User is correcting themselves
            self.resolve_conflict(
                conflicting_id,
                new_constraint.id,
                new_constraint.id,
                "Recency rule: user correction within 30s",
                auto=True
            )
            self.constraints[new_constraint.id] = new_constraint
            return True, f"Auto-resolved: replaced {conflicting_id} with {new_constraint.id}"
        
        # Rule 2: Mandatory beats Recommended
        if new_constraint.strength == ConstraintStrength.MANDATORY and \
           existing.strength == ConstraintStrength.RECOMMENDED:
            self.resolve_conflict(
                conflicting_id,
                new_constraint.id,
                new_constraint.id,
                "Mandatory constraint overrides recommended",
                auto=True
            )
            self.constraints[new_constraint.id] = new_constraint
            return True, f"Auto-resolved: mandatory {new_constraint.id} replaced {conflicting_id}"
        
        # Rule 3: Higher confidence wins if difference > 0.3
        if abs(new_constraint.confidence - existing.confidence) > 0.3:
            winner = new_constraint if new_constraint.confidence > existing.confidence else existing
            loser = existing if winner == new_constraint else new_constraint
            
            if winner == new_constraint:
                self.resolve_conflict(
                    conflicting_id,
                    new_constraint.id,
                    new_constraint.id,
                    f"Higher confidence: {new_constraint.confidence:.2f} vs {existing.confidence:.2f}",
                    auto=True
                )
                self.constraints[new_constraint.id] = new_constraint
                return True, f"Auto-resolved: higher confidence {new_constraint.id}"
            else:
                return False, f"Rejected: lower confidence than {conflicting_id}"
        
        # Cannot auto-resolve - need user input
        return False, f"MUTEX conflict with {conflicting_id} - requires user resolution"
    
    def _increment_version(self) -> None:
        """Increment version and update timestamp"""
        self.version += 1
        self.last_update = time.time()
    
    def get_state_hash(self) -> str:
        """Get deterministic hash of current state"""
        with self.lock:
            state_str = json.dumps({
                "use_cases": dict(self.use_case_votes),
                "constraints": [c.id for c in sorted(self.constraints.values(), key=lambda x: x.id)],
                "version": self.version
            }, sort_keys=True)
            return hashlib.sha256(state_str.encode()).hexdigest()[:8]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        with self.lock:
            return {
                "version": self.version,
                "total_constraints": len(self.constraints),
                "total_resolutions": len(self.resolutions),
                "auto_resolution_rate": sum(1 for r in self.resolutions if r.auto_resolved) / max(len(self.resolutions), 1),
                "merge_count": self.merge_count,
                "conflict_count": self.conflict_count,
                "state_hash": self.get_state_hash()
            }
    
    def export_state(self) -> Dict[str, Any]:
        """Export full state for persistence or debugging"""
        with self.lock:
            return {
                "session_id": self.session_id,
                "version": self.version,
                "timestamp": self.last_update,
                "use_cases": dict(self.use_case_votes),
                "constraints": {
                    c_id: {
                        "id": c.id,
                        "value": c.value,
                        "strength": c.strength.value,
                        "timestamp": c.timestamp,
                        "source_agent": c.source_agent,
                        "confidence": c.confidence
                    }
                    for c_id, c in self.constraints.items()
                },
                "resolutions": [
                    {
                        "conflict_type": r.conflict_type,
                        "constraint_a": r.constraint_a,
                        "constraint_b": r.constraint_b,
                        "chosen": r.chosen,
                        "reason": r.reason,
                        "timestamp": r.timestamp,
                        "auto_resolved": r.auto_resolved
                    }
                    for r in self.resolutions
                ],
                "metrics": self.get_metrics()
            }


# Example usage and testing
if __name__ == "__main__":
    # Load mutex config from cleaned useCase.json
    mutex_config = {
        "power_performance": [
            {"constraint_a": "CNST_POWER_MAX_10W", "constraint_b": "CNST_PROCESSOR_MIN_I7"},
            {"constraint_a": "CNST_POWER_MAX_10W", "constraint_b": "CNST_GPU_REQUIRED"},
        ],
        "latency_connectivity": [
            {"constraint_a": "CNST_LATENCY_MAX_1MS", "constraint_b": "CNST_WIFI"},
        ]
    }
    
    # Create state manager
    state_mgr = CRDTStateManager("test-session-001", mutex_config)
    
    # Test adding constraints
    c1 = Constraint(
        id="CNST_POWER_MAX_10W",
        value=10,
        strength=ConstraintStrength.MANDATORY,
        timestamp=time.time(),
        source_agent="elicitor",
        confidence=0.9
    )
    
    success, msg = state_mgr.add_constraint(c1)
    print(f"Added constraint 1: {success}, {msg}")
    
    # Test MUTEX conflict
    time.sleep(0.1)
    c2 = Constraint(
        id="CNST_PROCESSOR_MIN_I7",
        value="i7",
        strength=ConstraintStrength.MANDATORY,
        timestamp=time.time(),
        source_agent="mapper",
        confidence=0.8
    )
    
    success, msg = state_mgr.add_constraint(c2)
    print(f"Added conflicting constraint: {success}, {msg}")
    
    # Test state export
    print("\nFinal state:")
    print(json.dumps(state_mgr.export_state(), indent=2))
