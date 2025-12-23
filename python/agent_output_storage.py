import json
import os
from datetime import datetime, timezone


def save_agent_output(agent_name, output, version=None, storage_dir="data/agent_outputs"):
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


def list_agent_outputs(agent_name, storage_dir="data/agent_outputs"):
    files = [f for f in os.listdir(storage_dir) if f.startswith(agent_name)]
    return files
