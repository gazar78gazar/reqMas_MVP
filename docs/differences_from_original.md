# Differences from Original reqMAS

## What We Kept
- Data files (all JSON specifications)
- ProductLookup.js logic (if needed)
- Domain knowledge about requirements

## What We Simplified
- Orchestration: Sequential instead of parallel
- State: Flat structure instead of blackboard
- Agents: 3-4 instead of 6+
- Validation: Single validator instead of multiple
- No confidence scoring (initially)
- No user assessment (initially)
- No disambiguation loops (initially)

## What We Added
- Comprehensive decision logging
- Test-first development
- Observable state at every step
- Iteration limits (max 3)