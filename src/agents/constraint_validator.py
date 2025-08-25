"""
Constraint Validator Agent
Validates constraints for consistency and MUTEX violations
Checks constraint relationships and completeness
"""

from typing import Dict, List

# Import from the correct location
from src.state.crdt_state_manager import StateSnapshot, ConstraintStrength


class ConstraintValidatorAgent:
    """
    Validates constraints for consistency and MUTEX violations
    Checks constraint relationships and completeness
    """
    
    def __init__(self, use_case_config: Dict):
        self.use_case_config = use_case_config
        self.mutex_rules = use_case_config.get('mutex_constraints', {})
        
        # Validation rules
        self.io_limits = {
            'digital': 256,
            'analog': 64
        }
        
        self.temperature_ranges = {
            'standard': (-10, 60),
            'extended': (-40, 85),
            'extreme': (-55, 125)
        }
    
    async def process_async(self, user_input: str, snapshot: StateSnapshot, context: Dict) -> Dict:
        """
        Validate current constraints and check for issues
        """
        state_updates = {
            'validation_status': 'valid',
            'issues': [],
            'warnings': []
        }
        
        # Check I/O limits
        io_constraints = [c for c in snapshot.constraints.values() 
                         if 'IO' in c.id or 'DIGITAL' in c.id or 'ANALOG' in c.id]
        
        total_digital = sum(c.value for c in io_constraints 
                          if 'DIGITAL' in c.id and hasattr(c, 'value'))
        total_analog = sum(c.value for c in io_constraints 
                         if 'ANALOG' in c.id and hasattr(c, 'value'))
        
        if total_digital > self.io_limits['digital']:
            state_updates['warnings'].append({
                'type': 'io_limit',
                'message': f'Digital I/O count ({total_digital}) exceeds single controller limit',
                'suggestion': 'Consider distributed I/O architecture'
            })
        
        if total_analog > self.io_limits['analog']:
            state_updates['warnings'].append({
                'type': 'io_limit',
                'message': f'Analog I/O count ({total_analog}) exceeds single controller limit',
                'suggestion': 'Consider multiple controllers or I/O modules'
            })
        
        # Check for incompatible constraint combinations
        constraint_ids = set(c.id for c in snapshot.constraints.values())
        
        # Check outdoor + high performance
        if 'CNST_IP54' in constraint_ids and 'CNST_GPU_REQUIRED' in constraint_ids:
            state_updates['warnings'].append({
                'type': 'compatibility',
                'message': 'GPU systems difficult to ruggedize for outdoor use',
                'suggestion': 'Consider edge server in enclosure'
            })
        
        # Validate completeness for identified use case
        if snapshot.use_cases:
            top_uc = max(snapshot.use_cases.items(), key=lambda x: x[1])
            if top_uc[1] > 0.8:  # Strong UC identification
                required = self._get_required_constraints(top_uc[0])
                missing = [r for r in required if r not in constraint_ids]
                
                if missing:
                    state_updates['warnings'].append({
                        'type': 'completeness',
                        'message': f'Missing typical constraints for {top_uc[0]}',
                        'missing': missing
                    })
        
        # Check for MUTEX violations (handled by CRDT, but validate)
        for category, rules in self.mutex_rules.items():
            for rule in rules:
                if rule['constraint_a'] in constraint_ids and rule['constraint_b'] in constraint_ids:
                    state_updates['issues'].append({
                        'type': 'mutex_violation',
                        'message': f"Conflicting constraints: {rule['constraint_a']} vs {rule['constraint_b']}",
                        'resolution': rule.get('resolution', 'User must choose')
                    })
                    state_updates['validation_status'] = 'has_conflicts'
        
        return {'state_updates': state_updates}
    
    def _get_required_constraints(self, uc_id: str) -> List[str]:
        """Get typically required constraints for a use case"""
        required_map = {
            'UC1': ['CNST_REDUNDANT_POWER', 'CNST_IEC61850'],
            'UC2': ['CNST_POWER_MAX_10W', 'CNST_LTE'],
            'UC3': ['CNST_LATENCY_MAX_1MS', 'CNST_TSN_SUPPORT'],
            'UC6': ['CNST_ANALOG_IO_MIN_8', 'CNST_IP54'],
            'UC9': ['CNST_IP69K'],
            'UC10': ['CNST_ATEX_CERTIFIED', 'CNST_FANLESS']
        }
        return required_map.get(uc_id, [])