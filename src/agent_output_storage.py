import json
import os
from datetime import datetime, timezone
from typing import Any, List, Optional


def save_agent_output(
    agent_name: str,
    output: Any,
    version: Optional[str] = None,
    storage_dir: str = "data/agent_outputs",
) -> str:
    os.makedirs(storage_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    version = version or timestamp
    filename = f"{agent_name}_v{version}.json"
    path = os.path.join(storage_dir, filename)
    with open(path, "w") as f:
        json.dump(
            {"agent": agent_name, "version": version, "output": output, "timestamp": timestamp}, f
        )
    return path


def list_agent_outputs(agent_name: str, storage_dir: str = "data/agent_outputs") -> List[str]:
    # If the directory does not exist, return an empty list instead of raising
    # FileNotFoundError. This mirrors the behavior of `save_agent_output` which
    # creates the directory when saving.
    if not os.path.exists(storage_dir):
        return []
    files = [f for f in os.listdir(storage_dir) if f.startswith(agent_name)]
    return files
