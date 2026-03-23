import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from uuid import UUID
if __package__ in (None, ''):
    repo_root = Path(__file__).resolve().parents[5]
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)
from backend.python.multi_agent.guardrails import Guardrails
from backend.python.apps.analytics.api.monitoring_models import CommandCreate, CommandResponse, CommandStatus, CommandUpdate, EventSeverity, OperationalEventCreate, OperationalEventResponse
from backend.python.config import settings
from backend.python.logging_config import get_logger
from backend.python.supabase_pool import get_pool
logger = get_logger(__name__)

def _safe_log_value(value: object, max_length: int=200) -> str:
    return Guardrails.sanitize_for_logging(value, max_length=max_length)

class MonitoringService:

    def __init__(self, actor: str='api_user'):
        self.actor = actor

    async def emit_event(self, event: OperationalEventCreate) -> OperationalEventResponse:
        pool = await get_pool(settings.database_url)
        row = await pool.fetchrow('\n            INSERT INTO monitoring.operational_events\n                (event_type, severity, source, correlation_id, payload)\n            VALUES ($1, $2, $3, $4, $5)\n            RETURNING id, event_type, severity, source, correlation_id,\n                      payload, created_at, acknowledged_at\n            ', event.event_type, event.severity.value, event.source, event.correlation_id, json.dumps(event.payload))
        logger.info('Operational event emitted: type=%s severity=%s source=%s', _safe_log_value(event.event_type), _safe_log_value(event.severity.value), _safe_log_value(event.source))
        return self._row_to_event(row)

    async def list_events(self, severity: Optional[EventSeverity]=None, source: Optional[str]=None, limit: int=50, offset: int=0) -> List[OperationalEventResponse]:
        pool = await get_pool(settings.database_url)
        conditions = []
        params: list = []
        idx = 1
        if severity is not None:
            conditions.append(f'severity = ${idx}')
            params.append(severity.value)
            idx += 1
        if source is not None:
            conditions.append(f'source = ${idx}')
            params.append(source)
            idx += 1
        where = 'WHERE ' + ' AND '.join(conditions) if conditions else ''
        params.extend([limit, offset])
        query = f'\n            SELECT id, event_type, severity, source, correlation_id,\n                   payload, created_at, acknowledged_at\n            FROM monitoring.operational_events\n            {where}\n            ORDER BY created_at DESC\n            LIMIT ${idx} OFFSET ${idx + 1}\n        '
        rows = await pool.fetch(query, *params)
        return [self._row_to_event(r) for r in rows]

    async def acknowledge_event(self, event_id: UUID) -> Optional[OperationalEventResponse]:
        pool = await get_pool(settings.database_url)
        row = await pool.fetchrow('\n            UPDATE monitoring.operational_events\n            SET acknowledged_at = $1\n            WHERE id = $2\n            RETURNING id, event_type, severity, source, correlation_id,\n                      payload, created_at, acknowledged_at\n            ', datetime.now(timezone.utc), event_id)
        if row is None:
            return None
        logger.info('Event acknowledged: %s', _safe_log_value(event_id))
        return self._row_to_event(row)

    async def create_command(self, cmd: CommandCreate) -> CommandResponse:
        pool = await get_pool(settings.database_url)
        row = await pool.fetchrow('\n            INSERT INTO monitoring.commands\n                (command_type, requested_by, event_id, parameters)\n            VALUES ($1, $2, $3, $4)\n            RETURNING id, command_type, status, requested_by, event_id,\n                      parameters, result, created_at, started_at, completed_at\n            ', cmd.command_type, cmd.requested_by, cmd.event_id, json.dumps(cmd.parameters))
        logger.info('Command created: type=%s by=%s', _safe_log_value(cmd.command_type), _safe_log_value(cmd.requested_by))
        return self._row_to_command(row)

    async def list_commands(self, status: Optional[CommandStatus]=None, limit: int=50) -> List[CommandResponse]:
        pool = await get_pool(settings.database_url)
        params: list = []
        idx = 1
        where = ''
        if status is not None:
            where = f'WHERE status = ${idx}'
            params.append(status.value)
            idx += 1
        params.append(limit)
        query = f'\n            SELECT id, command_type, status, requested_by, event_id,\n                   parameters, result, created_at, started_at, completed_at\n            FROM monitoring.commands\n            {where}\n            ORDER BY created_at DESC\n            LIMIT ${idx}\n        '
        rows = await pool.fetch(query, *params)
        return [self._row_to_command(r) for r in rows]

    async def update_command_status(self, cmd_id: UUID, update: CommandUpdate) -> Optional[CommandResponse]:
        pool = await get_pool(settings.database_url)
        now = datetime.now(timezone.utc)
        result_json = json.dumps(update.result) if update.result is not None else None
        if update.status == CommandStatus.running:
            row = await pool.fetchrow('\n                UPDATE monitoring.commands\n                SET status = $1, result = $2, started_at = $3\n                WHERE id = $4\n                RETURNING id, command_type, status, requested_by, event_id,\n                          parameters, result, created_at, started_at, completed_at\n                ', update.status.value, result_json, now, cmd_id)
        elif update.status in (CommandStatus.completed, CommandStatus.failed):
            row = await pool.fetchrow('\n                UPDATE monitoring.commands\n                SET status = $1, result = $2, completed_at = $3\n                WHERE id = $4\n                RETURNING id, command_type, status, requested_by, event_id,\n                          parameters, result, created_at, started_at, completed_at\n                ', update.status.value, result_json, now, cmd_id)
        else:
            row = await pool.fetchrow('\n                UPDATE monitoring.commands\n                SET status = $1, result = $2\n                WHERE id = $3\n                RETURNING id, command_type, status, requested_by, event_id,\n                          parameters, result, created_at, started_at, completed_at\n                ', update.status.value, result_json, cmd_id)
        if row is None:
            return None
        logger.info('Command %s updated to status=%s', _safe_log_value(cmd_id), _safe_log_value(update.status.value))
        return self._row_to_command(row)

    @staticmethod
    def _parse_json(value) -> dict:
        if value is None:
            return {}
        return json.loads(value) if isinstance(value, str) else value

    @staticmethod
    def _parse_json_nullable(value):
        if value is None:
            return None
        return json.loads(value) if isinstance(value, str) else value

    def _row_to_event(self, row) -> OperationalEventResponse:
        return OperationalEventResponse(id=row['id'], event_type=row['event_type'], severity=EventSeverity(row['severity']), source=row['source'], correlation_id=row['correlation_id'], payload=self._parse_json(row['payload']), created_at=row['created_at'], acknowledged_at=row['acknowledged_at'])

    def _row_to_command(self, row) -> CommandResponse:
        return CommandResponse(id=row['id'], command_type=row['command_type'], status=CommandStatus(row['status']), requested_by=row['requested_by'], event_id=row['event_id'], parameters=self._parse_json(row['parameters']), result=self._parse_json_nullable(row['result']), created_at=row['created_at'], started_at=row['started_at'], completed_at=row['completed_at'])
