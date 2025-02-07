"""
This module defines the Logger class which logs events to daily JSON files.
Each log entry includes a timestamp (with minute precision), the client's IP, the command, and an optional error message.
"""

import os
import json
import datetime


class Logger:
    """
    Logger class for writing log entries to a JSON file.

    Each log file is named with the current date (DD,MM,YYYY.json) and stores a JSON array of log entries.
    """

    def __init__(self, log_dir="logs"):
        """
        Initializes the Logger instance.

        Args:
            log_dir (str): Directory where log files will be stored.
        """
        self.log_dir = log_dir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    def log(self, level, client_ip, command, error_message=None):
        """
        Writes a log entry to the daily log file.

        Args:
            level (str): The log level (e.g., "INFO", "ER").
            client_ip (str): The IP address of the client.
            command (str): The command string.
            error_message (str, optional): An optional error message.
        """
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
