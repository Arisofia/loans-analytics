from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

import asyncpg


@dataclass(frozen=True)
class KPIResult:
    kpi_key: str
    value_num: Optional[Decimal]
    unit: str
    status: str  # healthy|warning|critical|unknown
    target: Optional[Decimal]
    components: Dict[str, Any]
    as_of: date
    computed_at: datetime
    inputs_hash: str


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _hash_inputs(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, default=str).encode()
    return hashlib.sha256(raw).hexdigest()


def _status_by_thresholds(
    value: Optional[Decimal], green: Decimal, yellow: Decimal, direction: str
) -> str:
    if value is None:
        return "unknown"
    if direction == "higher_is_better":
        if value >= green:
            return "healthy"
        if value >= yellow:
            return "warning"
        return "critical"
    else:
        if value <= green:
            return "healthy"
        if value <= yellow:
            return "warning"
        return "critical"


class KPICalculator:
    def __init__(self, db_uri: str):
        self.db_uri = db_uri
        self.pool: Optional[asyncpg.Pool] = None

    async def __aenter__(self) -> "KPICalculator":
        self.pool = await asyncpg.create_pool(
            self.db_uri, min_size=1, max_size=5, command_timeout=30
        )
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self.pool:
            await self.pool.close()

    async def _fetchval(self, sql: str, *args) -> Any:
        assert self.pool
        async with self.pool.acquire() as conn:
            return await conn.fetchval(sql, *args)

    async def _execute(self, sql: str, *args) -> None:
        assert self.pool
        async with self.pool.acquire() as conn:
            await conn.execute(sql, *args)

    # Example: Portfolio at Risk (90+ days)
    async def par_90(self, snapshot_id: str, as_of: date) -> KPIResult:
        total = await self._fetchval(
            """
            select coalesce(sum(balance),0)
            from cascade.loan_status
            where snapshot_id=$1
            """,
            snapshot_id,
        )
        delinquent = await self._fetchval(
            """
            select coalesce(sum(balance),0)
            from cascade.loan_status
            where snapshot_id=$1 and days_past_due >= 90
            """,
            snapshot_id,
        )
        total_d = Decimal(str(total))
        delinquent_d = Decimal(str(delinquent))
        rate = (delinquent_d / total_d * Decimal("100")) if total_d > 0 else None
        ih = _hash_inputs(
            {
                "total": str(total_d),
                "delinquent": str(delinquent_d),
                "snapshot_id": snapshot_id,
                "as_of": str(as_of),
            }
        )
        status = _status_by_thresholds(
            rate, green=Decimal("3"), yellow=Decimal("5"), direction="lower_is_better"
        )
        return KPIResult(
            kpi_key="risk.par_90",
            value_num=rate,
            unit="percent",
            status=status,
            target=Decimal("3"),
            components={"delinquent_balance": str(delinquent_d), "total_balance": str(total_d)},
            as_of=as_of,
            computed_at=_utcnow(),
            inputs_hash=ih,
        )

    # Add additional KPI calculation methods here following the same pattern
