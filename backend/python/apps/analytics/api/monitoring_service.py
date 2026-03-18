"""Service layer for the self-healing monitoring and command system."""

import json
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

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
from backend.python.supabase_pool import get_pool

logger = get_logger(__name__)


class MonitoringService:
    def __init__(self, actor: str = "api_user"):
        self.actor = actor

    async def emit_event(self, event: OperationalEventCreate) -> OperationalEventResponse:
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
            json.dumps(event.payload),
        )

        logger.info(
            "Operational event emitted: type=%s severity=%s source=%s",
            event.event_type,
            event.severity.value,
            event.source,
        )

        return self._row_to_event(row)

    async def list_events(
        self,
        severity: Optional[EventSeverity] = None,
        source: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[OperationalEventResponse]:
        pool = await get_pool(settings.database_url)

        conditions = []
        params: list = []
        idx = 1

        if severity is not None:
            conditions.append(f"severity = ${idx}")
            params.append(severity.value)
            idx += 1

        if source is not None:
            conditions.append(f"source = ${idx}")
            params.append(source)
            idx += 1

        where = ""
        if conditions:
            where = "WHERE " + " AND ".join(conditions)

        params.extend([limit, offset])
        query = f"""
            SELECT id, event_type, severity, source, correlation_id,
                   payload, created_at, acknowledged_at
            FROM monitoring.operational_events
            {where}
            ORDER BY created_at DESC
            LIMIT ${idx} OFFSET ${idx + 1}
        """  # nosec B608 -- parameterized via asyncpg $N placeholders

        rows = await pool.fetch(query, *params)
        return [self._row_to_event(r) for r in rows]

    async def acknowledge_event(self, event_id: UUID) -> Optional[OperationalEventResponse]:
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

        logger.info("Event acknowledged: %s", event_id)
        return self._row_to_event(row)

    async def create_command(self, cmd: CommandCreate) -> CommandResponse:
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
            json.dumps(cmd.parameters),
        )

        logger.info(
            "Command created: type=%s by=%s",
            cmd.command_type,
            cmd.requested_by,
        )

        return self._row_to_command(row)

    async def list_commands(
        self,
        status: Optional[CommandStatus] = None,
        limit: int = 50,
    ) -> List[CommandResponse]:
        pool = await get_pool(settings.database_url)

        params: list = []
        idx = 1
        where = ""

        if status is not None:
            where = f"WHERE status = ${idx}"
            params.append(status.value)
            idx += 1

        params.append(limit)
        query = f"""
            SELECT id, command_type, status, requested_by, event_id,
                   parameters, result, created_at, started_at, completed_at
            FROM monitoring.commands
            {where}
            ORDER BY created_at DESC
            LIMIT ${idx}
        """  # nosec B608 -- parameterized via asyncpg $N placeholders

        rows = await pool.fetch(query, *params)
        return [self._row_to_command(r) for r in rows]

    async def update_command_status(
        self, cmd_id: UUID, update: CommandUpdate
    ) -> Optional[CommandResponse]:
        pool = await get_pool(settings.database_url)

        now = datetime.now(timezone.utc)
        result_json = json.dumps(update.result) if update.result is not None else None

        # Build the update dynamically based on status transition
        if update.status == CommandStatus.running:
            row = await pool.fetchrow(
                """
                UPDATE monitoring.commands
                SET status = $1, result = $2, started_at = $3
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
                SET status = $1, result = $2, completed_at = $3
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
                SET status = $1, result = $2
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

        logger.info("Command %s updated to status=%s", cmd_id, update.status.value)
        return self._row_to_command(row)

    # ------------------------------------------------------------------
    # Row mappers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_json(value) -> dict:
        """Parse a jsonb value that may be str or dict from asyncpg."""
        if value is None:
            return {}
        if isinstance(value, str):
            return json.loads(value)
        return value

    @staticmethod
    def _parse_json_nullable(value):
        """Parse a nullable jsonb value from asyncpg."""
        if value is None:
            return None
        if isinstance(value, str):
            return json.loads(value)
        return value

    def _row_to_event(self, row) -> OperationalEventResponse:
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

    def _row_to_command(self, row) -> CommandResponse:
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
