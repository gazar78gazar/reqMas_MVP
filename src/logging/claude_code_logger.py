import json
import datetime
from pathlib import Path

class ClaudeCodeLogger:
    def __init__(self):
        self.log_file = Path("logs/claude_code_actions.log")
        self.log_file.parent.mkdir(exist_ok=True)
        
        # Log MVP session start
        self.log_action("session_start", {
            "project": "reqMas_MVP",
            "original_project": "C:\\dev\\reqMas",
            "approach": "simplified_sequential"
        })
        
    def log_action(self, action_type, details, status="started"):
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "project": "reqMas_MVP",  # Always mark as MVP
            "action": action_type,
            "details": details,
            "status": status
        }
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
    
    def log_migration(self, file_copied, from_path, to_path):
        """Special logging for files copied from original"""
        self.log_action("migration", {
            "file": file_copied,
            "from": from_path,
            "to": to_path,
            "type": "reuse"
        })