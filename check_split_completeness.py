"""
Check if the agent files were split completely
"""

def count_lines(filepath):
    """Count lines in a file"""
    try:
        with open(filepath, 'r') as f:
            return len(f.readlines())
    except:
        return 0

# Count lines in each file
files = {
    'original': r'src\agents\phase1_agents.py',
    'requirements_elicitor': r'src\agents\requirements_elicitor.py',
    'specification_mapper': r'src\agents\specification_mapper.py', 
    'constraint_validator': r'src\agents\constraint_validator.py',
    'resolution_agent': r'src\agents\resolution_agent.py'
}

print("Line counts:")
total_split = 0
for name, path in files.items():
    lines = count_lines(path)
    print(f"  {name}: {lines} lines")
    if name != 'original':
        total_split += lines

print(f"\nOriginal file: {count_lines(files['original'])} lines")
print(f"Total in split files: {total_split} lines")

# Check each agent class
print("\nChecking agent classes in original file...")
with open(files['original'], 'r') as f:
    content = f.read()
    
classes = [
    'RequirementsElicitorAgent',
    'SpecificationMapperAgent', 
    'ConstraintValidatorAgent',
    'ResolutionAgent'
]

for cls in classes:
    if f'class {cls}' in content:
        # Find the line numbers
        lines = content.split('\n')
        start = None
        end = None
        for i, line in enumerate(lines, 1):
            if f'class {cls}' in line:
                start = i
            if start and i > start and line.startswith('class ') and not cls in line:
                end = i - 1
                break
        if start and not end:
            end = len(lines)
        
        print(f"  {cls}: lines {start}-{end} ({end-start+1} lines)")

print("\nChecking split files for completeness...")
for cls in classes:
    # Map class to file
    file_map = {
        'RequirementsElicitorAgent': 'requirements_elicitor',
        'SpecificationMapperAgent': 'specification_mapper',
        'ConstraintValidatorAgent': 'constraint_validator',
        'ResolutionAgent': 'resolution_agent'
    }
    
    filepath = files[file_map[cls]]
    with open(filepath, 'r') as f:
        if f'class {cls}' in f.read():
            print(f"  [OK] {cls} found in {file_map[cls]}.py")
        else:
            print(f"  [MISSING] {cls} NOT found in {file_map[cls]}.py")