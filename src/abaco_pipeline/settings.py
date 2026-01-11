"""Settings layer for the v2 canonical pipeline scaffold."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    supabase_url: str | None = field(default_factory=lambda: os.getenv("SUPABASE_URL"))
    # Canonical (matches config/pipeline.yml): SUPABASE_SERVICE_ROLE
    # Back-compat: SUPABASE_SERVICE_ROLE_KEY
    supabase_service_role_key: str | None = field(
        default_factory=lambda: os.getenv("SUPABASE_SERVICE_ROLE")
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    )

    cascade_base_url: str = field(
        default_factory=lambda: os.getenv("CASCADE_BASE_URL", "https://app.cascadedebt.com")
    )
    cascade_token: str | None = field(default_factory=lambda: os.getenv("CASCADE_TOKEN"))
