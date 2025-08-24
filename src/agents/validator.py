import json
from typing import Dict, List, Optional
from pathlib import Path
from copy import deepcopy
from src.state.simple_state import SimpleState
from src.logging.decision_logger import DecisionLogger
from src.agents.validation_result import ValidationResult


class ConstraintValidator:
    """Agent responsible for validating requirements against constraints"""
    
    def __init__(self, logger: DecisionLogger):
        self.logger = logger
        self.constraints = self._load_constraints()
    
    def _load_constraints(self) -> Dict:
        """Load constraint rules from JSON file"""
        constraints_file = Path("data/constraints.json")
        if constraints_file.exists():
            try:
                with open(constraints_file, 'r', encoding='utf-8') as f:
                    full_data = json.load(f)
                    # Extract simplified constraints from complex structure
                    return self._simplify_constraints(full_data)
            except:
                # If parsing fails, use defaults
                return self._get_default_constraints()
        else:
            # Fallback to hardcoded constraints if file not found
            return self._get_default_constraints()
    
    def _simplify_constraints(self, full_data: Dict) -> Dict:
        """Extract simplified constraints from full constraint data"""
        # Extract basic limits from the complex structure
        return {
            "io_limits": {
                "max_digital_inputs": 256,
                "max_digital_outputs": 256,
                "max_analog_inputs": 64,
                "max_analog_outputs": 32,
                "max_total_io": 512
            },
            "temperature": {
                "min_celsius": -40,
                "max_celsius": 85,
                "outdoor_min": -40,
                "outdoor_max": 70,
                "indoor_min": 0,
                "indoor_max": 60
            },
            "power": {
                "available_voltages": ["24VDC", "120VAC", "240VAC", "48VDC"],
                "max_power_watts": 2000,
                "min_power_watts": 10
            },
            "communication": {
                "supported_protocols": ["Ethernet", "Modbus", "Profibus", "CANbus", "Serial", "EtherCAT"],
                "max_devices": 128,
                "max_data_rate_mbps": 1000
            },
            "incompatibilities": [
                {
                    "condition": "outdoor",
                    "incompatible_with": ["standard_ethernet"],
                    "message": "Outdoor installations require industrial-rated Ethernet"
                },
                {
                    "condition": "high_temperature",
                    "threshold": 60,
                    "incompatible_with": ["standard_components"],
                    "message": "High temperature requires special components"
                }
            ]
        }
    
    def _get_default_constraints(self) -> Dict:
        """Default validation rules if constraints.json not found"""
        return {
            "io_limits": {
                "max_digital_inputs": 256,
                "max_digital_outputs": 256,
                "max_analog_inputs": 64,
                "max_analog_outputs": 32,
                "max_total_io": 512
            },
            "temperature": {
                "min_celsius": -40,
                "max_celsius": 85,
                "outdoor_min": -40,
                "outdoor_max": 70,
                "indoor_min": 0,
                "indoor_max": 60
            },
            "power": {
                "available_voltages": ["24VDC", "120VAC", "240VAC", "48VDC"],
                "max_power_watts": 2000,
                "min_power_watts": 10
            },
            "communication": {
                "supported_protocols": ["Ethernet", "Modbus", "Profibus", "CANbus", "Serial", "EtherCAT"],
                "max_devices": 128,
                "max_data_rate_mbps": 1000
            },
            "incompatibilities": [
                {
                    "condition": "outdoor",
                    "incompatible_with": ["standard_ethernet"],
                    "message": "Outdoor installations require industrial-rated Ethernet"
                },
                {
                    "condition": "high_temperature",
                    "threshold": 60,
                    "incompatible_with": ["standard_components"],
                    "message": "High temperature requires special components"
                }
            ]
        }
    
    def validate(self, state: SimpleState) -> ValidationResult:
        """
        Validate requirements against constraints
        
        Returns:
            ValidationResult with validation details
        """
        result = ValidationResult(is_valid=True)
        reasoning = []
        
        # Extract requirement values
        req_values = self._extract_requirement_values(state)
        reasoning.append(f"Extracted {len(req_values)} requirement values")
        
        # Validate I/O constraints
        io_violations = self._validate_io(req_values)
        for violation in io_violations:
            result.add_violation(violation)
        
        # Validate temperature constraints
        temp_violations = self._validate_temperature(req_values)
        for violation in temp_violations:
            result.add_violation(violation)
        
        # Validate power constraints
        power_violations = self._validate_power(req_values)
        for violation in power_violations:
            result.add_violation(violation)
        
        # Validate communication constraints
        comm_violations = self._validate_communication(req_values)
        for violation in comm_violations:
            result.add_violation(violation)
        
        # Check incompatibilities
        incomp_warnings = self._check_incompatibilities(req_values)
        for warning in incomp_warnings:
            result.add_warning(warning)
        
        # Add suggestions based on validation
        suggestions = self._generate_suggestions(result.violations, result.warnings, req_values)
        for suggestion in suggestions:
            result.add_suggestion(suggestion)
        
        reasoning.append(f"Found {len(result.violations)} violations")
        reasoning.append(f"Found {len(result.warnings)} warnings")
        reasoning.append(f"Generated {len(result.suggestions)} suggestions")
        
        if result.is_valid:
            if result.warnings:
                decision = "valid_with_warnings"
                reasoning.append("Requirements valid but has warnings")
            else:
                decision = "fully_valid"
                reasoning.append("All requirements valid")
        else:
            decision = "invalid_requirements"
            reasoning.append("Requirements have constraint violations")
        
        # Log decision
        self.logger.log_decision(
            agent_name="validator",
            input_received=f"State with {len(state.requirements)} requirements",
            reasoning_steps=reasoning,
            decision_made=decision,
            output_produced=f"Valid: {result.is_valid}, Violations: {len(result.violations)}, Warnings: {len(result.warnings)}"
        )
        
        # Update state decision log
        state.add_decision(
            agent="validator",
            decision=decision,
            reasoning=reasoning
        )
        
        return result
    
    def _extract_requirement_values(self, state: SimpleState) -> Dict:
        """Extract and parse requirement values from state"""
        values = {
            "digital_inputs": 0,
            "digital_outputs": 0,
            "analog_inputs": 0,
            "analog_outputs": 0,
            "temperature_min": None,
            "temperature_max": None,
            "indoor_outdoor": None,
            "power_voltage": None,
            "power_watts": None,
            "protocols": [],
            "device_count": 0
        }
        
        for req in state.requirements:
            if not req.answer:
                continue
                
            answer_lower = req.answer.lower()
            
            # Parse I/O values
            if "digital input" in req.question.lower():
                values["digital_inputs"] = self._parse_number(req.answer)
            elif "digital output" in req.question.lower():
                values["digital_outputs"] = self._parse_number(req.answer)
            elif "analog input" in req.question.lower():
                values["analog_inputs"] = self._parse_number(req.answer)
            elif "analog output" in req.question.lower():
                values["analog_outputs"] = self._parse_number(req.answer)
            
            # Parse temperature
            elif "temperature" in req.question.lower():
                temp_range = self._parse_temperature_range(req.answer)
                if temp_range:
                    values["temperature_min"] = temp_range[0]
                    values["temperature_max"] = temp_range[1]
            
            # Parse indoor/outdoor
            elif "indoor or outdoor" in req.question.lower():
                values["indoor_outdoor"] = "outdoor" if "outdoor" in answer_lower else "indoor"
            
            # Parse power
            elif "power supply voltage" in req.question.lower():
                values["power_voltage"] = req.answer.upper()
            elif "power budget" in req.question.lower():
                values["power_watts"] = self._parse_number(req.answer)
            
            # Parse communication
            elif "communication protocol" in req.question.lower():
                values["protocols"] = self._parse_protocols(req.answer)
            elif "devices will communicate" in req.question.lower():
                values["device_count"] = self._parse_number(req.answer)
        
        return values
    
    def _parse_number(self, text: str) -> int:
        """Extract number from text"""
        import re
        numbers = re.findall(r'\d+', text)
        return int(numbers[0]) if numbers else 0
    
    def _parse_temperature_range(self, text: str) -> Optional[tuple]:
        """Parse temperature range from text"""
        import re
        # Look for patterns like "-10 to 50" or "-10C to 50C" or "From -10C to 50C"
        pattern = r'(-?\d+)\s*[CcFf]?\s*(?:to|[-–])\s*(-?\d+)'
        match = re.search(pattern, text)
        if match:
            return (int(match.group(1)), int(match.group(2)))
        return None
    
    def _parse_protocols(self, text: str) -> List[str]:
        """Extract protocol names from text"""
        protocols = []
        text_lower = text.lower()
        
        known_protocols = ["ethernet", "modbus", "profibus", "canbus", "serial", "ethercat"]
        for protocol in known_protocols:
            if protocol in text_lower:
                protocols.append(protocol.capitalize())
        
        return protocols
    
    def _validate_io(self, values: Dict) -> List[str]:
        """Validate I/O constraints"""
        violations = []
        limits = self.constraints.get("io_limits", {})
        
        if values["digital_inputs"] > limits.get("max_digital_inputs", 256):
            violations.append(f"Digital inputs ({values['digital_inputs']}) exceed maximum ({limits['max_digital_inputs']})")
        
        if values["digital_outputs"] > limits.get("max_digital_outputs", 256):
            violations.append(f"Digital outputs ({values['digital_outputs']}) exceed maximum ({limits['max_digital_outputs']})")
        
        total_io = (values["digital_inputs"] + values["digital_outputs"] + 
                   values["analog_inputs"] + values["analog_outputs"])
        if total_io > limits.get("max_total_io", 512):
            violations.append(f"Total I/O count ({total_io}) exceeds maximum ({limits['max_total_io']})")
        
        return violations
    
    def _validate_temperature(self, values: Dict) -> List[str]:
        """Validate temperature constraints"""
        violations = []
        temp_limits = self.constraints.get("temperature", {})
        
        if values["temperature_min"] is not None and values["temperature_max"] is not None:
            # Check absolute limits
            if values["temperature_min"] < temp_limits.get("min_celsius", -40):
                violations.append(f"Minimum temperature ({values['temperature_min']}°C) below limit ({temp_limits['min_celsius']}°C)")
            
            if values["temperature_max"] > temp_limits.get("max_celsius", 85):
                violations.append(f"Maximum temperature ({values['temperature_max']}°C) exceeds limit ({temp_limits['max_celsius']}°C)")
            
            # Check indoor/outdoor specific limits
            if values["indoor_outdoor"] == "outdoor":
                if values["temperature_max"] > temp_limits.get("outdoor_max", 70):
                    violations.append(f"Outdoor temperature ({values['temperature_max']}°C) exceeds outdoor limit ({temp_limits['outdoor_max']}°C)")
        
        return violations
    
    def _validate_power(self, values: Dict) -> List[str]:
        """Validate power constraints"""
        violations = []
        power_limits = self.constraints.get("power", {})
        
        # Check voltage
        if values["power_voltage"]:
            available = power_limits.get("available_voltages", [])
            if values["power_voltage"] not in available:
                violations.append(f"Voltage {values['power_voltage']} not in available options: {', '.join(available)}")
        
        # Check power budget
        if values["power_watts"]:
            if values["power_watts"] > power_limits.get("max_power_watts", 2000):
                violations.append(f"Power budget ({values['power_watts']}W) exceeds maximum ({power_limits['max_power_watts']}W)")
        
        return violations
    
    def _validate_communication(self, values: Dict) -> List[str]:
        """Validate communication constraints"""
        violations = []
        comm_limits = self.constraints.get("communication", {})
        
        # Check protocols
        if values["protocols"]:
            supported = comm_limits.get("supported_protocols", [])
            for protocol in values["protocols"]:
                if protocol not in supported:
                    violations.append(f"Protocol {protocol} not supported. Available: {', '.join(supported)}")
        
        # Check device count
        if values["device_count"] > comm_limits.get("max_devices", 128):
            violations.append(f"Device count ({values['device_count']}) exceeds maximum ({comm_limits['max_devices']})")
        
        return violations
    
    def _check_incompatibilities(self, values: Dict) -> List[str]:
        """Check for incompatible combinations"""
        warnings = []
        incompatibilities = self.constraints.get("incompatibilities", [])
        
        for rule in incompatibilities:
            # Check if condition is met
            condition_met = False
            
            if rule["condition"] == "outdoor" and values["indoor_outdoor"] == "outdoor":
                condition_met = True
            elif rule["condition"] == "high_temperature":
                if values["temperature_max"] and values["temperature_max"] > rule.get("threshold", 60):
                    condition_met = True
            
            if condition_met:
                warnings.append(rule["message"])
        
        return warnings
    
    def _generate_suggestions(self, violations: List[str], warnings: List[str], values: Dict) -> List[str]:
        """Generate suggestions based on validation results"""
        suggestions = []
        
        # Suggestions for violations
        for violation in violations:
            if "I/O" in violation or "input" in violation.lower() or "output" in violation.lower():
                suggestions.append("Consider using distributed I/O or multiple controllers")
            elif "temperature" in violation.lower():
                suggestions.append("Consider temperature-hardened components or environmental controls")
            elif "voltage" in violation.lower():
                suggestions.append("Use a power converter or verify available power supplies")
            elif "power budget" in violation.lower():
                suggestions.append("Consider using multiple power supplies or reducing power requirements")
        
        # Suggestions for warnings
        for warning in warnings:
            if "outdoor" in warning.lower():
                suggestions.append("Use IP67-rated enclosures and industrial Ethernet switches")
            elif "temperature" in warning.lower():
                suggestions.append("Specify conformal coating and extended temperature range components")
        
        # General suggestions
        if values.get("device_count", 0) > 50:
            suggestions.append("Consider using a managed switch for large device networks")
        
        # Remove duplicates
        return list(set(suggestions))
    
    def validate_io_limits(self, state: SimpleState) -> List[str]:
        """Check if total I/O points exceed hardware limits"""
        req_values = self._extract_requirement_values(state)
        return self._validate_io(req_values)
    
    def validate_power_requirements(self, state: SimpleState) -> List[str]:
        """Check if power requirements are feasible"""
        req_values = self._extract_requirement_values(state)
        return self._validate_power(req_values)
    
    def validate_environmental_compatibility(self, state: SimpleState) -> List[str]:
        """Check if environment matches hardware specs"""
        req_values = self._extract_requirement_values(state)
        return self._validate_temperature(req_values)