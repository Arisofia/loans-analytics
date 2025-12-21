import json
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping

_SAFE_NAME = re.compile(r"[^A-Za-z0-9_.-]+")


def _safe_filename(agent_name: str, version: str) -> str:
    """Return a sanitized filename to avoid path traversal or shell injection.

    Bandit flagged our previous implementation for using user-provided strings
    directly in file paths. This helper limits the character set to predictable
    values so the resulting file always stays within ``storage_dir``.
    """

    safe_agent = _SAFE_NAME.sub("_", agent_name or "agent")
    safe_version = _SAFE_NAME.sub("_", version or "latest")
    return f"{safe_agent}_v{safe_version}.json"


def save_agent_output(
    agent_name: str,
    output: Mapping[str, object],
    version: str | None = None,
    storage_dir: str | Path = "data/agent_outputs",
) -> Path:
    storage_path = Path(storage_dir)
    storage_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    resolved_version = version or timestamp
    filename = _safe_filename(agent_name, resolved_version)
    path = storage_path / filename

    # Use atomic write pattern to avoid partially written files if the process
    # is interrupted mid-write.
    tmp_path = path.with_suffix(".json.tmp")
    payload = {
        "agent": agent_name,
        "version": resolved_version,
        "output": output,
        "timestamp": timestamp,
    }

    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(path)
    return path


def list_agent_outputs(agent_name: str, storage_dir: str | Path = "data/agent_outputs") -> Iterable[str]:
    storage_path = Path(storage_dir)
    safe_agent_prefix = _SAFE_NAME.sub("_", agent_name or "agent")
    return [f.name for f in storage_path.glob(f"{safe_agent_prefix}_v*.json") if f.is_file()]
