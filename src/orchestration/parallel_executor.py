"""
Phase 1 Parallel Execution Framework
Core orchestration for parallel agent execution with CRDT state management
"""

import asyncio
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import logging

# Import our CRDT State Manager
from src.state.crdt_state_manager import CRDTStateManager, Constraint, ConstraintStrength, StateSnapshot


class AgentType(Enum):
    """Agent types for Phase 1"""
    ELICITOR = "requirements_elicitor"
    MAPPER = "specification_mapper" 
    VALIDATOR = "constraint_validator"
    RESOLVER = "resolution_agent"


@dataclass
class AgentResult:
    """Result from individual agent execution"""
    agent_type: AgentType
    success: bool
    data: Dict[str, Any]
    execution_time: float
    error: Optional[str] = None


@dataclass
class ExecutionResult:
    """Combined result from parallel execution"""
    success: bool
    state_snapshot: StateSnapshot
    agent_results: List[AgentResult]
    total_time: float
    conflicts: List[Dict[str, Any]]
    completeness_score: float


class ParallelExecutor:
    """
    Orchestrates parallel agent execution with CRDT state management
    Production-ready with timeout, error handling, and performance tracking
    """
    
    def __init__(self, 
                 state_manager: CRDTStateManager,
                 use_case_config: Dict = None,  # Make it optional
                 timeout_seconds: float = 3.0,
                 max_workers: int = 4):
        """
        Initialize parallel executor
        
        Args:
            state_manager: CRDT state manager instance
            use_case_config: Loaded useCase.json configuration (optional)
            timeout_seconds: Maximum time for parallel execution
            max_workers: Maximum concurrent agent executions
        """
        # Auto-load config if not provided
        if use_case_config is None:
            import json
            import os
            config_path = os.path.join('data', 'useCase_phase1.json')
            with open(config_path, 'r') as f:
                use_case_config = json.load(f)
        
        self.state_manager = state_manager
        self.use_case_config = use_case_config
        self.timeout = timeout_seconds
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Initialize agents (would import from src.agents)
        self.agents = self._initialize_agents()
        
        # Performance tracking
        self.execution_count = 0
        self.total_execution_time = 0
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    def _initialize_agents(self) -> Dict[AgentType, Any]:
        """Initialize agent instances"""
        from src.agents.requirements_elicitor import RequirementsElicitorAgent
        from src.agents.specification_mapper import SpecificationMapperAgent
        from src.agents.constraint_validator import ConstraintValidatorAgent
        from src.agents.resolution_agent import ResolutionAgent
        
        return {
            AgentType.ELICITOR: RequirementsElicitorAgent(self.use_case_config),
            AgentType.MAPPER: SpecificationMapperAgent(self.use_case_config),
            AgentType.VALIDATOR: ConstraintValidatorAgent(self.use_case_config),
            AgentType.RESOLVER: ResolutionAgent(self.use_case_config)
        }
    
    async def process_input(self, user_input: str, context: Optional[Dict] = None) -> ExecutionResult:
        """
        Main entry point for processing user input
        
        Args:
            user_input: Raw user input text
            context: Optional context from previous interactions
            
        Returns:
            ExecutionResult with state snapshot and agent results
        """
        start_time = time.time()
        self.execution_count += 1
        
        # Get current state snapshot for agents
        snapshot = self.state_manager.get_snapshot()
        
        # Determine which agents should run
        active_agents = self._select_active_agents(user_input, snapshot)
        
        # Execute agents in parallel
        agent_results = await self._execute_parallel(
            active_agents, 
            user_input, 
            snapshot, 
            context or {}
        )
        
        # Process agent results and update state
        conflicts = self._process_results(agent_results)
        
        # Calculate completeness
        completeness = self._calculate_completeness()
        
        # Get final state
        final_snapshot = self.state_manager.get_snapshot()
        
        execution_time = time.time() - start_time
        self.total_execution_time += execution_time
        
        return ExecutionResult(
            success=all(r.success for r in agent_results),
            state_snapshot=final_snapshot,
            agent_results=agent_results,
            total_time=execution_time,
            conflicts=conflicts,
            completeness_score=completeness
        )
    
    async def _execute_parallel(self, 
                               agents: List[AgentType],
                               user_input: str,
                               snapshot: StateSnapshot,
                               context: Dict) -> List[AgentResult]:
        """Execute selected agents in parallel with timeout"""
        tasks = []
        
        for agent_type in agents:
            agent = self.agents[agent_type]
            task = asyncio.create_task(
                self._execute_agent_with_timeout(
                    agent_type,
                    agent,
                    user_input,
                    snapshot,
                    context
                )
            )
            tasks.append(task)
        
        # Wait for all with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            self.logger.warning(f"Parallel execution timeout after {self.timeout}s")
            # Cancel remaining tasks
            for task in tasks:
                if not task.done():
                    task.cancel()
            
            # Collect completed results
            results = []
            for task in tasks:
                if task.done() and not task.cancelled():
                    try:
                        results.append(task.result())
                    except:
                        pass
        
        # Filter out exceptions and convert to AgentResults
        agent_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                agent_results.append(AgentResult(
                    agent_type=agents[i],
                    success=False,
                    data={},
                    execution_time=self.timeout,
                    error=str(result)
                ))
            elif isinstance(result, AgentResult):
                agent_results.append(result)
        
        return agent_results
    
    async def _execute_agent_with_timeout(self,
                                        agent_type: AgentType,
                                        agent: Any,
                                        user_input: str,
                                        snapshot: StateSnapshot,
                                        context: Dict) -> AgentResult:
        """Execute single agent with error handling"""
        start_time = time.time()
        
        try:
            # Run agent processing
            result = await agent.process_async(user_input, snapshot, context)
            
            return AgentResult(
                agent_type=agent_type,
                success=True,
                data=result,
                execution_time=time.time() - start_time
            )
        except Exception as e:
            self.logger.error(f"Agent {agent_type.value} failed: {e}")
            return AgentResult(
                agent_type=agent_type,
                success=False,
                data={},
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    def _select_active_agents(self, user_input: str, snapshot: StateSnapshot) -> List[AgentType]:
        """
        Determine which agents should run based on input and state
        Phase 1: Always run Elicitor + Mapper in parallel, then Validator
        """
        # Check if we need resolution
        if snapshot.constraints and self._has_unresolved_conflicts(snapshot):
            return [AgentType.RESOLVER]
        
        # Standard parallel execution
        return [AgentType.ELICITOR, AgentType.MAPPER, AgentType.VALIDATOR]
    
    def _process_results(self, agent_results: List[AgentResult]) -> List[Dict[str, Any]]:
        """Process agent results and update CRDT state"""
        conflicts = []
        
        for result in agent_results:
            if not result.success:
                continue
            
            # Extract state updates from agent results
            agent_state = result.data.get('state_updates', {})
            
            # Process use case signals
            for uc_id, confidence in agent_state.get('use_cases', {}).items():
                self.state_manager.add_use_case_signal(
                    uc_id, 
                    confidence, 
                    result.agent_type.value
                )
            
            # Process constraints
            for constraint_data in agent_state.get('constraints', []):
                constraint = Constraint(
                    id=constraint_data['id'],
                    value=constraint_data.get('value'),
                    strength=ConstraintStrength(constraint_data.get('strength', 10)),
                    timestamp=time.time(),
                    source_agent=result.agent_type.value,
                    confidence=constraint_data.get('confidence', 1.0)
                )
                
                success, msg = self.state_manager.add_constraint(constraint)
                
                # Track conflicts
                if not success and 'conflict' in str(msg).lower():
                    conflicts.append({
                        'type': 'MUTEX',
                        'constraint': constraint.id,
                        'message': msg,
                        'agent': result.agent_type.value
                    })
        
        # Merge any additional state updates
        for result in agent_results:
            if result.success and 'full_state' in result.data:
                self.state_manager.merge_state(result.data['full_state'])
        
        return conflicts
    
    def _has_unresolved_conflicts(self, snapshot: StateSnapshot) -> bool:
        """Check if there are unresolved conflicts requiring user input"""
        # Check if last resolution was recent
        if snapshot.resolutions:
            last_resolution = snapshot.resolutions[-1]
            if time.time() - last_resolution.timestamp < 1.0:
                return False  # Just resolved
        
        # Check for pending conflicts in agent results
        # This would be more sophisticated in production
        return False
    
    def _calculate_completeness(self) -> float:
        """
        Calculate specification completeness score
        Phase 1 target: 70%
        """
        snapshot = self.state_manager.get_snapshot()
        
        # Basic completeness calculation
        score = 0.0
        weights = {
            'use_case_identified': 0.2,
            'mandatory_constraints': 0.5,
            'recommended_constraints': 0.2,
            'conflicts_resolved': 0.1
        }
        
        # Use case identification
        if snapshot.use_cases:
            top_uc = self.state_manager.get_top_use_cases(1)
            if top_uc and top_uc[0][1] > 0.8:
                score += weights['use_case_identified']
        
        # Constraint coverage
        mandatory_count = sum(1 for c in snapshot.constraints.values() 
                            if c.strength == ConstraintStrength.MANDATORY)
        if mandatory_count >= 5:
            score += weights['mandatory_constraints']
        elif mandatory_count >= 3:
            score += weights['mandatory_constraints'] * 0.5
        
        recommended_count = sum(1 for c in snapshot.constraints.values()
                               if c.strength == ConstraintStrength.RECOMMENDED)
        if recommended_count >= 3:
            score += weights['recommended_constraints']
        
        # Conflict resolution
        if not self._has_unresolved_conflicts(snapshot):
            score += weights['conflicts_resolved']
        
        return min(score, 1.0)
    
    def resolve_conflict(self, choice: str, conflict_id: str) -> bool:
        """
        Resolve a conflict based on user choice
        
        Args:
            choice: 'A' or 'B' for binary choice
            conflict_id: Identifier of the conflict
            
        Returns:
            Success status
        """
        # This would be called when user makes a choice
        # Implementation depends on conflict storage mechanism
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get execution metrics"""
        avg_time = self.total_execution_time / max(self.execution_count, 1)
        
        return {
            'execution_count': self.execution_count,
            'average_execution_time': avg_time,
            'total_execution_time': self.total_execution_time,
            'state_metrics': self.state_manager.get_metrics()
        }


# Mock agent classes removed - using imported agents from src.agents
