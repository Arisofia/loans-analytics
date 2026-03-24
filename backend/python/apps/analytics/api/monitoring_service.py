from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

try:
    from .monitoring_models import (
        CommandCreate,
        CommandResponse,
        CommandStatus,
        CommandUpdate,
        EventSeverity,
        OperationalEventCreate,
        OperationalEventResponse,
    )
    from ....config import settings
    from ....logging_config import get_logger
    from ....multi_agent.guardrails import Guardrails
    from ....supabase_pool import get_pool
except ImportError:
    if __package__ not in (None, ""):
        raise

    repo_root = Path(__file__).resolve().parents[5]
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)

    from backend.python.apps.analytics.api.monitoring_models import (
        CommandCreate,
        CommandResponse,
        CommandStatus,
        CommandUpdate,
        EventSeverity,
        OperationalEventCreate,
        OperationalEventResponse,
    )
    from backend.python.config import settings
    from backend.python.logging_config import get_logger
    from backend.python.multi_agent.guardrails import Guardrails
    from backend.python.supabase_pool import get_pool

logger = get_logger(__name__)
MAX_QUERY_LIMIT = 500


def _safe_log_value(value: object, max_length: int = 200) -> str:
    return Guardrails.sanitize_for_logging(value, max_length=max_length)


def _json_default(value: Any) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def _json_dumps(value: Any) -> str:
    return json.dumps(value, default=_json_default)


def _bounded_int(value: int, lower: int, upper: int) -> int:
    return max(lower, min(value, upper))


def _parse_json_object(value: Any, *, default: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return default
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return default
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        logger.warning('Invalid JSON payload encountered in monitoring row')
        return default
    return parsed if isinstance(parsed, dict) else default


class MonitoringService:
    def __init__(self, actor: str = "api_user") -> None:
        self.actor = actor

    async def emit_event(
        self,
        event: OperationalEventCreate,
    ) -> OperationalEventResponse:
        pool = await get_pool(settings.database_url)
        row = await pool.fetchrow(
            """
            INSERT INTO monitoring.operational_events
                (event_type, severity, source, correlation_id, payload)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, event_type, severity, source, correlation_id,
                      payload, created_at, acknowledged_at
            """,
            event.event_type,
            event.severity.value,
            event.source,
            event.correlation_id,
            _json_dumps(event.payload),
        )
        if row is None:
            raise RuntimeError("Failed to insert operational event")

        logger.info(
            "Operational event emitted: type=%s severity=%s source=%s",
            _safe_log_value(event.event_type),
            _safe_log_value(event.severity.value),
            _safe_log_value(event.source),
        )
        return self._row_to_event(row)

    async def list_events(
        self,
        severity: EventSeverity | None = None,
        source: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[OperationalEventResponse]:
        pool = await get_pool(settings.database_url)

        limit = _bounded_int(limit, 1, MAX_QUERY_LIMIT)
        offset = max(0, offset)

        conditions: list[str] = []
        params: list[Any] = []
        idx = 1

        if severity is not None:
            conditions.append(f"severity = ${idx}")
            params.append(severity.value)
            idx += 1

        if source is not None:
            conditions.append(f"source = ${idx}")
            params.append(source)
            idx += 1

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.extend([limit, offset])

        query = (
            f"SELECT id, event_type, severity, source, correlation_id,"
            f" payload, created_at, acknowledged_at"
            f" FROM monitoring.operational_events"
            f" {where}"  # nosec B608
            f" ORDER BY created_at DESC"
            f" LIMIT ${idx} OFFSET ${idx + 1}"
        )

        rows = await pool.fetch(query, *params)
        return [self._row_to_event(row) for row in rows]

    async def acknowledge_event(
        self,
        event_id: UUID,
    ) -> OperationalEventResponse | None:
        pool = await get_pool(settings.database_url)
        row = await pool.fetchrow(
            """
            UPDATE monitoring.operational_events
            SET acknowledged_at = $1
            WHERE id = $2
            RETURNING id, event_type, severity, source, correlation_id,
                      payload, created_at, acknowledged_at
            """,
            datetime.now(timezone.utc),
            event_id,
        )
        if row is None:
            return None

        logger.info("Event acknowledged: %s", _safe_log_value(event_id))
        return self._row_to_event(row)

    async def create_command(
        self,
        cmd: CommandCreate,
    ) -> CommandResponse:
        pool = await get_pool(settings.database_url)
        row = await pool.fetchrow(
            """
            INSERT INTO monitoring.commands
                (command_type, requested_by, event_id, parameters)
            VALUES ($1, $2, $3, $4)
            RETURNING id, command_type, status, requested_by, event_id,
                      parameters, result, created_at, started_at, completed_at
            """,
            cmd.command_type,
            cmd.requested_by,
            cmd.event_id,
            _json_dumps(cmd.parameters),
        )
        if row is None:
            raise RuntimeError("Failed to create command")

        logger.info(
            "Command created: type=%s by=%s",
            _safe_log_value(cmd.command_type),
            _safe_log_value(cmd.requested_by),
        )
        return self._row_to_command(row)

    async def list_commands(
        self,
        status: CommandStatus | None = None,
        limit: int = 50,
    ) -> list[CommandResponse]:
        pool = await get_pool(settings.database_url)

        limit = _bounded_int(limit, 1, MAX_QUERY_LIMIT)

        params: list[Any] = []
        idx = 1
        where = ""

        if status is not None:
            where = f"WHERE status = ${idx}"
            params.append(status.value)
            idx += 1

        params.append(limit)

        query = (
            f"SELECT id, command_type, status, requested_by, event_id,"
            f" parameters, result, created_at, started_at, completed_at"
            f" FROM monitoring.commands"
            f" {where}"  # nosec B608
            f" ORDER BY created_at DESC"
            f" LIMIT ${idx}"
        )

        rows = await pool.fetch(query, *params)
        return [self._row_to_command(row) for row in rows]

    async def update_command_status(
        self,
        cmd_id: UUID,
        update: CommandUpdate,
    ) -> CommandResponse | None:
        pool = await get_pool(settings.database_url)
        now = datetime.now(timezone.utc)
        result_json = _json_dumps(update.result) if update.result is not None else None

        if update.status == CommandStatus.running:
            row = await pool.fetchrow(
                """
                UPDATE monitoring.commands
                SET status = $1,
                    result = $2,
                    started_at = COALESCE(started_at, $3),
                    completed_at = NULL
                WHERE id = $4
                RETURNING id, command_type, status, requested_by, event_id,
                          parameters, result, created_at, started_at, completed_at
                """,
                update.status.value,
                result_json,
                now,
                cmd_id,
            )
        elif update.status in (CommandStatus.completed, CommandStatus.failed):
            row = await pool.fetchrow(
                """
                UPDATE monitoring.commands
                SET status = $1,
                    result = $2,
                    started_at = COALESCE(started_at, $3),
                    completed_at = $3
                WHERE id = $4
                RETURNING id, command_type, status, requested_by, event_id,
                          parameters, result, created_at, started_at, completed_at
                """,
                update.status.value,
                result_json,
                now,
                cmd_id,
            )
        else:
            row = await pool.fetchrow(
                """
                UPDATE monitoring.commands
                SET status = $1,
                    result = $2
                WHERE id = $3
                RETURNING id, command_type, status, requested_by, event_id,
                          parameters, result, created_at, started_at, completed_at
                """,
                update.status.value,
                result_json,
                cmd_id,
            )

        if row is None:
            return None

        logger.info(
            "Command %s updated to status=%s",
            _safe_log_value(cmd_id),
            _safe_log_value(update.status.value),
        )
        return self._row_to_command(row)

    @staticmethod
    def _parse_json(value: Any) -> dict[str, Any]:
        return _parse_json_object(value, default={}) or {}

    @staticmethod
    def _parse_json_nullable(value: Any) -> dict[str, Any] | None:
        return _parse_json_object(value, default=None)

    def _row_to_event(self, row: Any) -> OperationalEventResponse:
        return OperationalEventResponse(
            id=row["id"],
            event_type=row["event_type"],
            severity=EventSeverity(row["severity"]),
            source=row["source"],
            correlation_id=row["correlation_id"],
            payload=self._parse_json(row["payload"]),
            created_at=row["created_at"],
            acknowledged_at=row["acknowledged_at"],
        )

    def _row_to_command(self, row: Any) -> CommandResponse:
        return CommandResponse(
            id=row["id"],
            command_type=row["command_type"],
            status=CommandStatus(row["status"]),
            requested_by=row["requested_by"],
            event_id=row["event_id"],
            parameters=self._parse_json(row["parameters"]),
            result=self._parse_json_nullable(row["result"]),
            created_at=row["created_at"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
        )
