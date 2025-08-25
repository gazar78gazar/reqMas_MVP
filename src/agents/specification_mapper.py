"""
Specification Mapper Agent
Maps user requirements to use cases and specifications
Uses deterministic mapping from useCase.json
"""

from typing import Dict, List

# Import from the correct location
from src.state.crdt_state_manager import StateSnapshot, ConstraintStrength


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