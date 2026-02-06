"""Usage metrics tracking and export utility."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from pydantic import BaseModel, Field

from python.logging_config import get_logger

logger = get_logger(__name__)


class UsageEvent(BaseModel):
    """Model for a single usage event."""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: Optional[str] = None
    feature_name: str
    action: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for export."""
        data = self.model_dump()
        # Convert datetime to ISO string
        data["timestamp"] = self.timestamp.isoformat()
        return data


class UsageTracker:
    """Track and export usage metrics."""

    def __init__(self, storage_path: Optional[Union[str, Path]] = None):
        """
        Initialize usage tracker.

        Args:
            storage_path: Path to JSONL file for persistent storage.
                         Defaults to data/usage_metrics/usage_events.jsonl
        """
        if storage_path is None:
            # Default to data/usage_metrics/usage_events.jsonl relative to project root
            repo_root = Path(__file__).parent.parent.parent
            self.storage_path = repo_root / "data" / "usage_metrics" / "usage_events.jsonl"
        else:
            self.storage_path = Path(storage_path)

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.events: List[UsageEvent] = []
        self._load_events()

    def track(
        self,
        feature_name: str,
        action: str,
        user_id: Optional[str] = None,
        **metadata: Any,
    ) -> UsageEvent:
        """
        Track a usage event.

        Args:
            feature_name: Name of the feature being used
            action: Action performed (e.g., 'view', 'run', 'export')
            user_id: Optional user identifier
            metadata: Additional context for the event

        Returns:
            The created UsageEvent
        """
        event = UsageEvent(
            feature_name=feature_name,
            action=action,
            user_id=user_id,
            metadata=metadata,
        )
        self.events.append(event)
        self._persist_event(event)
        
        logger.info(
            f"Usage tracked: {feature_name}:{action}",
            extra={"feature": feature_name, "action": action, "user_id": user_id}
        )
        return event

    def get_events(self) -> List[UsageEvent]:
        """Get all tracked events."""
        return self.events

    def export(self, output_path: Union[str, Path], format: str = "json") -> Path:
        """
        Export events to a file.

        Args:
            output_path: Path to save the exported file
            format: Export format ('json', 'csv', 'parquet')

        Returns:
            Path to the exported file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.events:
            logger.warning("No events to export")
            # Create an empty file or just return
            if format == "json":
                output_path.write_text("[]")
            elif format == "csv":
                pd.DataFrame().to_csv(output_path, index=False)
            return output_path

        data = [event.to_dict() for event in self.events]
        df = pd.DataFrame(data)

        # Handle metadata for CSV/Parquet as they don't like nested dicts/empty structs
        if format in ["csv", "parquet"]:
            df["metadata"] = df["metadata"].apply(json.dumps)

        if format == "json":
            output_path.write_text(json.dumps(data, indent=2))
        elif format == "csv":
            df.to_csv(output_path, index=False)
        elif format == "parquet":
            df.to_parquet(output_path, index=False)
        else:
            raise ValueError(f"Unsupported export format: {format}")

        logger.info(f"Exported {len(self.events)} events to {output_path} ({format})")
        return output_path

    def _persist_event(self, event: UsageEvent) -> None:
        """Append a single event to the storage file."""
        try:
            with open(self.storage_path, "a") as f:
                f.write(event.model_dump_json() + "\n")
        except Exception as e:
            logger.error(f"Failed to persist usage event: {e}")

    def _load_events(self) -> None:
        """Load events from the storage file."""
        if not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, "r") as f:
                for line in f:
                    if line.strip():
                        try:
                            self.events.append(UsageEvent.model_validate_json(line))
                        except Exception as e:
                            logger.warning(f"Failed to parse usage event line: {e}")
        except Exception as e:
            logger.error(f"Failed to load usage events: {e}")
