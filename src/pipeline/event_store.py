import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class EventStore:
    """
    Immutable Event Store for Event Sourcing.
    Provides a tamper-evident audit trail for all domain events.
    """

    def __init__(self, ledger_path: Optional[Path] = None):
        self.ledger_path = ledger_path or Path("data/ledger/events.jsonl")
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event_type: str, data: Dict[str, Any], actor: str = "system"):
        """
        Append a new event to the ledger.
        """
        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "data": data,
            "actor": actor,
            "version": "1.0",
        }

        # Append to JSONL (JSON Lines) for efficient append and streaming read
        with open(self.ledger_path, "a") as f:
            f.write(json.dumps(event) + "\n")

        logger.debug("Appended event %s: %s", event_type, event["event_id"])

    def get_events(self, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve events from the ledger, optionally filtered by type.
        """
        if not self.ledger_path.exists():
            return []

        events = []
        with open(self.ledger_path, "r") as f:
            for line in f:
                event = json.loads(line)
                if event_type is None or event["event_type"] == event_type:
                    events.append(event)
        return events

    def replay(self, start_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Replay events to reconstruct state.
        """
        events = self.get_events()
        if start_date:
            events = [
                e
                for e in events
                if datetime.fromisoformat(e["timestamp"]) >= start_date
            ]
        return events
