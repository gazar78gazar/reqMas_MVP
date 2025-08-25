"""
Phase 1 Production Agents
Clean implementation of the 4 core agents for reqMAS MVP
"""

import re
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# These would be imported from src.state in production
from crdt_state_manager import StateSnapshot, ConstraintStrength


class RequirementsElicitorAgent:
    """
    Extracts technical requirements from natural language input
    Maps to constraint IDs based on patterns and keywords
    """
    
    def __init__(self, use_case_config: Dict):
        self.use_case_config = use_case_config
        
        # Pattern mappings for requirement extraction
        self.io_patterns = {
            r'(\d+)\s*digital\s*input': self._extract_digital_inputs,
            r'(\d+)\s*digital\s*output': self._extract_digital_outputs,
            r'(\d+)\s*analog\s*input': self._extract_analog_inputs,
            r'(\d+)\s*analog\s*output': self._extract_analog_outputs,
        }
        
        self.env_patterns = {
            r'outdoor': ['CNST_IP54', 'CNST_TEMP_EXTENDED'],
            r'indoor': [],
            r'harsh\s*environment': ['CNST_IP54', 'CNST_TEMP_EXTENDED', 'CNST_VIBRATION_2G'],
            r'hygienic|food.?grade|washdown': ['CNST_IP69K'],
            r'hazardous|atex|explosion': ['CNST_ATEX_CERTIFIED', 'CNST_CLASS1_DIV2', 'CNST_FANLESS'],
            r'extreme\s*temperature': ['CNST_TEMP_EXTENDED'],
            r'vibration|shock|mobile': ['CNST_VIBRATION_2G', 'CNST_COMPACT_FORM'],
        }
        
        self.power_patterns = {
            r'solar|battery|off.?grid': ['CNST_POWER_MAX_10W', 'CNST_FANLESS'],
            r'low\s*power|energy\s*efficient': ['CNST_POWER_MAX_20W'],
            r'24\s*VDC|24V\s*DC': ['CNST_POWER_24VDC'],
            r'redundant\s*power': ['CNST_REDUNDANT_POWER'],
        }
        
        self.comm_patterns = {
            r'ethernet': ['CNST_GIGABIT_ETHERNET'],
            r'modbus': ['CNST_MODBUS_TCP'],
            r'profinet': ['CNST_PROFINET'],
            r'ethercat': ['CNST_ETHERCAT'],
            r'opc.?ua': ['CNST_OPCUA'],
            r'mqtt': ['CNST_MQTT'],
            r'wifi|wireless': ['CNST_WIFI'],
            r'lte|4g|cellular': ['CNST_LTE'],
            r'5g': ['CNST_5G'],
        }
        
        self.performance_patterns = {
            r'real.?time|deterministic': ['CNST_LATENCY_MAX_1MS', 'CNST_TSN_SUPPORT'],
            r'(\d+)\s*ms\s*latency': self._extract_latency,
            r'high.?speed|fast': ['CNST_PROCESSOR_MIN_I5'],
            r'ai|machine\s*learning|vision': ['CNST_GPU_REQUIRED', 'CNST_PROCESSOR_MIN_I5'],
            r'motion\s*control': ['CNST_LATENCY_MAX_1MS', 'CNST_TSN_SUPPORT'],
        }
    
    async def process_async(self, user_input: str, snapshot: StateSnapshot, context: Dict) -> Dict:
        """
        Extract requirements from user input
        Returns state updates with constraints and use case signals
        """
        user_input_lower = user_input.lower()
        
        state_updates = {
            'use_cases': {},
            'constraints': []
        }
        
        # Extract I/O requirements
        for pattern, handler in self.io_patterns.items():
            match = re.search(pattern, user_input_lower)
            if match:
                constraints = handler(match)
                if constraints:
                    state_updates['constraints'].extend(constraints)
        
        # Extract environmental requirements
        for pattern, constraint_ids in self.env_patterns.items():
            if re.search(pattern, user_input_lower):
                for constraint_id in constraint_ids:
                    state_updates['constraints'].append({
                        'id': constraint_id,
                        'strength': 10,  # Mandatory for environmental
                        'confidence': 0.9
                    })
        
        # Extract power requirements
        for pattern, constraint_ids in self.power_patterns.items():
            if re.search(pattern, user_input_lower):
                for constraint_id in constraint_ids:
                    state_updates['constraints'].append({
                        'id': constraint_id,
                        'strength': 10,
                        'confidence': 0.85
                    })
        
        # Extract communication requirements
        for pattern, constraint_ids in self.comm_patterns.items():
            if re.search(pattern, user_input_lower):
                for constraint_id in constraint_ids:
                    state_updates['constraints'].append({
                        'id': constraint_id,
                        'strength': 10 if 'modbus' in pattern else 4,  # Modbus mandatory, others recommended
                        'confidence': 0.95
                    })
        
        # Extract performance requirements
        for pattern, handler in self.performance_patterns.items():
            if callable(handler):
                match = re.search(pattern, user_input_lower)
                if match:
                    constraints = handler(match)
                    if constraints:
                        state_updates['constraints'].extend(constraints)
            else:
                if re.search(pattern, user_input_lower):
                    for constraint_id in handler:
                        state_updates['constraints'].append({
                            'id': constraint_id,
                            'strength': 10,
                            'confidence': 0.9
                        })
        
        # Deduplicate constraints
        seen = set()
        unique_constraints = []
        for constraint in state_updates['constraints']:
            if constraint['id'] not in seen:
                seen.add(constraint['id'])
                unique_constraints.append(constraint)
        
        state_updates['constraints'] = unique_constraints
        
        return {'state_updates': state_updates}
    
    def _extract_digital_inputs(self, match) -> List[Dict]:
        """Extract digital input requirements"""
        count = int(match.group(1))
        if count > 64:
            return [{'id': 'CNST_DIGITAL_IO_MIN_64', 'value': count, 'strength': 10, 'confidence': 0.95}]
        elif count > 32:
            return [{'id': 'CNST_DIGITAL_IO_MIN_32', 'value': count, 'strength': 10, 'confidence': 0.95}]
        elif count > 16:
            return [{'id': 'CNST_DIGITAL_IO_MIN_16', 'value': count, 'strength': 10, 'confidence': 0.95}]
        return []
    
    def _extract_digital_outputs(self, match) -> List[Dict]:
        """Extract digital output requirements"""
        count = int(match.group(1))
        if count > 64:
            return [{'id': 'CNST_DIGITAL_IO_MIN_64', 'value': count, 'strength': 10, 'confidence': 0.95}]
        elif count > 32:
            return [{'id': 'CNST_DIGITAL_IO_MIN_32', 'value': count, 'strength': 10, 'confidence': 0.95}]
        return []
    
    def _extract_analog_inputs(self, match) -> List[Dict]:
        """Extract analog input requirements"""
        count = int(match.group(1))
        if count > 24:
            return [{'id': 'CNST_ANALOG_IO_MIN_24', 'value': count, 'strength': 10, 'confidence': 0.95}]
        elif count > 16:
            return [{'id': 'CNST_ANALOG_IO_MIN_16', 'value': count, 'strength': 10, 'confidence': 0.95}]
        elif count > 8:
            return [{'id': 'CNST_ANALOG_IO_MIN_8', 'value': count, 'strength': 10, 'confidence': 0.95}]
        return []
    
    def _extract_analog_outputs(self, match) -> List[Dict]:
        """Extract analog output requirements"""
        count = int(match.group(1))
        if count > 8:
            return [{'id': 'CNST_ANALOG_IO_MIN_8', 'value': count, 'strength': 10, 'confidence': 0.95}]
        return []
    
    def _extract_latency(self, match) -> List[Dict]:
        """Extract latency requirements"""
        latency_ms = int(match.group(1))
        if latency_ms <= 1:
            return [{'id': 'CNST_LATENCY_MAX_1MS', 'value': latency_ms, 'strength': 10, 'confidence': 0.9}]
        elif latency_ms <= 10:
            return [{'id': 'CNST_LATENCY_MAX_10MS', 'value': latency_ms, 'strength': 10, 'confidence': 0.9}]
        return []


class SpecificationMapperAgent:
    """
    Maps user requirements to use cases and specifications
    Uses deterministic mapping from useCase.json
    """
    
    def __init__(self, use_case_config: Dict):
        self.use_case_config = use_case_config
        self.use_cases = use_case_config.get('use_cases', {})
        self.common_requirements = use_case_config.get('common_sub_requirements', {})
        
        # Use case keyword mappings
        self.uc_keywords = {
            'UC1': ['substation', 'power grid', 'electrical', 'transformer'],
            'UC2': ['solar', 'pv', 'photovoltaic', 'renewable'],
            'UC3': ['motion', 'servo', 'axis', 'robot', 'trajectory'],
            'UC4': ['quality', 'inspection', 'vision', 'defect'],
            'UC5': ['industrial', 'machinery', 'opc', 'factory'],
            'UC6': ['water', 'treatment', 'ph', 'flow', 'pump'],
            'UC7': ['transport', 'logistics', 'vehicle', 'tracking'],
            'UC8': ['building', 'hvac', 'automation', 'temperature control'],
            'UC9': ['food', 'beverage', 'hygiene', 'batch'],
            'UC10': ['mining', 'mineral', 'extraction', 'hazardous'],
            'UC11': ['iot', 'edge', 'cloud', 'analytics'],
            'UC12': ['test', 'measurement', 'data acquisition', 'instrument']
        }
    
    async def process_async(self, user_input: str, snapshot: StateSnapshot, context: Dict) -> Dict:
        """
        Map input to use cases and derive specifications
        """
        user_input_lower = user_input.lower()
        
        state_updates = {
            'use_cases': {},
            'constraints': []
        }
        
        # Detect use cases based on keywords
        for uc_id, keywords in self.uc_keywords.items():
            score = sum(1 for kw in keywords if kw in user_input_lower)
            if score > 0:
                # Normalize score (max 1.0)
                confidence = min(score * 0.3, 1.0)
                state_updates['use_cases'][uc_id] = confidence
        
        # If strong use case match, add CSR constraints
        if state_updates['use_cases']:
            top_uc = max(state_updates['use_cases'].items(), key=lambda x: x[1])
            if top_uc[1] > 0.6:  # Strong match
                # Add constraints from CSRs associated with this use case
                constraints = self._get_uc_constraints(top_uc[0])
                state_updates['constraints'].extend(constraints)
        
        # Map specific requirements to CSRs
        if 'real time' in user_input_lower or 'deterministic' in user_input_lower:
            if 'CSR_REAL_TIME_1MS' in self.common_requirements:
                csr = self.common_requirements['CSR_REAL_TIME_1MS']
                for constraint in csr.get('implied_constraints', []):
                    state_updates['constraints'].append({
                        'id': constraint['constraint_id'],
                        'strength': constraint['strength_score'],
                        'confidence': 0.85
                    })
        
        if 'ai' in user_input_lower or 'vision' in user_input_lower:
            if 'CSR_AI_PROCESSING' in self.common_requirements:
                csr = self.common_requirements['CSR_AI_PROCESSING']
                for constraint in csr.get('implied_constraints', []):
                    state_updates['constraints'].append({
                        'id': constraint['constraint_id'],
                        'strength': constraint['strength_score'],
                        'confidence': 0.9
                    })
        
        return {'state_updates': state_updates}
    
    def _get_uc_constraints(self, uc_id: str) -> List[Dict]:
        """Get constraints associated with a use case"""
        constraints = []
        
        # Map UC to common constraints based on domain
        uc_constraint_map = {
            'UC1': ['CNST_IEC61850', 'CNST_REDUNDANT_POWER'],
            'UC2': ['CNST_POWER_MAX_10W', 'CNST_LTE', 'CNST_FANLESS'],
            'UC3': ['CNST_LATENCY_MAX_1MS', 'CNST_TSN_SUPPORT', 'CNST_ETHERCAT'],
            'UC4': ['CNST_GIGABIT_ETHERNET', 'CNST_GPU_REQUIRED'],
            'UC5': ['CNST_MODBUS_TCP', 'CNST_OPCUA'],
            'UC6': ['CNST_ANALOG_IO_MIN_8', 'CNST_MODBUS_TCP'],
            'UC7': ['CNST_LTE', 'CNST_GPS', 'CNST_VIBRATION_2G'],
            'UC8': ['CNST_MODBUS_TCP', 'CNST_BACNET'],
            'UC9': ['CNST_IP69K', 'CNST_STORAGE_256GB'],
            'UC10': ['CNST_ATEX_CERTIFIED', 'CNST_FANLESS', 'CNST_TEMP_EXTENDED'],
            'UC11': ['CNST_MQTT', 'CNST_OPCUA', 'CNST_PROCESSOR_MIN_I5'],
            'UC12': ['CNST_SAMPLING_RATE_100KHZ', 'CNST_ADC_RESOLUTION_16BIT']
        }
        
        if uc_id in uc_constraint_map:
            for constraint_id in uc_constraint_map[uc_id]:
                constraints.append({
                    'id': constraint_id,
                    'strength': 10,  # UC-derived constraints are mandatory
                    'confidence': 0.8
                })
        
        return constraints


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
