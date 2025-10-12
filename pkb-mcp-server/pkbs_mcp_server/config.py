from pydantic import BaseModel, Field
from typing import Optional
import json
import os
from pathlib import Path


class ServerConfig(BaseModel):
    database_path: str = "pkb.db"
    server_host: str = "127.0.0.1"
    server_port: int = 8080
    max_notes_per_search: int = 50
    auto_backup: bool = True
    backup_interval_minutes: int = 60

    @classmethod
    def from_file(cls, config_path: str = "config.json") -> "ServerConfig":
        """Load configuration from a JSON file."""
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config_data = json.load(f)
            return cls(**config_data)
        else:
            # Return default configuration if file doesn't exist
            return cls()

    def save_to_file(self, config_path: str = "config.json"):
        """Save configuration to a JSON file."""
        with open(config_path, "w") as f:
            json.dump(self.model_dump(), f, indent=2)