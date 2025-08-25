"""
Verify all methods from original are in split files
"""

import re

# Read original file
with open(r'src\agents\phase1_agents.py', 'r') as f:
    original = f.read()

# Find all methods in each class
def find_methods(content, class_name):
    """Find all methods in a class"""
    methods = []
    in_class = False
    for line in content.split('\n'):
        if f'class {class_name}' in line:
            in_class = True
        elif in_class and line.startswith('class '):
            break
        elif in_class and re.match(r'    def \w+', line):
            method = re.search(r'def (\w+)', line)
            if method:
                methods.append(method.group(1))
    return methods

# Map classes to files
class_file_map = {
    'RequirementsElicitorAgent': r'src\agents\requirements_elicitor.py',
    'SpecificationMapperAgent': r'src\agents\specification_mapper.py',
    'ConstraintValidatorAgent': r'src\agents\constraint_validator.py',
    'ResolutionAgent': r'src\agents\resolution_agent.py'
}

print("Verifying methods in each class:\n")

all_good = True
for class_name, filepath in class_file_map.items():
    print(f"{class_name}:")
    
    # Get methods from original
    original_methods = find_methods(original, class_name)
    print(f"  Original methods: {original_methods}")
    
    # Get methods from split file
    with open(filepath, 'r') as f:
        split_content = f.read()
    split_methods = find_methods(split_content, class_name)
    print(f"  Split file methods: {split_methods}")
    
    # Compare
    missing = set(original_methods) - set(split_methods)
    extra = set(split_methods) - set(original_methods)
    
    if missing:
        print(f"  [MISSING] Methods not in split file: {missing}")
        all_good = False
    if extra:
        print(f"  [EXTRA] Extra methods in split file: {extra}")
    
    if not missing and not extra:
        print(f"  [OK] All methods present")
    print()

if all_good:
    print("SUCCESS: All methods are properly split!")
else:
    print("WARNING: Some methods may be missing!")