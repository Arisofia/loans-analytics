from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast
import pandas as pd
from pydantic import BaseModel, Field
from backend.python.logging_config import get_logger
logger = get_logger(__name__)

class UsageEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: Optional[str] = None
    feature_name: str
    action: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = self.model_dump()
        timestamp = cast(datetime, self.timestamp)
        data['timestamp'] = timestamp.isoformat()
        return data

class UsageTracker:

    def __init__(self, storage_path: Optional[Union[str, Path]]=None):
        if storage_path is None:
            repo_root = Path(__file__).parent.parent.parent
            self.storage_path = repo_root / 'data' / 'usage_metrics' / 'usage_events.jsonl'
        else:
            self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.events: List[UsageEvent] = []
        self._load_events()

    def track(self, feature_name: str, action: str, user_id: Optional[str]=None, **metadata: Any) -> UsageEvent:
        event = UsageEvent(feature_name=feature_name, action=action, user_id=user_id, metadata=metadata)
        self.events.append(event)
        self._persist_event(event)
        logger.info('Usage tracked: %s:%s', feature_name, action, extra={'feature': feature_name, 'action': action, 'user_id': user_id})
        return event

    def get_events(self) -> List[UsageEvent]:
        return self.events

    def export(self, output_path: Union[str, Path], export_format: str='json') -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.events:
            logger.warning('No events to export')
            if export_format == 'json':
                output_path.write_text('[]')
            elif export_format == 'csv':
                pd.DataFrame().to_csv(output_path, index=False)
            return output_path
        data = [event.to_dict() for event in self.events]
        df = pd.DataFrame(data)
        if export_format in ['csv', 'parquet']:
            df['metadata'] = df['metadata'].apply(json.dumps)
        if export_format == 'json':
            output_path.write_text(json.dumps(data, indent=2))
        elif export_format == 'csv':
            df.to_csv(output_path, index=False)
        elif export_format == 'parquet':
            df.to_parquet(output_path, index=False)
        else:
            raise ValueError(f'Unsupported export format: {export_format}')
        logger.info('Exported %s events to %s (%s)', len(self.events), output_path, export_format)
        return output_path

    def _persist_event(self, event: UsageEvent) -> None:
        try:
            with open(self.storage_path, 'a') as f:
                f.write(event.model_dump_json() + '\n')
        except Exception as e:
            logger.error('Failed to persist usage event: %s', e)

    def _load_events(self) -> None:
        if not self.storage_path.exists():
            return
        try:
            with open(self.storage_path, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            self.events.append(UsageEvent.model_validate_json(line))
                        except Exception as e:
                            logger.warning('Failed to parse usage event line: %s', e)
        except Exception as e:
            logger.error('Failed to load usage events: %s', e)
