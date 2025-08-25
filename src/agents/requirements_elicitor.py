"""
Requirements Elicitor Agent
Extracts technical requirements from natural language input
Maps to constraint IDs based on patterns and keywords
"""

import re
from typing import Dict, List, Any

# Import from the correct location
from src.state.crdt_state_manager import StateSnapshot, ConstraintStrength


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