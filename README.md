# reqMas_MVP - Requirements Management System (Minimal Viable Product)

## Overview
Simplified version of the requirements management multi-agent system, focusing on core functionality without complexity.

## Project Structure
```
reqMas_MVP/
├── src/
│   ├── agents/        # Simplified agent implementations
│   ├── state/         # Flat state management
│   ├── logging/       # Enhanced decision logging
│   └── utils/         # Utility functions
├── data/              # JSON specifications
├── tests/             # Test suite
├── logs/              # Action and decision logs
└── docs/              # Documentation
```

## Key Features
- Sequential agent orchestration
- Flat state management
- Enhanced logging and observability
- Iteration limits (max 3)
- Simplified validation

## Installation
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## Running Tests
```bash
python -m pytest tests/ -v
```

## Differences from Original
See `docs/differences_from_original.md` for detailed comparison.

## Development Status
- [x] Project structure created
- [x] Data files migrated
- [x] Logging framework setup
- [ ] Agent implementations
- [ ] State management
- [ ] Test suite
- [ ] Integration testing