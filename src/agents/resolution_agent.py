"""
Resolution Agent
Handles conflict resolution and generates binary questions
Manages MUTEX conflicts and ambiguous requirements
"""

from typing import Dict, Tuple

# Import from the correct location
from src.state.crdt_state_manager import StateSnapshot, ConstraintStrength


class ResolutionAgent:
    """
    Handles conflict resolution and generates binary questions
    Manages MUTEX conflicts and ambiguous requirements
    """
    
    def __init__(self, use_case_config: Dict):
        self.use_case_config = use_case_config
        self.mutex_rules = use_case_config.get('mutex_constraints', {})
    
    async def process_async(self, user_input: str, snapshot: StateSnapshot, context: Dict) -> Dict:
        """
        Generate resolution options for conflicts
        """
        state_updates = {
            'resolution_needed': False,
            'conflicts': []
        }
        
        # Check for unresolved MUTEX conflicts
        constraint_ids = set(c.id for c in snapshot.constraints.values())
        
        for category, rules in self.mutex_rules.items():
            for rule in rules:
                if rule['constraint_a'] in constraint_ids and rule['constraint_b'] in constraint_ids:
                    # Found a conflict that needs resolution
                    conflict = self._create_binary_question(
                        rule['constraint_a'],
                        rule['constraint_b'],
                        rule.get('resolution', 'Choose your priority'),
                        category
                    )
                    state_updates['conflicts'].append(conflict)
                    state_updates['resolution_needed'] = True
        
        # Check for UC conflicts (multiple high-confidence use cases)
        if len(snapshot.use_cases) > 1:
            top_ucs = sorted(snapshot.use_cases.items(), key=lambda x: x[1], reverse=True)[:2]
            if top_ucs[0][1] > 0.6 and top_ucs[1][1] > 0.6:
                # Both have high confidence - need resolution
                conflict = self._create_uc_question(top_ucs[0], top_ucs[1])
                state_updates['conflicts'].append(conflict)
                state_updates['resolution_needed'] = True
        
        return {'state_updates': state_updates}
    
    def _create_binary_question(self, constraint_a: str, constraint_b: str, 
                               resolution_hint: str, category: str) -> Dict:
        """Create binary question for MUTEX resolution"""
        
        # Get human-readable descriptions
        descriptions = {
            'CNST_POWER_MAX_10W': 'Ultra-low power (10W) for solar/battery operation',
            'CNST_PROCESSOR_MIN_I7': 'High-performance Core i7 processor',
            'CNST_GPU_REQUIRED': 'GPU acceleration for AI/vision processing',
            'CNST_FANLESS': 'Fanless operation for reliability',
            'CNST_LATENCY_MAX_1MS': 'Sub-millisecond deterministic response',
            'CNST_WIFI': 'Wireless WiFi connectivity',
            'CNST_LTE': 'Cellular LTE connectivity',
            'CNST_COMPACT_FORM': 'Compact form factor',
            'CNST_DIGITAL_IO_MIN_64': 'High I/O density (64+ channels)'
        }
        
        impacts = {
            'power_performance': {
                'low_power': 'Enables off-grid operation but limits processing capability',
                'high_performance': 'Provides computational power but requires AC power'
            },
            'latency_connectivity': {
                'deterministic': 'Guarantees real-time response but requires wired connection',
                'wireless': 'Enables remote deployment but cannot guarantee timing'
            },
            'form_factor': {
                'compact': 'Fits in small spaces but limits I/O expansion',
                'high_io': 'Supports many connections but requires larger enclosure'
            }
        }
        
        category_impact = impacts.get(category, {})
        
        return {
            'type': 'binary_choice',
            'category': 'mutex_conflict',
            'question': f"Your requirements conflict. {resolution_hint}",
            'option_a': {
                'constraint': constraint_a,
                'description': descriptions.get(constraint_a, constraint_a),
                'impact': category_impact.get('option_a', 'Choose this for option A benefits')
            },
            'option_b': {
                'constraint': constraint_b,
                'description': descriptions.get(constraint_b, constraint_b),
                'impact': category_impact.get('option_b', 'Choose this for option B benefits')
            },
            'resolution_required': True
        }
    
    def _create_uc_question(self, uc_a: Tuple, uc_b: Tuple) -> Dict:
        """Create binary question for use case resolution"""
        
        uc_names = {
            'UC1': 'Power Substation Management',
            'UC2': 'Solar Array Monitoring',
            'UC3': 'Motion Control Systems',
            'UC4': 'Quality Inspection',
            'UC5': 'Industrial Automation',
            'UC6': 'Water Treatment',
            'UC7': 'Transportation/Logistics',
            'UC8': 'Building Automation',
            'UC9': 'Food Manufacturing',
            'UC10': 'Mining Operations',
            'UC11': 'IoT Edge Computing',
            'UC12': 'Test & Measurement'
        }
        
        return {
            'type': 'binary_choice',
            'category': 'use_case_conflict',
            'question': 'Multiple use cases detected. Which best describes your application?',
            'option_a': {
                'use_case': uc_a[0],
                'name': uc_names.get(uc_a[0], uc_a[0]),
                'confidence': uc_a[1],
                'impact': 'System will be optimized for this application type'
            },
            'option_b': {
                'use_case': uc_b[0],
                'name': uc_names.get(uc_b[0], uc_b[0]),
                'confidence': uc_b[1],
                'impact': 'System will be optimized for this application type'
            },
            'resolution_required': True
        }