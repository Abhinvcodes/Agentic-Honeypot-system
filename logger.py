import os
import json
from datetime import datetime, timezone

class HoneypotLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        # Ensure the logs directory exists right when the application starts
        os.makedirs(self.log_dir, exist_ok=True)

    async def log_event(self, session_id: str, event_type: str, data: dict):
        """
        Asynchronously appends a single event structured as a JSON Line 
        to the session's isolated file tracking using timezone-aware UTC.
        """
        file_path = os.path.join(self.log_dir, f"{session_id}.jsonl")
        
        # Structure the baseline audit frame with timezone-aware datetime
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            **data  # Unpacks custom dictionary fields cleanly into the entry object
        }
        
        # 'a' mode handles high-velocity tracking beautifully because the operating
        # system just appends bytes to the file end without reading previous contents.
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")