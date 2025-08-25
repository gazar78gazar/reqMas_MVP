# Run this Python script from reqMAS_MVP folder
import os
from pathlib import Path

# Create directories
Path("phase2/probabilistic").mkdir(parents=True, exist_ok=True)
Path("phase2/resolution").mkdir(parents=True, exist_ok=True)

# Create __init__.py files
Path("phase2/__init__.py").touch()
Path("phase2/probabilistic/__init__.py").touch()
Path("phase2/resolution/__init__.py").touch()

print("✓ Created all directories and __init__.py files")