"""Settings layer for the v2 canonical pipeline scaffold."""

from __future__ import annotations  # noqa: E402

import os  # noqa: E402
from dataclasses import dataclass, field  # noqa: E402


@dataclass(frozen=True)
class Settings:
    supabase_url: str | None = field(default_factory=lambda: os.getenv("SUPABASE_URL"))
    # Canonical (matches config/pipeline.yml): SUPABASE_SERVICE_ROLE
    # Back-compat: SUPABASE_SERVICE_ROLE_KEY
    supabase_service_role_key: str | None = field(
        default_factory=lambda: os.getenv("SUPABASE_SERVICE_ROLE")
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    )
