import os
import json
import datetime

class Logger:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    def log(self, level, client_ip, command, error_message=None):
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%dT%H:%M")
        date_str = now.strftime("%d,%m,%Y")
        log_file = os.path.join(self.log_dir, f"{date_str}.json")
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "client_ip": client_ip,
            "command": command,
        }
        if error_message:
            log_entry["error"] = error_message

        # Load existing logs as a JSON array, or create an empty array.
        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    logs = json.load(f)
                    if not isinstance(logs, list):
                        logs = []
            except Exception:
                logs = []
        else:
            logs = []

        logs.append(log_entry)
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2)
